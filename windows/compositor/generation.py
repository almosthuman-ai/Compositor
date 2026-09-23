"""Provider-independent immutable requests and candidates. Qt owns application, workers own network I/O."""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import base64, copy, io, json, os, time, urllib.request, urllib.error, uuid
from PIL import Image
from .settings import atomic_json
from .generation_source import prepare_source, region_instruction, normalize_candidate
from .pixels import resampling

def http_json(url,body=None,headers=None,timeout=300):
    request=urllib.request.Request(url,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json',**(headers or {})})
    try:
        with urllib.request.urlopen(request,timeout=timeout) as response: return json.load(response)
    except urllib.error.HTTPError as e:
        detail=e.read().decode('utf-8',errors='replace')
        try: detail=json.loads(detail).get('error',{}).get('message',detail)
        except (ValueError,AttributeError): pass
        raise RuntimeError(f'Image provider returned HTTP {e.code}: {detail[:1800]}') from None

def generate_provider(config,key,prompt,images,size,mask=None):
    provider=config['provider']; model=config['model']
    if not key: raise ValueError(f'Add your {provider.title()} API key in Settings')
    if provider=='openai':
        endpoint=config.get('openai_url','https://api.openai.com/v1').rstrip('/')
        params={'model':model,'prompt':prompt,'size':size,'quality':config.get('quality','high'),'n':1,'output_format':'png'}
        headers={'Authorization':f'Bearer {key}'}
        if images:
            boundary=uuid.uuid4().hex; parts=[]
            for name,value in params.items(): parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
            for i,path in enumerate(images):
                parts.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="image[]"; filename="input-{i}.png"\r\nContent-Type: image/png\r\n\r\n'.encode(),Path(path).read_bytes(),b'\r\n'])
            if mask:
                parts.extend([f'--{boundary}\r\nContent-Disposition: form-data; name="mask"; filename="mask.png"\r\nContent-Type: image/png\r\n\r\n'.encode(),Path(mask).read_bytes(),b'\r\n'])
            parts.append(f'--{boundary}--\r\n'.encode()); headers['Content-Type']=f'multipart/form-data; boundary={boundary}'
            req=urllib.request.Request(endpoint+'/images/edits',data=b''.join(parts),headers=headers)
            try:
                with urllib.request.urlopen(req,timeout=300) as response: result=json.load(response)
            except urllib.error.HTTPError as e: raise RuntimeError(f'Image provider HTTP {e.code}: {e.read().decode(errors="replace")[:1800]}') from None
        else: result=http_json(endpoint+'/images/generations',params,headers)
        item=result.get('data',[{}])[0]
        if not item.get('b64_json'): raise RuntimeError('Provider returned no image bytes')
        return base64.b64decode(item['b64_json']),result.get('usage')
    if provider=='gemini':
        parts=[{'text':prompt}]
        parts.extend({'inlineData':{'mimeType':'image/png','data':base64.b64encode(Path(p).read_bytes()).decode()}} for p in images)
        config_image={'imageSize':config.get('imageSize','2K')}
        if config.get('aspectRatio'): config_image['aspectRatio']=config['aspectRatio']
        endpoint=config.get('gemini_url','https://generativelanguage.googleapis.com/v1beta').rstrip('/')
        result=http_json(f'{endpoint}/models/{model}:generateContent',{'contents':[{'parts':parts}],'generationConfig':{'responseModalities':['TEXT','IMAGE'],'imageConfig':config_image}},{'x-goog-api-key':key})
        output=result.get('candidates',[{}])[0].get('content',{}).get('parts',[])
        found=[p['inlineData'] for p in output if p.get('inlineData') and not p.get('thought')]
        if not found: raise RuntimeError('Provider returned no image: '+' '.join(p.get('text','') for p in output)[:1500])
        return base64.b64decode(found[-1]['data']),result.get('usageMetadata')
    raise ValueError('Choose an OpenAI-compatible or Gemini image provider')

class Generation:
    def __init__(self,settings,on_complete,provider=generate_provider):
        self.settings=settings; self.root=settings.root/'generations'; self.root.mkdir(exist_ok=True)
        self.on_complete=on_complete; self.provider=provider; self.pool=ThreadPoolExecutor(max_workers=2,thread_name_prefix='image-generation'); self.jobs={}
        for path in self.root.glob('*/job.json'):
            try:
                job=json.loads(path.read_text(encoding='utf-8'))
                if job['status'] in ('queued','running'):
                    job.update(status='failed',error='The application stopped during this request. The saved source is intact; retry explicitly.',finished=time.time()); atomic_json(path,job)
                self.jobs[job['id']]=job
            except (ValueError,KeyError): continue

    def submit(self,document,args):
        prompt=args.get('prompt','').strip()
        if not prompt: raise ValueError('Describe the image or change you want')
        config={**self.settings.values,**{k:v for k,v in args.items() if k in ('provider','model','quality','imageSize','aspectRatio')}}
        key=self.settings.key(config['provider'])
        if not key: raise ValueError('Configure your image provider in Settings first')
        job_id=str(uuid.uuid4()); folder=self.root/job_id; folder.mkdir()
        kind=args.get('kind','generate'); source=prepare_source(document,kind,args.get('box'),folder,args.get('resampling'))
        images=[source['sourcePath']] if source['sourcePath'] else []
        if source.get('editArea'): prompt+='\n\n'+region_instruction(source)
        for i,reference in enumerate(args.get('references',[])):
            path=reference['path'] if isinstance(reference,dict) else reference
            with Image.open(path) as im: im.convert('RGBA').save(folder/f'reference-{i}.png')
            images.append(str(folder/f'reference-{i}.png'))
        size=args.get('size','1024x1024')
        job={**source,'id':job_id,'status':'queued','created':time.time(),'documentId':document.id,'sourceRevision':document.revision,'sourceStateId':document.state_id,'kind':kind,'prompt':prompt,'config':config,'size':size,'inputs':images,'references':copy.deepcopy(args.get('references',[])),'autoApply':bool(args.get('autoApply',False))}
        job['userPrompt']=args.get('userPrompt',prompt); job['creativeContext']=copy.deepcopy(args.get('creativeContext',{}))
        # Only non-secret provider configuration is retained. Credentials remain in the user's key store.
        self.jobs[job_id]=job; atomic_json(folder/'job.json',job)
        self.pool.submit(self._run,copy.deepcopy(job),key)
        return copy.deepcopy(job)

    def _run(self,job,key):
        folder=self.root/job['id']; job['status']='running'; atomic_json(folder/'job.json',job)
        self.on_complete(copy.deepcopy(job))
        try:
            raw,usage=self.provider(job['config'],key,job['prompt'],job['inputs'],job['size'])
            (folder/'provider-original').write_bytes(raw)
            with Image.open(io.BytesIO(raw)) as im:
                actual=list(im.size); candidate=normalize_candidate(im,job); candidate.save(folder/'result.png')
                job['candidateSize']=list(candidate.size)
            job.update(status='complete',result=str(folder/'result.png'),actualSize=actual,usage=usage)
        except Exception as e: job.update(status='failed',error=str(e))
        job['finished']=time.time(); atomic_json(folder/'job.json',job)
        self.on_complete(job)

    def receive(self,job): self.jobs[job['id']]=job

    def application_error(self,document,job_id):
        job=self.jobs[job_id]
        if job['status']!='complete': return 'The image is not complete.'
        if job.get('applied'): return 'This candidate has already been applied; use Undo or duplicate its layer.'
        if job['documentId']!=document.id: return 'This candidate belongs to another document.'
        if not job.get('sourceStateId'): return 'This older candidate has no saved source identity. Preview it, then use Place as layer to position it manually.'
        if job['sourceStateId']!=document.state_id: return 'The artwork changed after generation. The candidate is preserved; place it manually or generate from the current artwork.'
        return None

    def candidate_layer(self,document,job_id,palette_mode='document'):
        """The same logical pixels are used by inspection and application."""
        from .document import Layer
        job=self.jobs[job_id]
        if job['status']!='complete': raise ValueError('The image is not complete')
        if job['documentId']!=document.id: raise ValueError('This candidate belongs to another document')
        if palette_mode not in ('document','candidate'): raise ValueError('Choose document or candidate colors')
        method='nearest' if document.pixel_art else job.get('resampling','smooth')
        with Image.open(job['result']) as source: im=source.convert('RGBA')
        box=job.get('box'); x=y=0; mask=None
        if box:
            if job.get('workingContentBox'):
                im=im.resize(tuple(job['workingSize']),resampling(method)).crop(tuple(job['workingContentBox']))
            im=im.resize((box['width'],box['height']),resampling(method)); x,y=box['x'],box['y']
            mask_path=self.root/job_id/'selection.png'
            if mask_path.exists():
                with Image.open(mask_path) as source: mask=source.convert('L')
        if document.pixel_art:
            from .pixel_art import convert
            if not box: im=im.resize((document.width,document.height),Image.Resampling.NEAREST)
            palette=document.pixel_art.get('palette') if palette_mode=='document' else None
            if palette and len(palette)==1: palette=palette*2
            if palette:
                im,_=convert(im,{'width':im.width,'height':im.height,'palette':palette,'sampling':'nearest'})
            else: im.putalpha(im.getchannel('A').point(lambda value:255 if value>=128 else 0))
            if mask is not None: mask=mask.point(lambda value:255 if value>=128 else 0)
        return Layer(name=job.get('userPrompt',job['prompt'])[:48],image=im,mask=mask,x=x,y=y,resampling=method,provenance={'generationId':job_id,'provider':job['config']['provider'],'model':job['config']['model'],'prompt':job['prompt'],'creativeContext':job.get('creativeContext',{}),'sourceRevision':job['sourceRevision'],'sourceStateId':job.get('sourceStateId'),'pixelPalette':palette_mode if document.pixel_art else None})

    def preview(self,document,job_id,palette_mode='document'):
        from .pixels import placed
        layer=self.candidate_layer(document,job_id,palette_mode)
        return Image.alpha_composite(document.render(),placed(layer,(document.width,document.height)))

    def apply(self,document,job_id,palette_mode='document'):
        job=self.jobs[job_id]
        error=self.application_error(document,job_id)
        if error: raise ValueError(error)
        before=document.snapshot()
        try:
            document.add(self.candidate_layer(document,job_id,palette_mode))
            document._validate()
        except Exception: document.restore(before); raise
        document.history.append(('generation',before)); document.history=document.history[-60:]; document.future=[]
        document.state_id=str(uuid.uuid4()); document.revision+=1; document._cache=None
        job.update(applied=True,appliedLayer=document.active); atomic_json(self.root/job_id/'job.json',job)
        return document.info()
