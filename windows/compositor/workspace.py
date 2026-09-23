"""The single owner of open documents for the native UI and external operators."""
from pathlib import Path
import base64, io, json, os, time, uuid
from PySide6.QtCore import QObject, Signal, QTimer
from PIL import Image
from .document import Document
from .generation import Generation
from .generation_source import prepare_source, region_instruction, provider_sizes
from .connectors import StudioConnector
from .settings import atomic_json
from .projects import Projects
from .creative import CreativeLibrary,compose

class Workspace(QObject):
    changed=Signal()
    job_finished=Signal(dict)
    request_received=Signal(object)
    message=Signal(str)
    def __init__(self,settings,restore=True):
        super().__init__(); self.settings=settings; self.documents={}; self.active=None; self.view={'tool':'move','zoom':1}; self.window=None; self.prepared_generation=None; self.recovered_revisions={}
        self.job_finished.connect(self.finish_job); self.request_received.connect(self.handle_request)
        self.generation=Generation(settings,self.job_finished.emit)
        self.styles=CreativeLibrary(settings); self.projects=Projects(self)
        self.autosave=QTimer(self); self.autosave.setSingleShot(True); self.autosave.setInterval(2000); self.autosave.timeout.connect(self.save_recovery)
        if restore: self.restore_recovery()

    def document(self,document_id=None):
        d=self.documents.get(document_id or self.active)
        if d is None: raise ValueError('Open or create a document first')
        return d

    def notify(self): self.changed.emit(); self.autosave.start()

    def state(self):
        chat=getattr(self.window,'chat',None)
        return {'service':'compositor','activeDocument':self.active,'documents':[d.info() for d in self.documents.values()],
                'view':self.view,'jobs':list(self.generation.jobs.values()),'settings':self.settings.public(),'production':self.projects.info(),
                'chat':{'connected':bool(chat and chat.initialized),'signedIn':bool(chat and chat.account),'busy':bool(chat and (chat.busy or chat.generation_waiting or chat.waiting_message)),'model':chat.model if chat else None}}

    def dispatch(self,action,args=None):
        a=args or {}
        if action=='glitch':
            if not hasattr(self,'glitch'):
                from .glitch import GlitchTemple
                self.glitch=GlitchTemple(self)
            return self.glitch.dispatch(a)
        if action=='state': return self.state()
        if action=='chat':
            if not self.window: raise ValueError('Open Compositor to use ChatGPT')
            chat=self.window.ensure_chat(); operation=a.get('operation','status')
            if operation=='send':
                text=str(a.get('text','')).strip()
                if not text: raise ValueError('Write a message first')
                chat.send_message(text)
            elif operation=='stop': chat.interrupt()
            elif operation!='status': raise ValueError('Unknown chat operation')
            return {'connected':chat.initialized,'signedIn':bool(chat.account),'accountChecked':chat.account_checked,'busy':bool(chat.busy or chat.generation_waiting or chat.waiting_message),'model':chat.model,'workingDirectory':str(chat.work),'status':self.window.chat_status.text(),'accountLabel':self.window.chat_account.text(),'signInVisible':not self.window.login_button.isHidden(),'signOutVisible':not self.window.logout_button.isHidden()}
        if action=='fonts':
            from .fonts import catalog
            return {'families':catalog()}
        if action=='styles': return {'styles':self.styles.list()}
        if action=='save_style':
            result=self.styles.save(a); self.notify(); return result
        if action=='production':
            operation=a['operation']; arguments=a.get('args',{})
            if operation in ('present','close_presentation'):
                if not self.window: raise ValueError('Open the editor window to present a project')
                panel=self.window.production
                if operation=='present':
                    project=self.projects.get(arguments.get('projectId')); self.projects.select(project,self.projects.page(project,arguments.get('pageId')))
                    panel.present(project,arguments.get('twoPanels',False))
                elif hasattr(panel,'presentation'): panel.presentation.close()
                self.changed.emit(); return self.view
            result=self.projects.dispatch(a['operation'],a.get('args',{})); self.notify(); return result
        if action=='show':
            if self.window: self.window.showNormal(); self.window.raise_(); self.window.activateWindow()
            return {'shown':self.window is not None}
        if action=='capture_window':
            if not self.window: raise ValueError('No native window is open')
            path=Path(a['path']).resolve(); path.parent.mkdir(parents=True,exist_ok=True)
            if not self.window.grab().save(str(path)): raise ValueError('Could not save the window capture')
            return {'path':str(path),'bytes':path.stat().st_size}
        if action=='new':
            d=Document(a.get('width',1536),a.get('height',1024),a.get('title','Untitled'))
            if a.get('pixelArt'): d.pixel_art={'palette':[],'sampling':'nearest'}
            d.execute('add_layer',{'name':'Background','color':a.get('background','#ffffff')}); self.documents[d.id]=d; self.active=d.id; self.notify(); return d.info()
        if action=='open':
            if Path(a['path']).suffix.lower()=='.compbook':
                result=self.projects.open_bundle(a['path'],a.get('asCopy',False)); self.notify(); return result
            d=Document.load(a['path'])
            same_file=next((existing for existing in self.documents.values() if existing.path and os.path.normcase(str(Path(existing.path).resolve()))==os.path.normcase(str(Path(a['path']).resolve()))),None)
            if same_file and not a.get('asCopy'):
                d=same_file
            else:
                # Save-as variants may carry the same embedded identity. Their
                # files are independent work and must not select a different tab.
                if d.id in self.documents or a.get('asCopy'): d.id=str(uuid.uuid4())
                if a.get('asCopy'): d.path=None; d.saved_revision=-1
                self.documents[d.id]=d
            self.active=d.id
            self.notify(); return {**d.info(),'conversionReport':getattr(d,'conversion_report',[])}
        if action=='activate':
            self.active=self.document(a['documentId']).id
            linked=self.projects.for_document(self.active)
            if linked: self.projects.active=linked[0]['id']; linked[0]['activePage']=linked[1]['id']
            self.changed.emit(); return self.document().info()
        if action=='view':
            self.view.update(a); self.changed.emit(); return self.view
        if action=='settings':
            allowed={'provider','model','quality','imageSize','aspectRatio','studio_url','openai_url','gemini_url','codex_path','generationRoute','chat_model','chat_working_directory','artwork_directory'}
            if 'provider' in a:
                if a['provider'] not in ('openai','gemini'):raise ValueError('Choose an image provider')
                if 'model' not in a:a={**a,'model':self.settings.model_for(a['provider'])}
            if 'generationRoute' in a and a['generationRoute'] not in ('api','chatgpt'): raise ValueError('Choose API provider or ChatGPT subscription')
            reconnect='chat_working_directory' in a and a['chat_working_directory']!=self.settings.values.get('chat_working_directory','')
            chat=getattr(self.window,'chat',None)
            if reconnect and chat and (chat.busy or chat.waiting_message): raise ValueError('Stop the current ChatGPT request before changing its working folder')
            for k,v in a.items():
                if k not in allowed: raise ValueError(f'Unsupported setting {k}')
            if reconnect and a['chat_working_directory']:
                folder=Path(a['chat_working_directory']).expanduser().resolve(); folder.mkdir(parents=True,exist_ok=True)
                if not folder.is_dir(): raise ValueError('Choose a folder for ChatGPT files')
                a={**a,'chat_working_directory':str(folder)}
            if 'artwork_directory' in a:
                folder=a['artwork_directory'].strip()
                if folder:
                    folder=Path(folder).expanduser().resolve()
                    if not folder.is_dir(): raise ValueError('Choose an existing artwork folder')
                    folder=str(folder)
                a={**a,'artwork_directory':folder}
                if folder!=self.settings.values.get('artwork_directory',''):
                    remembered=self.settings.values.get('file_dialog_directories',{})
                    for purpose in ('save','export'): remembered.pop(purpose,None)
            models=self.settings.values.setdefault('provider_models',{})
            models[self.settings.values['provider']]=self.settings.values['model']
            self.settings.values.update(a)
            models[self.settings.values['provider']]=self.settings.values['model']
            self.settings.save(); self.changed.emit()
            if reconnect and chat: self.window.reconnect_chat()
            return self.settings.public()
        if action=='jobs': return list(self.generation.jobs.values())
        if action=='job': return self.generation.jobs[a['jobId']]
        if action=='connector_projects': return self.connector().projects()
        if action=='connector_action': return self.connector().action(a['action'],a.get('args',{}))
        if action=='connector_pull':
            result=self.connector().pull(a['projectId'],a.get('role','background'),a.get('page',1)); d=Document.load(result['path']); d.title=result['title']; d.studio=result['link']
            self.documents[d.id]=d; self.active=d.id; self.notify(); return d.info()
        d=self.document(a.get('documentId'))
        if action=='document': return d.info()
        if action=='pixel_art':
            from .pixel_art import convert, source
            from .document import Layer
            if a.get('expectedRevision') is not None and a['expectedRevision']!=d.revision: raise ValueError('The source changed. Refresh the conversion preview first.')
            image,metadata=convert(source(d,a),a)
            if a.get('operation','convert')=='preview':
                data=io.BytesIO(); image.save(data,'PNG')
                return {'width':image.width,'height':image.height,'mimeType':'image/png','data':base64.b64encode(data.getvalue()).decode(),**metadata}
            converted=Document(*image.size,title=a.get('title') or d.title+' — pixel art'); converted.pixel_art=metadata
            converted.add(Layer(name='Pixel artwork',image=image,resampling='nearest',provenance={'sourceDocument':d.id,'sourceRevision':d.revision,'conversion':metadata['conversion']}))
            self.documents[converted.id]=converted; self.active=converted.id; self.notify(); return converted.info()
        if action=='edit':
            result=d.execute(a['operation'],a.get('args'),a.get('expectedRevision')); self.notify(); return result
        if action=='save':
            result=d.save(a.get('path') or d.path); self.notify(); return result
        if action=='export': return d.export(a['path'],a.get('quality',95),a.get('scale',1))
        if action=='close':
            if d.dirty and not a.get('discard'): raise ValueError('Save this document first, or explicitly discard its unsaved changes')
            if self.projects.for_document(d.id): self.projects.flush()
            del self.documents[d.id]; self.active=next(iter(self.documents),None); self.notify(); return self.state()
        if action=='capture':
            im=d.render(); region=a.get('region')
            if region:
                x,y,w,h=[int(region[k]) for k in ('x','y','width','height')]
                if min(x,y)<0 or min(w,h)<1 or x+w>im.width or y+h>im.height: raise ValueError('Inspection region must fit inside the canvas')
                im=im.crop((x,y,x+w,y+h))
            if a.get('maxDimension'):
                im=im.copy(); im.thumbnail((int(a['maxDimension']),)*2,Image.Resampling.NEAREST if d.pixel_art else Image.Resampling.LANCZOS)
            if d.pixel_art:
                data=io.BytesIO(); im.save(data,'PNG')
                return {'documentId':d.id,'revision':d.revision,'width':im.width,'height':im.height,'mimeType':'image/png','data':base64.b64encode(data.getvalue()).decode()}
            bg=Image.new('RGBA',im.size,'white'); im=Image.alpha_composite(bg,im).convert('RGB'); data=io.BytesIO(); im.save(data,'JPEG',quality=90,subsampling=0)
            return {'documentId':d.id,'revision':d.revision,'width':im.width,'height':im.height,'mimeType':'image/jpeg','data':base64.b64encode(data.getvalue()).decode()}
        if action in ('prepare_generation','preview_generation'):
            folder=self.settings.root/'prepared'/str(uuid.uuid4()); folder.mkdir(parents=True)
            route=a.get('route') or self.settings.values['generationRoute']
            sizes=provider_sizes({**self.settings.values,**{k:v for k,v in a.items() if k in ('provider','model')}}) if action=='preview_generation' and route=='api' else None
            kind=a.get('kind','edit'); source=prepare_source(d,kind,a.get('box'),folder,a.get('resampling'),a.get('size'),sizes)
            request=self.creative_request(d,{**a,'prompt':a.get('prompt') or 'Edit the supplied image.','kind':kind})
            request['prompt']+='\n\n'+region_instruction(source)
            references=[]
            for i,ref in enumerate(request['references']):
                target=folder/f'reference-{i}.png'
                with Image.open(ref['path']) as image: image.convert('RGBA').save(target)
                references.append({**ref,'path':str(target)})
            source_path=source['sourcePath']
            prepared={**source,'documentId':d.id,'sourceRevision':d.revision,'sourceStateId':d.state_id,'kind':kind,'created':time.time(),'prompt':request['prompt'],'userPrompt':request['userPrompt'],'creativeContext':request['creativeContext'],'references':references,'inputs':([source_path] if source_path else [])+[r['path'] for r in references]}
            prepared['requestedSize']='x'.join(map(str,source['workingSize']))
            if action=='prepare_generation': self.prepared_generation=prepared
            atomic_json(folder/'source.json',prepared); return prepared
        if action=='generate':
            route=a.get('route') or self.settings.values['generationRoute']
            if route=='chatgpt':
                if not self.window: raise ValueError('Open the Compositor editor to generate with ChatGPT')
                return self.window.generate_with_chat(d,a)
            if route!='api': raise ValueError('Choose API provider or ChatGPT subscription')
            result=self.generation.submit(d,self.creative_request(d,a)); self.changed.emit(); return result
        if action=='generation_preview':
            im=self.generation.preview(d,a['jobId'],a.get('paletteMode','document')); data=io.BytesIO(); im.save(data,'PNG')
            return {'documentId':d.id,'revision':d.revision,'width':im.width,'height':im.height,'mimeType':'image/png','data':base64.b64encode(data.getvalue()).decode()}
        if action=='apply_generation':
            result=self.generation.apply(d,a['jobId'],a.get('paletteMode','document')); self.notify(); return result
        if action=='connector_push': return self.connector().push(d,a.get('projectId') or d.studio.get('lessonId'),a.get('role','background'),a.get('page',1))
        raise ValueError(f'Unknown action: {action}')

    def creative_request(self,document,args):
        linked=self.projects.for_document(document.id); context={}
        if linked:
            ids=[args['characterId']] if args.get('purpose')=='character' else None
            context=self.projects.creative_context(*linked,character_ids=ids)
        # A project style is canonical. A standalone document may choose a library profile per request.
        if not linked and args.get('styleId'):
            style=self.styles.get(args['styleId']); context={'style':style,'references':style.get('references',[])}
        explicit=[r if isinstance(r,dict) else {'path':r,'role':'reference','label':Path(r).stem} for r in args.get('references',[])]
        context['references']=[*context.get('references',[]),*explicit]
        result={**args,**compose(args.get('prompt',''),args.get('kind','generate'),**context)}
        if args.get('purpose')=='character': result['creativeContext'].update(purpose='character',characterId=args['characterId'])
        return result

    def connector(self):
        url=self.settings.values.get('studio_url')
        if not url: raise ValueError('Configure an optional Studio connector URL in Settings')
        return StudioConnector(url,self.settings.root/'exchange')

    def finish_job(self,job):
        self.generation.receive(job)
        if job['status']=='running': self.changed.emit(); return
        if job['status']=='complete' and job.get('autoApply'):
            try: self.generation.apply(self.document(job['documentId']),job['id'])
            except Exception as e: job['applyError']=str(e); atomic_json(self.generation.root/job['id']/'job.json',job)
        self.notify(); self.message.emit('Image ready' if job['status']=='complete' else job.get('error','Generation failed'))

    def handle_request(self,request):
        if not request['future'].set_running_or_notify_cancel(): return
        try: request['future'].set_result(self.dispatch(request['action'],request.get('args')))
        except Exception as e: request['future'].set_exception(e)

    def save_recovery(self):
        folder=self.settings.root/'recovery'; folder.mkdir(exist_ok=True); records=[]
        try:
            self.projects.flush()
            for d in self.documents.values():
                file=folder/(d.id+'.compwin')
                if self.recovered_revisions.get(d.id)!=d.revision or not file.exists():
                    d.save(file,mark_saved=False); self.recovered_revisions[d.id]=d.revision
                records.append({'id':d.id,'file':str(file),'path':d.path,'dirty':d.dirty,'activeLayer':d.active})
            atomic_json(folder/'session.json',{'documents':records,'active':self.active,'activeProject':self.projects.active})
        except Exception as e: self.message.emit('Recovery save failed: '+str(e))

    def restore_recovery(self):
        index=self.settings.root/'recovery/session.json'
        if not index.exists(): return
        try:
            state=json.loads(index.read_text(encoding='utf-8'))
            for row in state['documents']:
                d=Document.load(row['file']); d.path=row.get('path'); d.saved_revision=-1 if row['dirty'] else 0
                if row.get('activeLayer') in {l.id for l in d.layers}: d.active=row['activeLayer']
                self.documents[d.id]=d
            self.active=state.get('active')
            self.projects.active=state.get('activeProject')
        except Exception as e: self.message.emit('Recovery could not be fully restored: '+str(e))
