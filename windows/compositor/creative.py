"""Owned style profiles and reproducible creative context for every generation route."""
from pathlib import Path
import copy,json,uuid
from PIL import Image,ImageOps
from .settings import atomic_json


class CreativeLibrary:
    def __init__(self,settings):
        self.root=settings.root/'styles'; self.root.mkdir(exist_ok=True)
        self.presets=json.loads((Path(__file__).parent/'prompts/styles.json').read_text(encoding='utf-8'))
        self.custom={}
        for path in self.root.glob('*/style.json'):
            try:
                value=json.loads(path.read_text(encoding='utf-8')); self.custom[value['id']]=value
            except (ValueError,KeyError): continue

    def list(self): return copy.deepcopy([{**v,'builtin':True,'references':[]} for v in self.presets]+list(self.custom.values()))
    def get(self,style_id):
        value=next((v for v in self.list() if v['id']==style_id),None)
        if value is None: raise ValueError('Choose a style from the library')
        return value

    def save(self,args):
        name=str(args.get('name','')).strip()
        if not name: raise ValueError('Give this style a name')
        style_id=args.get('id')
        if style_id and style_id not in self.custom: raise ValueError('Save a copy to customize a built-in style')
        style_id=style_id or str(uuid.uuid4()); folder=self.root/style_id; folder.mkdir(exist_ok=True)
        value={'id':style_id,'name':name,'prefix':str(args.get('prefix','')),'suffix':str(args.get('suffix','')),'builtin':False,'references':[]}
        for reference in args.get('references',[]):
            path=reference['path'] if isinstance(reference,dict) else reference
            target=folder/(str(uuid.uuid4())+'.png')
            with Image.open(path) as im: ImageOps.exif_transpose(im).convert('RGBA').save(target)
            value['references'].append({'path':str(target),'role':'style','label':reference.get('label',Path(path).stem) if isinstance(reference,dict) else Path(path).stem})
        atomic_json(folder/'style.json',value); self.custom[style_id]=value; return copy.deepcopy(value)


def compose(prompt,kind='generate',style=None,story='',direction='',characters=(),references=(),project_id=None,page_id=None):
    """References are ordered exactly as the provider receives them, including a source image."""
    if not prompt.strip(): raise ValueError('Describe the image or change you want')
    style=copy.deepcopy(style); cast=copy.deepcopy(list(characters)); refs=copy.deepcopy(list(references))
    parts=[]
    if style and style.get('prefix','').strip(): parts.append(style['prefix'].strip())
    if story.strip(): parts.append('Story context:\n'+story.strip())
    if direction.strip(): parts.append('Project art direction:\n'+direction.strip())
    if cast:
        parts.append('Characters in this image:\n'+'\n'.join(c['name']+(': '+c['description'] if c.get('description') else '') for c in cast))
    if kind in ('edit','patch'): parts.append('Image 1 is the source '+('region' if kind=='patch' else 'composition')+' to edit.')
    offset=2 if kind in ('edit','patch') else 1
    for i,ref in enumerate(refs,offset):
        role=ref.get('role','reference'); name=ref.get('label') or Path(ref['path']).stem
        purpose={'character':'Preserve this character’s identifying facial features, proportions and costume details.','style':'Use its visual treatment, palette and mark-making.','composition':'Use its spatial arrangement and framing.'}.get(role,'Use this image as visual guidance.')
        parts.append(f'Image {i}: {role} reference — {name}. {purpose}')
    parts.append('Image request:\n'+prompt.strip())
    if style and style.get('suffix','').strip(): parts.append(style['suffix'].strip())
    return {'prompt':'\n\n'.join(parts),'userPrompt':prompt.strip(),'references':refs,'creativeContext':{'style':style,'characters':cast,'projectId':project_id,'pageId':page_id}}
