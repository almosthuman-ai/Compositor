"""Portable production projects over the editor's canonical layered documents."""
from pathlib import Path
import copy, html, io, json, os, tempfile, uuid, zipfile
from PIL import Image, ImageOps
from .document import Document
from .settings import atomic_json


class Projects:
    def __init__(self,workspace):
        self.ws=workspace; self.root=workspace.settings.root/'projects'; self.root.mkdir(exist_ok=True)
        self.items={}; self.active=None; self.saved_revisions={}
        for path in self.root.glob('*/project.json'):
            try:
                project=json.loads(path.read_text(encoding='utf-8')); self.items[project['id']]=project
            except (ValueError,KeyError): continue

    def get(self,project_id=None):
        project=self.items.get(project_id or self.active)
        if project is None: raise ValueError('Create or select a project first')
        return project

    def page(self,project,page_id=None):
        page_id=page_id or project.get('activePage')
        page=next((p for p in project['pages'] if p['id']==page_id),None)
        if page is None: raise ValueError('Select a page in this project')
        return page

    def folder(self,project): return self.root/project['id']
    def page_file(self,project,page): return self.folder(project)/'pages'/(page['id']+'.compwin')

    def for_document(self,document_id):
        return next(((p,page) for p in self.items.values() for page in p['pages'] if page['documentId']==document_id),None)

    def write(self,project):
        atomic_json(self.folder(project)/'project.json',project)

    def info(self,project=None):
        if project is None: return {'activeProject':self.active,'projects':[copy.deepcopy(p) for p in self.items.values()]}
        return copy.deepcopy(project)

    def document(self,project,page):
        document=self.ws.documents.get(page['documentId'])
        if document is not None: return document
        document=Document.load(self.page_file(project,page)); document.path=None
        return document

    def flush(self):
        for project in self.items.values():
            for page in project['pages']:
                d=self.ws.documents.get(page['documentId'])
                if d is not None and self.saved_revisions.get(d.id)!=(id(d),d.revision):
                    d.save(self.page_file(project,page),mark_saved=False); self.saved_revisions[d.id]=(id(d),d.revision)

    def select(self,project,page):
        was_open=page['documentId'] in self.ws.documents
        d=self.document(project,page); self.ws.documents[d.id]=d; self.ws.active=d.id
        if not was_open: self.saved_revisions[d.id]=(id(d),d.revision)
        self.active=project['id']; project['activePage']=page['id']; self.write(project)
        return self.info(project)

    def add_page(self,project,args):
        if len(project['pages'])>=64: raise ValueError('A project can contain up to 64 pages')
        d=self.ws.document(args['documentId']) if args.get('documentId') else Document(args.get('width',project['width']),args.get('height',project['height']),args.get('title') or f"Page {len(project['pages'])+1}")
        if any(page['documentId']==d.id for p in self.items.values() for page in p['pages']): raise ValueError('This document already belongs to a project; duplicate it to add another page')
        if not args.get('documentId'): d.execute('add_layer',{'name':'Background','color':'white'})
        page={'id':str(uuid.uuid4()),'documentId':d.id,'title':args.get('title',d.title),'text':args.get('text',''),'prompt':args.get('prompt',''),'splitY':None}
        project['pages'].append(page); d.save(self.page_file(project,page),mark_saved=False); self.saved_revisions[d.id]=(id(d),d.revision); self.write(project)
        return page,d

    def dispatch(self,action,args):
        a=args or {}
        if action=='list': return self.info()
        if action=='new':
            kind=a.get('kind','artwork')
            if kind not in ('artwork','comic','book'): raise ValueError('Choose artwork, comic or book')
            count=int(a.get('pageCount',1 if kind=='artwork' else 4))
            if not 1<=count<=64: raise ValueError('Choose 1–64 pages')
            from .document import dimensions
            width,height=dimensions(a.get('width',1536),a.get('height',1024))
            project={'format':'com.compositor.production','version':1,'id':str(uuid.uuid4()),'title':a.get('title','Untitled project'),'kind':kind,'width':width,'height':height,'story':'','artDirection':'','pages':[],'references':[],'activePage':None}
            self.items[project['id']]=project
            for _ in range(count): self.add_page(project,{})
            return self.select(project,project['pages'][0])
        if action=='open': return self.open_bundle(a['path'])
        project=self.get(a.get('projectId'))
        if action=='get': return self.info(project)
        if action=='select': return self.select(project,self.page(project,a.get('pageId')))
        if action=='update':
            for key in ('title','story','artDirection'):
                if key in a: project[key]=str(a[key])
        elif action=='add_page':
            page,d=self.add_page(project,a); self.ws.documents[d.id]=d
            return self.select(project,page)
        elif action=='update_page':
            page=self.page(project,a.get('pageId'))
            if 'splitY' in a and a['splitY'] is not None:
                d=self.document(project,page)
                if not 0<int(a['splitY'])<d.height: raise ValueError('Panel split must be inside the page')
            if 'title' in a and str(a['title'])!=page['title']:
                d=self.document(project,page); d.execute('rename',{'title':str(a['title'])})
                if d.id not in self.ws.documents: d.save(self.page_file(project,page),mark_saved=False)
            for key in ('title','text','prompt'):
                if key in a: page[key]=str(a[key])
            if 'splitY' in a: page['splitY']=None if a['splitY'] is None else int(a['splitY'])
        elif action=='reorder_page':
            page=self.page(project,a['pageId']); project['pages'].remove(page); project['pages'].insert(max(0,min(len(project['pages']),int(a['index']))),page)
        elif action=='remove_page':
            if len(project['pages'])<=1: raise ValueError('Keep at least one page in the project')
            page=self.page(project,a['pageId']); project['pages'].remove(page)
            # The document and saved page remain recoverable after removal.
            if project['activePage']==page['id']: project['activePage']=project['pages'][0]['id']
        elif action=='add_reference':
            role=a.get('role','style')
            if role not in ('character','style','composition'): raise ValueError('Reference role must be character, style or composition')
            reference={'id':str(uuid.uuid4()),'role':role,'label':a.get('label') or Path(a['path']).stem}
            target=self.folder(project)/'references'/(reference['id']+'.png'); target.parent.mkdir(exist_ok=True)
            with Image.open(a['path']) as im: ImageOps.exif_transpose(im).convert('RGBA').save(target)
            reference['file']='references/'+reference['id']+'.png'; project['references'].append(reference)
        elif action=='remove_reference': project['references']=[r for r in project['references'] if r['id']!=a['referenceId']]
        elif action=='save': return self.save_bundle(project,a['path'])
        elif action=='export': return self.export(project,a['path'])
        elif action=='generate':
            page=self.page(project,a.get('pageId')); self.select(project,page)
            prompt=a.get('prompt') or page['prompt']
            if not prompt.strip(): raise ValueError('Describe the image for this page')
            context=[project['artDirection'],project['story'],prompt]
            references=[]
            for i,reference in enumerate(project['references']):
                context.append(f"Reference {i+1}: {reference['role']} — {reference['label']}")
                references.append({'path':str(self.folder(project)/reference['file']),'role':reference['role'],'label':reference['label']})
            request={**a,'prompt':'\n\n'.join(p for p in context if p),'references':references}
            d=self.ws.document(); request.setdefault('size',f'{d.width}x{d.height}')
            request['kind']=a.get('generationKind','generate'); request.pop('projectId',None); request.pop('pageId',None)
            return self.ws.dispatch('generate',request)
        else: raise ValueError('Unknown project action: '+action)
        self.write(project); return self.info(project)

    def save_bundle(self,project,path):
        target=Path(path).resolve()
        if target.suffix.lower()!='.compbook': raise ValueError('Save projects with the .compbook extension')
        self.flush(); target.parent.mkdir(parents=True,exist_ok=True); temp=target.with_name(target.name+'.'+str(uuid.uuid4())+'.tmp')
        try:
            with zipfile.ZipFile(temp,'w',zipfile.ZIP_DEFLATED) as archive:
                archive.writestr('project.json',json.dumps(project,ensure_ascii=False))
                for page in project['pages']: archive.write(self.page_file(project,page),'pages/'+page['id']+'.compwin')
                for reference in project['references']: archive.write(self.folder(project)/reference['file'],reference['file'])
            os.replace(temp,target)
            for page in project['pages']:
                d=self.ws.documents.get(page['documentId'])
                if d is not None: d.saved_revision=d.revision
        finally:
            if temp.exists(): temp.unlink()
        return {'path':str(target),'bytes':target.stat().st_size,'pages':len(project['pages'])}

    def open_bundle(self,path):
        # Import under fresh project/document identities so another open version
        # and its unsaved edits remain owned by their existing documents.
        with zipfile.ZipFile(path) as archive:
            project=json.loads(archive.read('project.json'))
            if project.get('format')!='com.compositor.production' or project.get('version')!=1: raise ValueError('Unsupported production project')
            if not 1<=len(project['pages'])<=64: raise ValueError('Project needs 1–64 pages')
            for page in project['pages']:
                if str(uuid.UUID(page['id']))!=page['id']: raise ValueError('Invalid page identity')
            for reference in project['references']:
                if reference['file']!='references/'+str(uuid.UUID(reference['id']))+'.png': raise ValueError('Invalid reference identity')
            project['id']=str(uuid.uuid4()); folder=self.folder(project); folder.mkdir()
            with tempfile.TemporaryDirectory(prefix='compositor-import-') as temporary:
                for page in project['pages']:
                    entry='pages/'+page['id']+'.compwin'; raw=archive.read(entry)
                    extracted=Path(temporary)/'page.compwin'; extracted.write_bytes(raw)
                    d=Document.load(extracted); d.id=str(uuid.uuid4()); d.path=None; page['documentId']=d.id
                    d.save(self.page_file(project,page),mark_saved=False)
                for reference in project['references']:
                    name=reference['file']
                    if not name.startswith('references/') or '..' in Path(name).parts or Path(name).is_absolute(): raise ValueError('Invalid reference path')
                    target=folder/name; target.parent.mkdir(exist_ok=True); target.write_bytes(archive.read(name))
        self.items[project['id']]=project; self.write(project)
        return self.select(project,self.page(project))

    def export(self,project,path):
        target=Path(path).resolve(); target.parent.mkdir(parents=True,exist_ok=True)
        if target.suffix.lower() not in ('.html','.pdf'): raise ValueError('Export a self-contained .html reading copy or .pdf')
        import base64
        pages=[]
        for index,page in enumerate(project['pages']):
            im=self.document(project,page).render(); data=io.BytesIO(); im.save(data,'PNG')
            paragraphs=''.join('<p>'+html.escape(p)+'</p>' for p in page['text'].split('\n') if p.strip())
            pages.append('<div class="page"'+(' style="page-break-before:always"' if index else '')+'><h2>'+html.escape(page['title'])+'</h2><img width="640" alt="'+html.escape(page['title'],quote=True)+'" src="data:image/png;base64,'+base64.b64encode(data.getvalue()).decode()+'">'+paragraphs+'</div>')
        body='<!doctype html><html><head><meta charset="utf-8"><title>'+html.escape(project['title'])+'</title><style>body{font:20px/1.6 Georgia,serif;max-width:900px;margin:40px auto;padding:0 24px;color:#242424}.page{margin-bottom:64px}img{max-width:100%;height:auto}h2{font:600 22px sans-serif}p{white-space:pre-wrap}</style></head><body><h1>'+html.escape(project['title'])+'</h1>'+''.join(pages)+'</body></html>'
        temp=target.with_name(target.stem+'.'+str(uuid.uuid4())+target.suffix)
        try:
            if target.suffix.lower()=='.html': temp.write_text(body,encoding='utf-8')
            else:
                from PySide6.QtGui import QTextDocument, QPageSize
                from PySide6.QtPrintSupport import QPrinter
                printer=QPrinter(QPrinter.PrinterMode.HighResolution); printer.setOutputFormat(QPrinter.OutputFormat.PdfFormat); printer.setOutputFileName(str(temp)); printer.setPageSize(QPageSize(QPageSize.PageSizeId.A4))
                text=QTextDocument(); text.setHtml(body); text.print_(printer)
                if not temp.exists() or temp.stat().st_size<100: raise RuntimeError('PDF export produced no document')
            os.replace(temp,target)
        finally:
            if temp.exists(): temp.unlink()
        return {'path':str(target),'bytes':target.stat().st_size,'pages':len(project['pages'])}
