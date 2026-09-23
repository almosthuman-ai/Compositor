"""The single owner of open documents for the native UI and external operators."""
from pathlib import Path
import base64, io, json, time
from PySide6.QtCore import QObject, Signal, QTimer
from PIL import Image
from .document import Document
from .generation import Generation
from .connectors import StudioConnector
from .settings import atomic_json
from .projects import Projects

class Workspace(QObject):
    changed=Signal()
    job_finished=Signal(dict)
    request_received=Signal(object)
    message=Signal(str)
    def __init__(self,settings,restore=True):
        super().__init__(); self.settings=settings; self.documents={}; self.active=None; self.view={'tool':'move','zoom':1}; self.window=None; self.prepared_generation=None; self.recovered_revisions={}
        self.job_finished.connect(self.finish_job); self.request_received.connect(self.handle_request)
        self.generation=Generation(settings,self.job_finished.emit)
        self.projects=Projects(self)
        self.autosave=QTimer(self); self.autosave.setSingleShot(True); self.autosave.setInterval(2000); self.autosave.timeout.connect(self.save_recovery)
        if restore: self.restore_recovery()

    def document(self,document_id=None):
        d=self.documents.get(document_id or self.active)
        if d is None: raise ValueError('Open or create a document first')
        return d

    def notify(self): self.changed.emit(); self.autosave.start()

    def state(self):
        return {'service':'compositor','activeDocument':self.active,'documents':[d.info() for d in self.documents.values()],
                'view':self.view,'jobs':list(self.generation.jobs.values()),'settings':self.settings.public(),'production':self.projects.info()}

    def dispatch(self,action,args=None):
        a=args or {}
        if action=='state': return self.state()
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
            d.execute('add_layer',{'name':'Background','color':a.get('background','#ffffff')}); self.documents[d.id]=d; self.active=d.id; self.notify(); return d.info()
        if action=='open':
            if Path(a['path']).suffix.lower()=='.compbook':
                result=self.projects.open_bundle(a['path']); self.notify(); return result
            d=Document.load(a['path'])
            if d.id in self.documents: self.active=d.id
            else: self.documents[d.id]=d; self.active=d.id
            self.notify(); return {**d.info(),'conversionReport':getattr(d,'conversion_report',[])}
        if action=='activate':
            self.active=self.document(a['documentId']).id
            linked=self.projects.for_document(self.active)
            if linked: self.projects.active=linked[0]['id']; linked[0]['activePage']=linked[1]['id']
            self.changed.emit(); return self.document().info()
        if action=='view':
            self.view.update(a); self.changed.emit(); return self.view
        if action=='settings':
            allowed={'provider','model','quality','imageSize','aspectRatio','studio_url','openai_url','gemini_url','codex_path'}
            for k,v in a.items():
                if k not in allowed: raise ValueError(f'Unsupported setting {k}')
                self.settings.values[k]=v
            self.settings.save(); self.changed.emit(); return self.settings.public()
        if action=='jobs': return list(self.generation.jobs.values())
        if action=='job': return self.generation.jobs[a['jobId']]
        if action=='connector_projects': return self.connector().projects()
        if action=='connector_action': return self.connector().action(a['action'],a.get('args',{}))
        if action=='connector_pull':
            result=self.connector().pull(a['projectId'],a.get('role','background'),a.get('page',1)); d=Document.load(result['path']); d.title=result['title']; d.studio=result['link']
            self.documents[d.id]=d; self.active=d.id; self.notify(); return d.info()
        d=self.document(a.get('documentId'))
        if action=='document': return d.info()
        if action=='edit':
            result=d.execute(a['operation'],a.get('args'),a.get('expectedRevision')); self.notify(); return result
        if action=='save':
            result=d.save(a.get('path') or d.path); self.notify(); return result
        if action=='export': return d.export(a['path'],a.get('quality',95))
        if action=='close':
            if d.revision!=d.saved_revision and not a.get('discard'): raise ValueError('Save this document first, or explicitly discard its unsaved changes')
            if self.projects.for_document(d.id): self.projects.flush()
            del self.documents[d.id]; self.active=next(iter(self.documents),None); self.notify(); return self.state()
        if action=='capture':
            im=d.render(); region=a.get('region')
            if region:
                x,y,w,h=[int(region[k]) for k in ('x','y','width','height')]
                if min(x,y)<0 or min(w,h)<1 or x+w>im.width or y+h>im.height: raise ValueError('Inspection region must fit inside the canvas')
                im=im.crop((x,y,x+w,y+h))
            if a.get('maxDimension'):
                im=im.copy(); im.thumbnail((int(a['maxDimension']),)*2,Image.Resampling.LANCZOS)
            bg=Image.new('RGBA',im.size,'white'); im=Image.alpha_composite(bg,im).convert('RGB'); data=io.BytesIO(); im.save(data,'JPEG',quality=90,subsampling=0)
            return {'documentId':d.id,'revision':d.revision,'width':im.width,'height':im.height,'mimeType':'image/jpeg','data':base64.b64encode(data.getvalue()).decode()}
        if action=='prepare_generation':
            import uuid
            folder=self.settings.root/'prepared'/str(uuid.uuid4()); folder.mkdir(parents=True)
            im=d.render(); box=a.get('box'); kind=a.get('kind','edit')
            if kind=='patch':
                if box is None and d.selection is not None:
                    bounds=d.selection.getbbox()
                    if bounds: box={'x':bounds[0],'y':bounds[1],'width':bounds[2]-bounds[0],'height':bounds[3]-bounds[1]}
                if box is None: raise ValueError('Select the region to send for refinement')
                x,y=int(box['x']),int(box['y']); w=int(box.get('width',box.get('size',0))); h=int(box.get('height',box.get('size',0)))
                if min(x,y)<0 or min(w,h)<1 or x+w>im.width or y+h>im.height: raise ValueError('Region must fit inside the canvas')
                box={'x':x,'y':y,'width':w,'height':h}; im=im.crop((x,y,x+w,y+h))
                if d.selection is not None: d.selection.crop((x,y,x+w,y+h)).save(folder/'selection.png')
            im.save(folder/'source.png')
            self.prepared_generation={'documentId':d.id,'sourceRevision':d.revision,'kind':kind,'box':box,'sourcePath':str(folder/'source.png'),'created':time.time()}
            atomic_json(folder/'source.json',self.prepared_generation); return self.prepared_generation
        if action=='generate':
            result=self.generation.submit(d,a); self.changed.emit(); return result
        if action=='apply_generation':
            result=self.generation.apply(d,a['jobId']); self.notify(); return result
        if action=='connector_push': return self.connector().push(d,a.get('projectId') or d.studio.get('lessonId'),a.get('role','background'),a.get('page',1))
        raise ValueError(f'Unknown action: {action}')

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
                records.append({'id':d.id,'file':str(file),'path':d.path,'dirty':d.revision!=d.saved_revision})
            atomic_json(folder/'session.json',{'documents':records,'active':self.active,'activeProject':self.projects.active})
        except Exception as e: self.message.emit('Recovery save failed: '+str(e))

    def restore_recovery(self):
        index=self.settings.root/'recovery/session.json'
        if not index.exists(): return
        try:
            state=json.loads(index.read_text(encoding='utf-8'))
            for row in state['documents']:
                d=Document.load(row['file']); d.path=row.get('path'); d.saved_revision=-1 if row['dirty'] else 0; self.documents[d.id]=d
            self.active=state.get('active')
            self.projects.active=state.get('activeProject')
        except Exception as e: self.message.emit('Recovery could not be fully restored: '+str(e))
