"""Official Codex app-server integration: managed ChatGPT login and persistent art conversations."""
from pathlib import Path
import base64, copy, html, json, os, shutil, sys, time, uuid
from PySide6.QtCore import QObject, Signal, QProcess, QProcessEnvironment, QUrl, QTimer
from PySide6.QtGui import QDesktopServices, QTextDocument, QGuiApplication
from PIL import Image
from .settings import atomic_json

def message_html(role,text):
    label='You' if role=='user' else 'ChatGPT'
    if role=='user': body=html.escape(text).replace('\n','<br>')
    else:
        document=QTextDocument(); document.setDefaultFont(QGuiApplication.font()); document.setMarkdown(text)
        markup=document.toHtml(); body=markup.split('<body',1)[1].split('>',1)[1].rsplit('</body>',1)[0]
    return '<b>'+label+'</b><br>'+body

def editor_mcp_config(settings):
    if getattr(sys,'frozen',False): command=str(Path(sys.executable).with_name('Compositor-Tools.exe')); args=['--mcp']
    else: command=sys.executable; args=[str(Path(__file__).resolve().parents[1]/'run.py'),'--mcp']
    return {'command':command,'args':args,'env':{'COMPOSITOR_DATA':str(settings.root),'PYTHONUTF8':'1'}}

def runtime_command(configured=None):
    path=configured or shutil.which('codex.exe') or shutil.which('codex.cmd') or shutil.which('codex')
    if not path: raise RuntimeError('ChatGPT support needs to be installed')
    path=Path(path)
    if path.suffix.lower() in ('.cmd','.ps1'):
        script=path.parent/'node_modules/@openai/codex/bin/codex.js'
        node=shutil.which('node')
        if script.exists() and node: return node,[str(script)]
        raise RuntimeError('ChatGPT support needs to be repaired')
    if not path.is_file(): raise RuntimeError('ChatGPT support needs to be repaired')
    return str(path),[]

class ChatSession(QObject):
    display=Signal(str)
    stream=Signal(str)
    status=Signal(str)
    ready=Signal()
    models_changed=Signal()
    account_changed=Signal()
    question=Signal(dict)
    questions_cleared=Signal()
    message_sent=Signal(str)
    def __init__(self,workspace,parent=None):
        super().__init__(parent); self.ws=workspace; self.owner=parent; self.pending={}; self.sequence=0; self.buffer=b''; self.initialized=False; self.busy=False; self.thread=None; self.turn=None; self.account=None; self.model=None; self.model_options=[]; self.after_ready=[]; self.message_fragments={}; self.active_document=None; self.source_revision=None
        self.root=workspace.settings.root/'chat'; self.root.mkdir(exist_ok=True); self.home=self.root/'codex'; self.home.mkdir(exist_ok=True)
        self.model=workspace.settings.values.get('chat_model','gpt-6-sol')
        self.work=Path(workspace.settings.values.get('chat_working_directory') or self.root/'artifacts').resolve(); self.work.mkdir(parents=True,exist_ok=True); self.metadata_path=self.root/'conversation.json'
        self.metadata=json.loads(self.metadata_path.read_text(encoding='utf-8')) if self.metadata_path.exists() else {}
        self.transcript_path=self.root/'conversation.jsonl'; self.account_checked=False
        self.proc=QProcess(self); self.proc.setProcessChannelMode(QProcess.ProcessChannelMode.SeparateChannels); self.proc.readyReadStandardOutput.connect(self.read_output); self.proc.readyReadStandardError.connect(self.read_error); self.proc.errorOccurred.connect(lambda _:self.status.emit('ChatGPT runtime could not start')); self.proc.finished.connect(self.finished)
        self.configure_mcp()
        env=QProcessEnvironment.systemEnvironment()
        # The application owns its own sign-in and chat history. It never borrows another application's account.
        for key in env.keys():
            if key.startswith(('CODEX_','BUDDY_HOST_')) or key in ('OPENAI_API_KEY','OPENAI_BASE_URL'): env.remove(key)
        env.insert('CODEX_HOME',str(self.home)); env.insert('COMPOSITOR_DATA',str(workspace.settings.root)); env.insert('PYTHONUTF8','1'); self.proc.setProcessEnvironment(env); self.proc.setWorkingDirectory(str(self.work))
        self.proc.started.connect(self.initialize)
        program,args=runtime_command(workspace.settings.values.get('codex_path')); self.proc.start(program,args+['app-server','--stdio'])
        self.watchdog=QTimer(self); self.watchdog.setInterval(5000); self.watchdog.timeout.connect(self.expire_requests); self.watchdog.start()
        self.last_stderr=''; self.native_sources={}; self.turn_started_at=0
        self.requested_generation=None; self.generation_waiting=False
        self.waiting_message=None; self.login_pending=False; self.stop_requested=False
        self.request_started_at=None; self.last_activity=time.monotonic()
        self.stream_timer=QTimer(self); self.stream_timer.setInterval(100); self.stream_timer.timeout.connect(self.flush_stream); self.stream_timer.start(); self.stream_dirty=False

    def configure_mcp(self):
        connection=editor_mcp_config(self.ws.settings); command=connection['command']; args=connection['args']
        # JSON string escaping is compatible with TOML basic strings here; no shell is involved.
        config='[features]\nimage_generation = true\n\n[mcp_servers.compositor]\ncommand = '+json.dumps(command)+'\nargs = '+json.dumps(args)+'\nrequired = true\n\n[mcp_servers.compositor.env]\nCOMPOSITOR_DATA = '+json.dumps(str(self.ws.settings.root))+'\n'
        config=config.replace('required = true\n','required = true\ndefault_tools_approval_mode = "approve"\n')
        if os.name=='nt': config+='\n[windows]\nsandbox = "unelevated"\n'
        (self.home/'config.toml').write_text(config,encoding='utf-8')

    def rpc(self,method,params=None,callback=None):
        self.sequence+=1; request_id=self.sequence; self.pending[request_id]=(method,callback,time.monotonic())
        self.write({'id':request_id,'method':method,'params':params or {}}); return request_id
    def write(self,body): self.proc.write((json.dumps(body,ensure_ascii=False)+'\n').encode())
    def initialize(self): self.rpc('initialize',{'clientInfo':{'name':'compositor_windows','title':'Compositor','version':'0.1.0'},'capabilities':{'experimentalApi':True}},self.initialized_response)
    def initialized_response(self,result):
        self.write({'method':'initialized','params':{}}); self.initialized=True
        if os.name=='nt':
            self.status.emit('Preparing ChatGPT tools…'); self.rpc('windowsSandbox/setupStart',{'mode':'unelevated'})
        else: self.discover_account()
    def discover_account(self):
        self.rpc('account/read',{'refreshToken':False},self.account_response); self.rpc('model/list',{},self.models_response)
    def models_response(self,result):
        self.model_options=result.get('data',[])
        self.model=self.ws.settings.values.get('chat_model','gpt-6-sol')
        self.models_changed.emit()
    def account_response(self,result):
        self.account_checked=True; self.account=result.get('account'); self.status.emit(('Signed in · '+str(self.account.get('planType','ChatGPT'))) if self.account else 'Sign in to use ChatGPT')
        self.account_changed.emit()
        self.ready.emit()
        waiting,self.after_ready=self.after_ready,[]
        for fn in waiting: fn()
        if getattr(self,'waiting_message',None): self.flush_message()
    def login(self):
        if not self.initialized or not self.account_checked: self.after_ready.append(self.login); return
        if self.account: self.status.emit('Already signed in'); return
        if self.login_pending: return
        self.login_pending=True
        self.rpc('account/login/start',{'type':'chatgpt','useHostedLoginSuccessPage':True},self.login_started)
    def login_started(self,result):
        url=result.get('authUrl')
        if url: QDesktopServices.openUrl(QUrl(url)); self.status.emit('Finish signing in in your browser')
        elif result.get('verificationUrl'): self.display.emit(html.escape(result['verificationUrl']+' · '+result.get('userCode','')))
    def logout(self):
        self.interrupt(); self.rpc('account/logout',{},lambda _:self.account_response({'account':None}))

    def send_generation(self,prepared):
        status=self.send_message(prepared['userPrompt'],generation=prepared)
        return {'route':'chatgpt','status':status,'documentId':prepared['documentId']}

    def send_message(self,text,generation=None,context=None):
        if self.busy or self.waiting_message: raise ValueError('Wait for the current ChatGPT request or stop it before sending another message')
        self.waiting_message={'text':text,'generation':copy.deepcopy(generation),'documentId':generation['documentId'] if generation else self.ws.active,
            'sourceRevision':generation['sourceRevision'] if generation else self.ws.document().revision if self.ws.active else None,
            'sourceStateId':generation.get('sourceStateId') if generation else self.ws.document().state_id if self.ws.active else None}
        if context: self.waiting_message.update({k:context.get(k) for k in ('documentId','sourceRevision','sourceStateId')})
        self.request_started_at=time.monotonic()
        self.generation_waiting=bool(generation)
        return self.flush_message()
    def flush_message(self):
        if not self.waiting_message: return
        if not self.initialized or not self.account_checked:
            self.status.emit('Connecting to ChatGPT…'); return 'connecting'
        if not self.account:
            self.login(); return 'awaiting_signin'
        request=self.waiting_message; self.waiting_message=None; self.generation_waiting=False
        self.busy=True; self.stop_requested=False; self.status.emit('Starting…'); self.requested_generation=request['generation']
        self.active_document=request['documentId']; self.source_revision=request['sourceRevision']; self.source_state_id=request['sourceStateId']; text=request['text']
        self.record('user',text); self.message_sent.emit(text)
        if self.thread: self.start_turn(text); return 'requested'
        params={'cwd':str(self.work),'approvalPolicy':'on-request','sandbox':'workspace-write','developerInstructions':(Path(__file__).parent/'prompts/editor.md').read_text(encoding='utf-8')}
        if self.model: params['model']=self.model
        saved=self.metadata.get('threadId')
        if saved: params['threadId']=saved; params['excludeTurns']=True
        self.rpc('thread/resume' if saved else 'thread/start',params,lambda r:self.thread_started(r,text))
        return 'requested'
    def thread_started(self,result,text):
        self.thread=result['thread']['id']; self.metadata['threadId']=self.thread; atomic_json(self.metadata_path,self.metadata); self.start_turn(text)
    def start_turn(self,text):
        context={'activeDocument':self.active_document}
        if self.active_document: context['document']=self.ws.document(self.active_document).info()
        if self.requested_generation: context['preparedGeneration']=self.requested_generation
        params={'threadId':self.thread,'input':[{'type':'text','text':text+'\n\nCurrent editor context:\n'+json.dumps(context,ensure_ascii=False)}]}
        if self.model: params['model']=self.model
        self.rpc('turn/start',params,self.turn_started)
    def turn_started(self,result):
        self.turn=result['turn']['id']; self.turn_started_at=time.time()
        if self.stop_requested: self.interrupt()
        else: self.status.emit('Working…')
    def interrupt(self):
        self.waiting_message=None; self.generation_waiting=False; self.stop_requested=True
        if not self.busy: self.status.emit('Stopped')
        if self.thread and self.turn: self.rpc('turn/interrupt',{'threadId':self.thread,'turnId':self.turn}); self.status.emit('Stopping…')

    def read_output(self):
        self.buffer+=bytes(self.proc.readAllStandardOutput())
        while b'\n' in self.buffer:
            line,self.buffer=self.buffer.split(b'\n',1)
            try: message=json.loads(line)
            except ValueError: continue
            self.last_activity=time.monotonic()
            if 'id' in message and 'method' not in message:
                entry=self.pending.pop(message['id'],None)
                if 'error' in message:
                    self.status.emit(message['error'].get('message','ChatGPT request failed')); self.busy=False
                elif entry and entry[1]:
                    try: entry[1](message.get('result',{}))
                    except Exception as e: self.status.emit(str(e)); self.busy=False
            elif 'id' in message: self.server_request(message)
            else: self.notification(message.get('method',''),message.get('params',{}))
    def read_error(self): self.last_stderr=bytes(self.proc.readAllStandardError()).decode(errors='replace')[-1800:]

    def notification(self,method,p):
        if method=='windowsSandbox/setupCompleted':
            if p.get('success'): self.discover_account()
            else: self.status.emit('ChatGPT tools could not be prepared: '+str(p.get('error') or 'Unknown setup error'))
        elif method=='account/login/completed':
            self.login_pending=False
            if p.get('success'): self.rpc('account/read',{'refreshToken':False},self.account_response)
            else: self.status.emit(p.get('error') or 'Sign-in cancelled')
        elif method=='account/updated': self.rpc('account/read',{'refreshToken':False},self.account_response)
        elif method=='item/agentMessage/delta':
            item=p.get('itemId','reply'); self.message_fragments[item]=self.message_fragments.get(item,'')+p.get('delta','')
            # Debounced replacement of one pending reply rather than one widget per token.
            self.status.emit('Replying…')
            self.stream_dirty=True
        elif method=='item/started':
            item=p.get('item',{})
            if item.get('type')=='imageGeneration':
                requested=getattr(self,'requested_generation',None); source=requested or self.ws.prepared_generation
                if source and (requested or source['created']>=self.turn_started_at): self.native_sources[item['id']]=copy.deepcopy(source)
                self.status.emit('Generating an image with your subscription…')
            elif item.get('type') in ('mcpToolCall','dynamicToolCall'): self.status.emit('Editing · '+item.get('tool','Compositor'))
        elif method=='item/completed':
            item=p.get('item',{}); kind=item.get('type')
            if kind=='agentMessage':
                text=item.get('text') or self.message_fragments.pop(item.get('id'), '')
                self.message_fragments.pop(item.get('id'),None); self.stream.emit('')
                self.display.emit(message_html('assistant',text)); self.record('assistant',text)
            elif kind=='imageGeneration': self.native_image(item)
        elif method=='turn/completed':
            self.questions_cleared.emit()
            self.busy=False; self.turn=None; self.requested_generation=None; turn=p.get('turn',{}); error=turn.get('error'); self.status.emit(error.get('message') if error else ('Stopped' if turn.get('status')=='interrupted' else 'Ready'))
        elif method=='error':
            error=p.get('message') or p.get('error','ChatGPT error')
            self.status.emit(str(error.get('message','ChatGPT request failed') if isinstance(error,dict) else error))

    def native_image(self,item):
        if item.get('failure'):
            self.display.emit('Image generation: '+html.escape(str(item['failure']))); return
        job_id=str(uuid.uuid4()); folder=self.ws.generation.root/job_id; folder.mkdir()
        try:
            if item.get('savedPath') and Path(item['savedPath']).is_file(): raw=Path(item['savedPath']).read_bytes()
            else:
                result=item.get('result','')
                if result.startswith('data:'): result=result.split(',',1)[1]
                if not result: raise ValueError('The subscription runtime returned no image path or bytes')
                raw=base64.b64decode(result,validate=True)
            import io
            (folder/'provider-original').write_bytes(raw)
            source=self.native_sources.pop(item.get('id'),{})
            from .generation_source import normalize_candidate
            with Image.open(io.BytesIO(raw)) as im:
                actual=list(im.size); candidate=normalize_candidate(im,source); candidate.save(folder/'result.png')
            job={'id':job_id,'status':'complete','created':time.time(),'finished':time.time(),'documentId':source.get('documentId',self.active_document),'sourceRevision':source.get('sourceRevision',self.source_revision),'kind':'subscription','box':source.get('box'),'prompt':item.get('revisedPrompt') or 'ChatGPT image','config':{'provider':'chatgpt-subscription','model':self.model or 'account default'},'result':str(folder/'result.png'),'actualSize':actual,'nativeItemId':item.get('id'),'autoApply':False}
            job['creativeContext']=source.get('creativeContext',{}); job['userPrompt']=source.get('userPrompt',job['prompt']); job['requestedPrompt']=source.get('prompt'); job['references']=[]
            job['candidateSize']=list(candidate.size)
            job['sourceStateId']=source.get('sourceStateId') if source else getattr(self,'source_state_id',None)
            job.update({key:source[key] for key in ('workingSize','workingContentBox','selectionBox','editArea','resampling') if key in source})
            if source.get('sourcePath'):
                shutil.copyfile(source['sourcePath'],folder/'source.png'); job['inputs']=[str(folder/'source.png')]
                mask=Path(source['sourcePath']).with_name('selection.png')
                if mask.exists(): shutil.copyfile(mask,folder/'selection.png')
            for i,ref in enumerate(source.get('references',[])):
                target=folder/f'reference-{i}.png'; shutil.copyfile(ref['path'],target); job.setdefault('inputs',[]).append(str(target)); job['references'].append({**ref,'path':str(target)})
            atomic_json(folder/'job.json',job); self.ws.generation.receive(job); self.ws.changed.emit(); self.display.emit('Image ready in Generate. Inspect it, then apply or place it as a layer.')
        except Exception as e: self.display.emit('Could not import the generated candidate: '+html.escape(str(e)))

    def server_request(self,message):
        # Questions belong in the panel. A background reply must never open a modal
        # window or capture the user's keyboard focus in another application.
        self.question.emit(message); self.status.emit('Your answer is needed in ChatGPT')

    def answer_request(self,message,result):
        self.write({'id':message['id'],'result':result})

    def record(self,role,text):
        with self.transcript_path.open('a',encoding='utf-8') as file: file.write(json.dumps({'role':role,'text':text,'time':time.time()},ensure_ascii=False)+'\n')
    def flush_stream(self):
        if self.stream_dirty:
            self.stream_dirty=False; self.stream.emit('\n'.join(self.message_fragments.values()))
    def expire_requests(self):
        for key,(method,callback,started) in list(self.pending.items()):
            if time.monotonic()-started>120:
                del self.pending[key]; self.status.emit(method+' did not respond. Reconnect to ChatGPT.'); self.busy=False
    def finished(self,*_):
        self.initialized=False; self.busy=False; self.status.emit('ChatGPT disconnected'); self.pending.clear()
    def shutdown(self):
        self.watchdog.stop(); self.stream_timer.stop(); self.proc.closeWriteChannel()
        if not self.proc.waitForFinished(1500): self.proc.terminate()
