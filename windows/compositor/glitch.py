"""Glitch Temple rendering jobs and revisable treatments owned by the document workspace."""
from pathlib import Path
import base64,copy,io,json,math,time,uuid
from PIL import Image
from PySide6.QtCore import QObject,Signal,Slot,QUrl,QTimer,QProcess
from .document import Layer,Document
from .settings import atomic_json
from . import pixels


def export_dimensions(document,args):
    if args.get('scale') is not None or (document.pixel_art and 'maxDimension' not in args):
        if not document.pixel_art:raise ValueError('Integer enlargement is available for pixel artwork. Use maxDimension for other images.')
        if 'maxDimension' in args:raise ValueError('Choose integer enlargement or a maximum dimension, not both.')
        scale=float(args.get('scale',1))
        if not scale.is_integer() or not 1<=scale<=16:raise ValueError('Choose a whole-number enlargement from 1 to 16.')
        size=[document.width*int(scale),document.height*int(scale)]
        if max(size)>3840:raise ValueError('Choose a smaller enlargement. Animation exports support up to 3840 pixels per side.')
        return size
    maximum=max(32,min(3840,int(args.get('maxDimension',960))))
    ratio=min(1,maximum/max(document.width,document.height))
    return [max(1,round(document.width*ratio)),max(1,round(document.height*ratio))]


class TempleBridge(QObject):
    def __init__(self,owner): super().__init__(owner); self.owner=owner
    @Slot(str)
    def ready(self,text):
        self.owner.catalog=json.loads(text); self.owner.changed.emit(); self.owner.pump()
    @Slot(str)
    def completed(self,text): self.owner.completed(json.loads(text))


class GlitchTemple(QObject):
    changed=Signal()
    def __init__(self,workspace):
        super().__init__(workspace); self.ws=workspace; self.catalog=None; self.page=None
        self.root=workspace.settings.root/'glitch'; self.root.mkdir(exist_ok=True)
        self.jobs={}; self.queue=[]; self.current=None; self.callbacks={}; self.compositions={}; self.encoders={}
        self.assets=Path(__file__).parent/'glitch_assets'
        for path in self.root.glob('*/job.json'):
            try:
                job=json.loads(path.read_text(encoding='utf-8'))
                if job['status'] in ('queued','running','encoding','stopping'):
                    job.update(status='failed',error='Compositor closed during rendering. The saved source and recipe are intact.'); atomic_json(path,job)
                self.jobs[job['id']]=job
            except (ValueError,KeyError): pass

    def start(self):
        if self.page: return
        if not (self.assets/'engine.js').exists(): raise ValueError('The Glitch Temple engine is not included in this build.')
        from PySide6.QtWebEngineCore import QWebEnginePage,QWebEngineSettings
        from PySide6.QtWebChannel import QWebChannel
        self.page=QWebEnginePage(self)
        self.page.settings().setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls,False)
        self.channel=QWebChannel(self.page); self.bridge=TempleBridge(self)
        self.channel.registerObject('bridge',self.bridge); self.page.setWebChannel(self.channel)
        self.page.loadFinished.connect(self.loaded)
        self.page.renderProcessTerminated.connect(lambda *_:self.renderer_failed('Glitch Temple renderer stopped. Retry the saved recipe.'))
        self.page.load(QUrl.fromLocalFile(str(self.assets/'index.html')))

    def loaded(self,success):
        if not success: self.renderer_failed('Could not load the local Glitch Temple renderer.')

    def renderer_failed(self,error):
        self.fail_current(error)
        for request in self.queue:
            job=self.jobs.get(request['id'])
            if job:job.update(status='failed',error=error);self.persist(job)
            self.compositions.pop(request['id'],None)
            callback=self.callbacks.pop(request['id'],None)
            if callback:callback({'error':error})
        self.queue.clear();self.catalog=None
        if self.page:self.page.deleteLater();self.page=None

    def persist(self,job):
        atomic_json(self.root/job['id']/'job.json',job); self.changed.emit()

    def pump(self):
        if self.current or not self.catalog or not self.queue: return
        request=self.queue.pop(0); self.current=request['id']
        job=self.jobs.get(request['id'])
        if job:
            job['status']='running'; self.persist(job)
            if request['operation']=='render':request={**request,'source':self.data_url(self.root/job['id']/'source.png') if job.get('engineSource',job.get('source'))!='generated' else None}
        self.page.runJavaScript('window.templeRequest('+json.dumps(request)+')')

    @staticmethod
    def data_url(path): return 'data:image/png;base64,'+base64.b64encode(Path(path).read_bytes()).decode()

    def fail_current(self,error):
        self.compositions.pop(self.current,None)
        if self.current in self.jobs:
            job=self.jobs[self.current]; job.update(status='failed',error=error); self.persist(job)
        callback=self.callbacks.pop(self.current,None)
        if callback:callback({'error':error})
        self.current=None; self.changed.emit()

    def completed(self,message):
        request_id=message['id']
        if request_id!=self.current: return
        self.current=None
        if request_id in self.callbacks:
            callback=self.callbacks.pop(request_id); callback(message)
        elif request_id in self.jobs:
            job=self.jobs[request_id]
            try:
                if job['status']=='stopping': job.update(status='cancelled')
                elif message.get('error'): job.update(status='failed',error=message['error'])
                elif job.get('kind')=='recipe':job.update(status='complete',recipe=message['result'],finished=time.time())
                else:
                    result=message['result']; raw=base64.b64decode(result['image'].split(',',1)[1])
                    with Image.open(io.BytesIO(raw)) as image: image=image.convert('RGBA')
                    if image.size!=tuple(job['size']): raise ValueError('Renderer returned unexpected dimensions')
                    folder=self.root/job['id']
                    if job.get('preserveAlpha'):
                        with Image.open(folder/'source.png') as source: image.putalpha(source.convert('RGBA').getchannel('A'))
                    job['recipe']=result['recipe']
                    image=self.finish_pixels(image,job['recipe'])
                    if job.get('kind')=='loop': self.accept_frame(job,image)
                    else:
                        path=folder/'result.png'; image.save(path)
                        composition=self.compositions.pop(job['id'])
                        if job['source']=='treatment':
                            original=composition.layer(job['sourceLayerId']);original.image=original.effect_source;composition._cache=None
                        composition.render().save(folder/'before.png')
                        with Image.open(folder/'source.png') as source:self.prepare_layer(composition,job,image,source.convert('RGBA'))
                        composition.render().save(folder/'composition.png')
                        job.update(status='complete',result=str(path),finished=time.time())
                        job.update(compositionResult=str(folder/'composition.png'),originalComposition=str(folder/'before.png'))
                        if job.get('autoApply'):
                            try: self.apply(job['id'])
                            except Exception as error: job['applyError']=str(error)
            except Exception as error: job.update(status='failed',error=str(error))
            if job['status'] in ('failed','cancelled'):self.compositions.pop(job['id'],None)
            self.persist(job)
        self.pump()

    def transform(self,recipe,operation,callback,**args):
        self.start(); request_id=str(uuid.uuid4()); self.callbacks[request_id]=callback
        self.queue.append({'id':request_id,'operation':operation,'recipe':recipe,**args}); self.pump()

    def vary(self,recipe,kind,callback): self.transform(recipe,'vary',callback,kind=kind)

    @staticmethod
    def finish_pixels(image,recipe):
        finish=recipe.get('compositor',{}).get('pixelFinish',{})
        if finish.get('paletteMode')=='document' and finish.get('palette'):
            from .pixel_art import restrict_palette
            image=restrict_palette(image,finish['palette'],finish.get('dither',False))
        if finish.get('hardAlpha'):image.putalpha(image.getchannel('A').point(lambda v:255 if v>=128 else 0))
        return image

    def submit(self,document,args):
        self.start(); source_mode=args.get('source','layer'); layer=None; export_path=None
        if args.get('exportPath'):
            export_path=Path(args['exportPath']).expanduser().resolve()
            if export_path.suffix.lower() not in ('.gif','.mp4'):raise ValueError('Choose a GIF or MP4 filename')
            if export_path.exists():raise ValueError('That file already exists. Choose a new filename to preserve it.')
            if not export_path.parent.is_dir():raise ValueError('Choose an existing export folder')
            source_mode='treatment'
        if source_mode not in ('layer','composite','generated','treatment'): raise ValueError('Choose layer, composite, generated or treatment')
        if source_mode in ('layer','treatment'):
            layer=document.layer(args.get('layerId'))
            if layer.kind in ('group','adjustment'): raise ValueError('Choose a painted, image, text or shape layer, or use the complete composition')
            if source_mode=='treatment' and layer.effect_source is None: raise ValueError('This layer has no retained treatment source')
            image=layer.effect_source if source_mode=='treatment' else pixels.content(layer)
        else: image=document.render() if source_mode=='composite' else Image.new('RGBA',(document.width,document.height))
        if max(image.size)>3840: raise ValueError('Glitch Temple currently renders layers up to 3840 pixels per side. Use a smaller source layer or a resized copy.')
        engine_source=layer.provenance.get('glitchTemple',{}).get('sourceKind','layer') if source_mode=='treatment' else source_mode
        recipe=copy.deepcopy(args.get('recipe') or (layer.params.get('glitchRecipe') if layer else None))
        if recipe is None:
            if not self.catalog: raise ValueError('Glitch Temple is starting. Try again in a moment.')
            recipe=copy.deepcopy(self.catalog['defaults']); recipe.update(effects=[],colorMode='source')
        if len(recipe.get('effects',[]))>32: raise ValueError('Use at most 32 effects in one treatment')
        if recipe.get('schemaVersion')!=1 or not isinstance(recipe.get('effects'),list):raise ValueError('Choose a Glitch Temple recipe')
        recipe.update(renderWidth=image.width,renderHeight=image.height,renderSize=max(image.size),layers=[])
        if document.pixel_art or recipe.get('compositor',{}).get('pixelFinish'):
            integration=recipe.setdefault('compositor',{})
            finish=integration.setdefault('pixelFinish',{'paletteMode':'document' if document.pixel_art.get('palette') else 'effect','hardAlpha':True,'dither':False})
            if finish.get('paletteMode') not in ('document','effect'):raise ValueError('Choose document palette or effect colors')
            if finish['paletteMode']=='document' and (not export_path or not finish.get('palette')):
                finish['palette']=copy.deepcopy(document.pixel_art.get('palette') or finish.get('palette',[]))
                if not finish['palette']:raise ValueError('This document has no palette. Choose Effect colors or convert the artwork to a limited palette first.')
        output_size=export_dimensions(document,args) if export_path else None
        job_id=str(uuid.uuid4()); folder=self.root/job_id; folder.mkdir()
        image.save(folder/'source.png')
        selection=None
        if args.get('useSelection',True) and document.selection is not None and source_mode=='composite':
            document.selection.save(folder/'selection.png'); selection=True
        job={'id':job_id,'status':'queued','created':time.time(),'documentId':document.id,'sourceStateId':document.state_id,
             'source':source_mode,'engineSource':engine_source,'sourceLayerId':layer.id if layer else None,'size':list(image.size),'recipe':recipe,
             'preserveAlpha':bool(args.get('preserveAlpha',layer.provenance.get('glitchTemple',{}).get('preserveAlpha',True) if source_mode=='treatment' else source_mode=='layer')),'selection':selection,
             'name':str(args.get('name','Glitch Temple treatment')),'autoApply':bool(args.get('autoApply',False))}
        composition=Document();composition.restore(document.snapshot());self.compositions[job_id]=composition
        if export_path:
            frame_count=max(2,min(240,int(args.get('frames',recipe.get('loopFrames',36)))))
            fps=max(1,min(30,int(args.get('fps',recipe.get('loopFps',12)))))
            composition.save(folder/'composition.compwin',mark_saved=False)
            job.update(kind='loop',exportPath=str(export_path),frames=frame_count,fps=fps,framesRendered=0,
                       outputSize=output_size,autoApply=False,pixelArt=bool(document.pixel_art))
        self.jobs[job_id]=job; self.persist(job)
        self.queue.append({'id':job_id,'operation':'render','recipe':recipe,'width':image.width,'height':image.height,
                           'targetEffectId':args.get('targetEffectId'),**({'phase':0,'animated':True} if export_path else {})})
        self.pump(); return copy.deepcopy(job)

    def accept_frame(self,job,image):
        folder=self.root/job['id'];composition=self.compositions[job['id']]
        composition.layer(job['sourceLayerId']).image=image;composition._cache=None
        output=composition.render().resize(tuple(job['outputSize']),Image.Resampling.NEAREST if job['pixelArt'] else Image.Resampling.LANCZOS)
        job['hasTransparency']=job.get('hasTransparency',False) or output.getchannel('A').getextrema()[0]<255
        number=job['framesRendered'];output.save(folder/f'frame-{number:04d}.png')
        if number==0:
            output.save(folder/'result.png');job['result']=str(folder/'result.png')
        job['framesRendered']+=1
        if job['framesRendered']<job['frames']:
            job['status']='queued'
            self.queue.append({'id':job['id'],'operation':'render','recipe':job['recipe'],'width':job['size'][0],'height':job['size'][1],
                               'phase':2*math.pi*job['framesRendered']/job['frames'],'animated':True})
        else:self.encode(job)

    def encode(self,job):
        from .encoder import executable
        folder=self.root/job['id'];extension=Path(job['exportPath']).suffix.lower();temporary=folder/('loop'+extension)
        command=['-hide_banner','-loglevel','error','-y','-framerate',str(job['fps']),'-i',str(folder/'frame-%04d.png')]
        if extension=='.gif':command+=['-filter_complex',f'[0:v]split[a][b];[a]palettegen=reserve_transparent={int(job.get("hasTransparency",True))}[p];[b][p]paletteuse=dither=none','-loop','0']
        else:command+=['-vf','pad=ceil(iw/2)*2:ceil(ih/2)*2:color=black','-c:v','libx264','-pix_fmt','yuv420p','-crf','18','-movflags','+faststart']
        command.append(str(temporary))
        process=QProcess(self);self.encoders[job['id']]=process
        def finished(code,*_):
            if job['id'] not in self.encoders:return
            self.encoders.pop(job['id']);self.compositions.pop(job['id'],None)
            try:
                if job['status'] in ('stopping','cancelled'):job.update(status='cancelled')
                elif code!=0:raise ValueError(bytes(process.readAllStandardError()).decode(errors='replace').strip() or 'Animation export failed')
                else:
                    # Exclusive creation preserves any file written while frames were rendering.
                    import shutil
                    with open(temporary,'rb') as source,open(job['exportPath'],'xb') as destination:shutil.copyfileobj(source,destination)
                    job.update(status='complete',finished=time.time(),exported=True)
                    for path in folder.glob('frame-*.png'):path.unlink()
            except Exception as error:job.update(status='failed',error=str(error))
            self.persist(job);process.deleteLater()
        process.finished.connect(finished)
        process.errorOccurred.connect(lambda error:finished(-1) if error==QProcess.ProcessError.FailedToStart else None)
        job['status']='encoding';self.persist(job);process.start(str(executable()),command)

    def shutdown(self):
        for job in self.jobs.values():
            if job['status'] in ('queued','running','encoding','stopping'):
                job.update(status='cancelled');self.persist(job)
        self.queue.clear();self.current=None
        for process in list(self.encoders.values()):process.kill();process.waitForFinished(3000)
        self.compositions.clear()
        if self.page:self.page.deleteLater();self.page=None;self.catalog=None

    def apply(self,job_id):
        job=self.jobs[job_id]
        if job.get('kind') in ('loop','recipe'):raise ValueError('Render a still treatment before applying it to the artwork')
        document=self.ws.document(job['documentId'])
        if job['status']!='complete': raise ValueError('Wait for the treatment to finish')
        if job.get('applied'): raise ValueError('This treatment is already applied')
        if document.state_id!=job['sourceStateId']: raise ValueError('The artwork changed during rendering. The candidate is preserved; render again from the current artwork.')
        folder=self.root/job_id
        with Image.open(folder/'source.png') as image: source=image.convert('RGBA')
        with Image.open(job['result']) as image: result=image.convert('RGBA')
        before=document.snapshot()
        try:
            old=document.layer(job['sourceLayerId']) if job.get('sourceLayerId') else None
            if old and old.locked: raise ValueError('Unlock the source layer before applying this treatment')
            layer=self.prepare_layer(document,job,result,source);document._validate()
        except Exception: document.restore(before); raise
        document.history.append(('Glitch Temple',before)); document.history=document.history[-60:]; document.future=[]
        document.state_id=str(uuid.uuid4()); document.revision+=1; document._cache=None
        job.update(applied=True,appliedLayer=layer.id); self.persist(job); self.ws.notify(); return document.info()

    def prepare_layer(self,document,job,result,source):
        old=document.layer(job['sourceLayerId']) if job.get('sourceLayerId') else None
        if job['source']=='treatment':layer=old
        elif old:
            layer=old.clone();layer.id=str(uuid.uuid4());old.visible=False;document.active=old.id;document.add(layer)
        else:layer=Layer();document.add(layer)
        layer.kind='raster';layer.image=result;layer.effect_source=source;layer.name=job['name'];layer.visible=True
        layer.params={'glitchRecipe':copy.deepcopy(job['recipe'])}
        layer.provenance={**layer.provenance,'glitchTemple':{'jobId':job['id'],'engine':'Canvas','sourceStateId':job['sourceStateId'],'preserveAlpha':job['preserveAlpha'],'sourceKind':job.get('engineSource',job['source'])}}
        if document.pixel_art or not old:layer.resampling='nearest' if document.pixel_art else 'smooth'
        if job.get('selection'):
            with Image.open(self.root/job['id']/'selection.png') as mask:layer.mask=mask.convert('L')
        document.active=layer.id;document._cache=None;return layer

    def dispatch(self,args):
        self.start(); operation=args.get('operation','catalog')
        if operation=='catalog': return {'ready':bool(self.catalog),**(copy.deepcopy(self.catalog) if self.catalog else {})}
        if operation=='jobs': return list(copy.deepcopy(self.jobs).values())
        if operation=='job': return copy.deepcopy(self.jobs[args['jobId']])
        if operation in ('vary','normalize','palette'):
            job_id=str(uuid.uuid4());(self.root/job_id).mkdir()
            job={'id':job_id,'kind':'recipe','status':'queued','created':time.time(),'recipe':copy.deepcopy(args['recipe'])}
            self.jobs[job_id]=job;self.persist(job)
            self.queue.append({'id':job_id,'operation':operation,'recipe':job['recipe'],'kind':args.get('variation','structure')})
            self.pump();return copy.deepcopy(job)
        if operation=='capture':
            job=self.jobs[args['jobId']]
            scope=args.get('scope','composition')
            if scope not in ('composition','layer','original'):raise ValueError('Choose composition, layer or original')
            path=job.get('originalComposition') if scope=='original' else job.get('compositionResult',job.get('result')) if scope=='composition' else job.get('result')
            if not path: raise ValueError('Wait for the treatment to finish')
            with Image.open(path) as image:
                image.thumbnail((int(args.get('maxDimension',1600)),)*2,Image.Resampling.NEAREST)
                data=io.BytesIO();image.save(data,'PNG')
            return {'mimeType':'image/png','data':base64.b64encode(data.getvalue()).decode()}
        if operation=='render': return self.submit(self.ws.document(args.get('documentId')),args)
        if operation=='export':
            if not args.get('path'):raise ValueError('Choose a GIF or MP4 filename')
            return self.submit(self.ws.document(args.get('documentId')),{**args,'exportPath':args['path']})
        if operation=='apply': return self.apply(args['jobId'])
        if operation=='cancel':
            job=self.jobs[args['jobId']]
            if job['status']=='queued': self.queue=[r for r in self.queue if r['id']!=job['id']]; job['status']='cancelled'
            elif job['status'] in ('running','encoding'):
                job['status']='stopping'
                if job['id'] in self.encoders:self.encoders[job['id']].kill()
            if job['status']=='cancelled':self.compositions.pop(job['id'],None)
            self.persist(job); return copy.deepcopy(job)
        raise ValueError('Unknown Glitch Temple operation')
