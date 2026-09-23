"""Immutable pixel references with transactional edits, editable layers and recoverable history."""
from dataclasses import dataclass, field, replace
from pathlib import Path
import copy, io, json, math, os, uuid, zipfile
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageOps
from . import pixels

def uid(): return str(uuid.uuid4())
def dimensions(w,h):
    w,h=int(w),int(h)
    if not (1 <= w <= 30000 and 1 <= h <= 30000 and w*h <= 100_000_000): raise ValueError('Canvas must be 1–30,000 pixels per side and at most 100 megapixels')
    return w,h

@dataclass
class Layer:
    name: str = 'Layer'
    id: str = field(default_factory=uid)
    kind: str = 'raster'
    image: object = None
    mask: object = None
    mask_enabled: bool = True
    visible: bool = True
    locked: bool = False
    opacity: float = 1
    blend: str = 'normal'
    x: float = 0
    y: float = 0
    sx: float = 1
    sy: float = 1
    angle: float = 0
    parent: str | None = None
    clipping: bool = False
    params: dict = field(default_factory=dict)
    effects: dict = field(default_factory=dict)
    provenance: dict = field(default_factory=dict)

    def clone(self):
        return replace(self,params=copy.deepcopy(self.params),effects=copy.deepcopy(self.effects),provenance=copy.deepcopy(self.provenance))

    def info(self):
        result={k:v for k,v in vars(self).items() if k not in ('image','mask')}
        im=pixels.content(self) if self.kind not in ('group','adjustment') else None
        return {**result,'pixelWidth':im.width if im else 0,'pixelHeight':im.height if im else 0,'hasMask':self.mask is not None}

class Document:
    def __init__(self,width=1536,height=1024,title='Untitled'):
        self.width,self.height=dimensions(width,height); self.title=title; self.id=uid()
        self.layers=[]; self.active=None; self.selection=None; self.revision=0
        self.state_id=uid(); self.saved_state_id=None; self.saved_revision=-1
        self.path=None; self.history=[]; self.future=[]; self.guides=[]; self.studio={}; self._cache=None

    def snapshot(self):
        return (self.width,self.height,self.title,[l.clone() for l in self.layers],self.active,self.selection,copy.deepcopy(self.guides),copy.deepcopy(self.studio),self.state_id)

    def restore(self,s):
        self.width,self.height,self.title,self.layers,self.active,self.selection,self.guides,self.studio,self.state_id=s
        self._cache=None

    @property
    def saved_revision(self): return self._saved_revision

    @saved_revision.setter
    def saved_revision(self,value):
        self._saved_revision=value
        self.saved_state_id=self.state_id if value==self.revision else None

    @property
    def dirty(self): return self.state_id!=self.saved_state_id

    def info(self):
        box=self.selection.getbbox() if self.selection is not None else None
        return {'id':self.id,'title':self.title,'width':self.width,'height':self.height,'path':self.path,'revision':self.revision,
                'dirty':self.dirty,'activeLayer':self.active,'layers':[l.info() for l in self.layers],
                'selection':list(box) if box else None,'guides':self.guides,'studio':self.studio,
                'undo':[h[0] for h in self.history],'redo':[h[0] for h in self.future]}

    def layer(self,layer_id=None):
        layer_id=layer_id or self.active
        return next((l for l in self.layers if l.id==layer_id),None) or self._missing()

    def _missing(self): raise ValueError('Select an existing layer first')

    def render(self):
        if self._cache is None: self._cache=pixels.render(self)
        return self._cache

    def execute(self,op,args=None,expected_revision=None):
        if expected_revision is not None and expected_revision != self.revision: raise ValueError(f'Document changed: expected revision {expected_revision}, current {self.revision}')
        args=args or {}
        if op in ('undo','redo'):
            source,target=(self.history,self.future) if op=='undo' else (self.future,self.history)
            if not source: return self.info()
            label,state=source.pop(); target.append((label,self.snapshot())); self.restore(state); self.revision+=1; return self.info()
        before=self.snapshot()
        try:
            self._edit(op,args)
            self._validate()
            self._cache=None
            self.render()
        except Exception:
            self.restore(before); raise
        self.history.append((op,before)); self.history=self.history[-60:]; self.future=[]; self.state_id=uid(); self.revision+=1
        return self.info()

    def _validate(self):
        dimensions(self.width,self.height)
        ids={l.id for l in self.layers}
        for l in self.layers:
            if l.blend not in pixels.BLENDS: raise ValueError('Unknown blend mode')
            if not 0 <= l.opacity <= 1: raise ValueError('Opacity must be 0–1')
            if not all(math.isfinite(v) for v in (l.x,l.y,l.sx,l.sy,l.angle)) or l.sx==0 or l.sy==0: raise ValueError('Transform must be finite and nonzero')
            if l.kind in ('shape','gradient'):
                dimensions(l.params.get('width',300),l.params.get('height',200))
            if l.kind not in ('group','adjustment'):
                im=pixels.content(l); dimensions(*im.size)
            seen={l.id}; parent=l.parent
            while parent:
                if parent in seen or parent not in ids: raise ValueError('Invalid layer group hierarchy')
                seen.add(parent); ancestor=self.layer(parent)
                if ancestor.kind != 'group': raise ValueError('Parent must be a group')
                parent=ancestor.parent

    def add(self,layer):
        i=next((i+1 for i,l in enumerate(self.layers) if l.id==self.active),len(self.layers))
        self.layers.insert(i,layer); self.active=layer.id

    def raster(self,l,bake_mask=False):
        if l.locked: raise ValueError('Layer is locked')
        if l.kind in ('group','adjustment'): raise ValueError('Choose a pixel, text, shape or gradient layer')
        # Bake placement for pixel editing. Earlier editable source remains in undo.
        size=(self.width,self.height)
        mapped_mask=None
        if l.mask is not None and not bake_mask:
            mask_layer=l.clone(); mask_layer.kind='raster'; mask_layer.mask=None
            mask_layer.image=Image.new('RGBA',pixels.content(l).size,'white')
            mask_layer.image.putalpha(l.mask.resize(mask_layer.image.size))
            mapped_mask=pixels.placed(mask_layer,size,include_mask=False).getchannel('A')
        l.image=pixels.placed(l,size,include_mask=bake_mask); l.kind='raster'; l.params={}; l.mask=mapped_mask
        l.x=l.y=l.angle=0; l.sx=l.sy=1
        return l.image

    def constrained(self,before,after):
        return Image.composite(after,before,self.selection) if self.selection is not None else after

    def _edit(self,op,a):
        size=(self.width,self.height)
        if op=='add_layer':
            kind=a.get('kind','raster')
            if kind not in ('raster','text','shape','gradient','adjustment','group'): raise ValueError('Unknown layer kind')
            im=Image.new('RGBA',size,a.get('color',(0,0,0,0))) if kind=='raster' else None
            layer=Layer(name=a.get('name',kind.title()),kind=kind,image=im,x=a.get('x',0),y=a.get('y',0),params=copy.deepcopy(a.get('params',{})),parent=a.get('parent'))
            for key in ('visible','locked','opacity','blend','sx','sy','angle','clipping','effects'):
                if key in a: setattr(layer,key,copy.deepcopy(a[key]))
            self.add(layer)
        elif op=='import_image':
            file=Path(a['path']).resolve()
            with Image.open(file) as source: im=ImageOps.exif_transpose(source).convert('RGBA')
            dimensions(*im.size)
            self.add(Layer(name=a.get('name',file.stem),image=im,x=a.get('x',0),y=a.get('y',0),provenance={'source':str(file),**a.get('provenance',{})}))
        elif op=='select_layer': self.active=self.layer(a['layerId']).id
        elif op=='update_layer':
            l=self.layer(a.get('layerId'))
            if l.locked and any(k in a for k in ('x','y','sx','sy','angle','params')): raise ValueError('Layer is locked')
            if l.kind=='group' and any(k in a for k in ('x','y','sx','sy','angle')):
                descendants=set(); pending=[l.id]
                while pending:
                    parent=pending.pop()
                    children=[child for child in self.layers if child.parent==parent]
                    descendants.update(child.id for child in children); pending.extend(child.id for child in children if child.kind=='group')
                sx=a.get('sx',l.sx)/l.sx; sy=a.get('sy',l.sy)/l.sy; angle=a.get('angle',l.angle)-l.angle; radians=math.radians(angle)
                for child in self.layers:
                    if child.id in descendants:
                        x=(child.x-l.x)*sx; y=(child.y-l.y)*sy
                        child.x=a.get('x',l.x)+x*math.cos(radians)-y*math.sin(radians); child.y=a.get('y',l.y)+x*math.sin(radians)+y*math.cos(radians)
                        child.sx*=sx; child.sy*=sy; child.angle+=angle
            allowed={'name','visible','locked','opacity','blend','x','y','sx','sy','angle','parent','clipping','mask_enabled','params','effects'}
            for key,value in a.items():
                if key=='layerId': continue
                if key not in allowed: raise ValueError(f'Unsupported layer property: {key}')
                setattr(l,key,copy.deepcopy(value))
        elif op=='duplicate_layer':
            l=self.layer(a.get('layerId')); new=l.clone(); new.id=uid(); new.name+=' copy'; self.add(new)
            if l.kind=='group':
                mapping={l.id:new.id}
                pending=[c for c in self.layers if c.id!=new.id and c.parent==l.id]
                while pending:
                    c=pending.pop(0); n=c.clone(); n.id=uid(); n.parent=mapping[c.parent]; mapping[c.id]=n.id; self.layers.append(n)
                    pending.extend(ch for ch in self.layers if ch.parent==c.id)
        elif op=='delete_layer':
            target=self.layer(a.get('layerId')).id; removed={target}
            while True:
                more={l.id for l in self.layers if l.parent in removed}-removed
                if not more: break
                removed|=more
            self.layers=[l for l in self.layers if l.id not in removed]; self.active=self.layers[-1].id if self.layers else None
        elif op=='reorder_layer':
            l=self.layer(a.get('layerId')); self.layers.remove(l); self.layers.insert(max(0,min(len(self.layers),int(a['index']))),l)
            if 'parent' in a: l.parent=a['parent']
        elif op=='rasterize': self.raster(self.layer(a.get('layerId')),bake_mask=a.get('applyMask',False))
        elif op in ('merge_down','flatten'):
            if op=='flatten':
                im=self.render().copy(); self.layers=[]; self.add(Layer(name='Merged',image=im))
            else:
                l=self.layer(a.get('layerId')); index=self.layers.index(l)
                if index<1: raise ValueError('There is no layer below')
                below=self.layers[index-1]
                if l.parent != below.parent or l.kind in ('group','adjustment') or below.kind in ('group','adjustment'): raise ValueError('Merge neighboring pixel layers in the same group')
                if below.blend!='normal' or below.clipping or l.clipping: raise ValueError('Flatten the composition to preserve backdrop-dependent blending')
                lower=pixels.blend(Image.new('RGBA',size),pixels.effects(pixels.placed(below,size),below.effects),'normal',below.opacity)
                im=pixels.blend(lower,pixels.effects(pixels.placed(l,size),l.effects),l.blend,l.opacity)
                self.layers[index-1:index+1]=[Layer(name=below.name,image=im,parent=below.parent)]; self.active=self.layers[index-1].id
        elif op=='selection': self._selection(a)
        elif op=='mask':
            l=self.layer(a.get('layerId')); kind=a.get('mode','selection'); mask_size=size if l.kind in ('group','adjustment') else pixels.content(l).size
            if kind=='remove': l.mask=None
            elif kind=='invert': l.mask=ImageOps.invert(l.mask or Image.new('L',mask_size,255))
            elif kind=='blur': l.mask=(l.mask or Image.new('L',mask_size,255)).filter(ImageFilter.GaussianBlur(a.get('radius',5)))
            elif kind in ('white','black'): l.mask=Image.new('L',mask_size,255 if kind=='white' else 0)
            else:
                if self.selection is None: raise ValueError('Make a selection first')
                if l.kind not in ('group','adjustment'): self.raster(l)
                l.mask=self.selection.copy()
        elif op in ('brush','erase','clone','heal','blur_brush'):
            l=self.layer(a.get('layerId')); stroke=self.stroke_mask(a)
            if self.selection is not None: stroke=ImageChops.multiply(stroke,self.selection)
            if a.get('target')=='mask':
                if l.locked: raise ValueError('Layer is locked')
                # Preserve image alpha independently when materializing a transformed mask.
                if l.kind not in ('group','adjustment'):
                    original_mask=l.mask; mask_layer=l.clone(); mask_layer.mask=None
                    if original_mask is not None:
                        mask_rgba=Image.new('RGBA',original_mask.size,'white'); mask_rgba.putalpha(original_mask); mask_layer.kind='raster'; mask_layer.image=mask_rgba
                        mapped_mask=pixels.placed(mask_layer,size,include_mask=False).getchannel('A')
                    else: mapped_mask=Image.new('L',size,255)
                    l.image=pixels.placed(l,size,include_mask=False); l.kind='raster'; l.params={}; l.x=l.y=l.angle=0; l.sx=l.sy=1; l.mask=mapped_mask
                l.mask=Image.composite(Image.new('L',size,a.get('maskValue',255)),l.mask or Image.new('L',size,255),stroke); return
            old=self.raster(l).copy()
            if op=='erase':
                after=old.copy(); after.putalpha(ImageChops.multiply(old.getchannel('A'),ImageOps.invert(stroke)))
            elif op=='brush':
                from PIL import ImageColor
                color=ImageColor.getcolor(a.get('color','#ffffff'),'RGBA'); paint=Image.new('RGBA',size,color)
                paint.putalpha(stroke.point(lambda v:int(v*color[3]/255))); after=Image.alpha_composite(old,paint)
            elif op=='clone':
                source=self.render() if a.get('sampleMerged',True) else old
                dx,dy=a.get('offset',[0,0]); shifted=Image.new('RGBA',size); shifted.paste(source,(int(dx),int(dy)))
                after=Image.composite(shifted,old,stroke)
            elif op=='blur_brush': after=Image.composite(old.filter(ImageFilter.GaussianBlur(a.get('blur',5))),old,stroke)
            else: after=self.inpaint(old,stroke,a.get('radius',5))
            l.image=after
        elif op in ('fill','clear','content_fill','filter'):
            l=self.layer(a.get('layerId')); old=self.raster(l).copy()
            if op=='filter': after=pixels.adjustment(old,a)
            elif op=='content_fill':
                if self.selection is None: raise ValueError('Make a selection first')
                after=self.inpaint(old,self.selection,a.get('radius',5))
            else: after=Image.new('RGBA',size,a.get('color','#ffffff') if op=='fill' else (0,0,0,0))
            l.image=self.constrained(old,after)
        elif op in ('copy_selection','cut_selection'):
            l=self.layer(a.get('layerId')); im=self.render().copy() if a.get('merged') else pixels.placed(l,size)
            if self.selection is not None: im.putalpha(ImageChops.multiply(im.getchannel('A'),self.selection))
            box=im.getbbox()
            if not box: raise ValueError('Selection is empty')
            if op=='cut_selection':
                old=self.raster(l).copy(); old.putalpha(ImageChops.multiply(old.getchannel('A'),ImageOps.invert(self.selection or Image.new('L',size,255)))); l.image=old
            self.add(Layer(name='Selection',image=im.crop(box),x=box[0],y=box[1]))
        elif op=='crop':
            x,y,w,h=[int(a[k]) for k in ('x','y','width','height')]; dimensions(w,h)
            for l in self.layers:
                l.x-=x; l.y-=y
                if l.kind in ('group','adjustment') and l.mask is not None: l.mask=l.mask.crop((x,y,x+w,y+h))
            self.width,self.height=w,h; self.selection=None
        elif op=='canvas_size':
            w,h=dimensions(a['width'],a['height']); dx,dy=(w-self.width)/2,(h-self.height)/2
            if a.get('anchor','center')=='center':
                for l in self.layers: l.x+=dx; l.y+=dy
            else: dx=dy=0
            for l in self.layers:
                if l.kind in ('group','adjustment') and l.mask is not None:
                    mask=Image.new('L',(w,h)); mask.paste(l.mask,(round(dx),round(dy))); l.mask=mask
            self.width,self.height=w,h; self.selection=None
        elif op=='image_size':
            w,h=dimensions(a['width'],a['height']); sx,sy=w/self.width,h/self.height
            for l in self.layers:
                l.x*=sx; l.y*=sy; l.sx*=sx; l.sy*=sy
                if l.kind in ('group','adjustment') and l.mask is not None: l.mask=l.mask.resize((w,h),Image.Resampling.LANCZOS)
            self.width,self.height=w,h; self.selection=None
        elif op=='guides': self.guides=copy.deepcopy(a.get('guides',[]))
        elif op=='rename': self.title=a['title']
        elif op=='link_studio': self.studio=copy.deepcopy(a)
        elif op=='apply_patch':
            if a['sourceRevision'] != self.revision: raise ValueError('Artwork changed after generation; the candidate is preserved. Inspect it and choose where to place it.')
            box=a['box']; im=Image.open(a['path']).convert('RGBA').resize((box['size'],box['size']),Image.Resampling.LANCZOS)
            self.add(Layer(name=a.get('name','Generated refinement'),image=im,x=box['x'],y=box['y'],provenance=a.get('provenance',{})))
        else: raise ValueError(f'Unknown document operation: {op}')

    def _selection(self,a):
        kind=a.get('kind','rectangle'); size=(self.width,self.height); mask=Image.new('L',size)
        if kind=='none': self.selection=None; return
        if kind=='all': mask=Image.new('L',size,255)
        elif kind=='invert': mask=ImageOps.invert(self.selection or mask)
        elif kind in ('expand','contract','feather'):
            if self.selection is None: raise ValueError('Make a selection first')
            n=min(199,max(3,2*int(a.get('radius',3))+1))
            filt=ImageFilter.MaxFilter(n) if kind=='expand' else ImageFilter.MinFilter(n) if kind=='contract' else ImageFilter.GaussianBlur(a.get('radius',3))
            mask=self.selection.filter(filt)
        elif kind=='layer_alpha': mask=pixels.placed(self.layer(a.get('layerId')),size).getchannel('A')
        elif kind=='wand':
            import cv2
            src=np.array(self.render().convert('RGB')); x,y=int(a['x']),int(a['y'])
            if not (0<=x<self.width and 0<=y<self.height): raise ValueError('Pick inside the canvas')
            tolerance=int(a.get('tolerance',32))
            if a.get('contiguous',True):
                flood=np.zeros((self.height+2,self.width+2),np.uint8)
                cv2.floodFill(src,flood,(x,y),(0,0,0),(tolerance,)*3,(tolerance,)*3,cv2.FLOODFILL_MASK_ONLY|cv2.FLOODFILL_FIXED_RANGE|(255<<8)|4)
                mask=Image.fromarray(flood[1:-1,1:-1])
            else: mask=Image.fromarray((np.max(np.abs(src.astype(int)-src[y,x].astype(int)),axis=2)<=tolerance).astype('uint8')*255)
        elif kind=='polygon': ImageDraw.Draw(mask).polygon([tuple(p) for p in a['points']],fill=255)
        else:
            x,y,w,h=[int(a[k]) for k in ('x','y','width','height')]; box=(x,y,x+w-1,y+h-1)
            if w<=0 or h<=0: raise ValueError('Selection needs positive width and height')
            if kind=='rectangle': ImageDraw.Draw(mask).rectangle(box,fill=255)
            elif kind=='ellipse': ImageDraw.Draw(mask).ellipse(box,fill=255)
            else: raise ValueError('Unknown selection kind')
        if a.get('feather',0): mask=mask.filter(ImageFilter.GaussianBlur(a['feather']))
        mode=a.get('mode','replace')
        if self.selection is not None:
            if mode=='add': mask=ImageChops.lighter(mask,self.selection)
            elif mode=='subtract': mask=ImageChops.subtract(self.selection,mask)
            elif mode=='intersect': mask=ImageChops.darker(self.selection,mask)
        self.selection=mask

    def stroke_mask(self,a):
        mask=Image.new('L',(self.width,self.height)); points=a['points']; radius=max(.5,float(a.get('size',32))/2)
        opacity=max(0,min(1,float(a.get('opacity',1)))); hardness=max(0,min(1,float(a.get('hardness',.8))))
        d=ImageDraw.Draw(mask); last=None
        for p in points:
            x,y=p[:2]; pressure=float(p[2]) if len(p)>2 else 1; r=radius*pressure
            if last is not None:
                dist=math.hypot(x-last[0],y-last[1]); steps=max(1,math.ceil(dist/max(1,min(r,last[2])*.3)))
                for t in np.linspace(0,1,steps+1):
                    xx,yy=last[0]+t*(x-last[0]),last[1]+t*(y-last[1]); rr=last[2]+t*(r-last[2]); d.ellipse((xx-rr,yy-rr,xx+rr,yy+rr),fill=255)
            else: d.ellipse((x-r,y-r,x+r,y+r),fill=255)
            last=(x,y,r)
        if hardness<1: mask=mask.filter(ImageFilter.GaussianBlur(radius*(1-hardness)*.45))
        return mask.point(lambda v:round(v*opacity))

    @staticmethod
    def inpaint(im,mask,radius):
        import cv2
        data=cv2.inpaint(np.array(im.convert('RGB')),np.array(mask),float(radius),cv2.INPAINT_TELEA)
        out=Image.fromarray(data).convert('RGBA'); out.putalpha(ImageChops.lighter(im.getchannel('A'),mask)); return out

    def save(self,path,mark_saved=True):
        path=Path(path).resolve(); path.parent.mkdir(parents=True,exist_ok=True)
        if path.suffix.lower() not in ('.compwin','.ora'): raise ValueError('Save layered documents as .compwin or .ora; use Export for flat images')
        temp=path.with_name(path.name+'.'+uid()+'.tmp')
        manifest={'format':'com.compositor.windows','version':1,'id':self.id,'title':self.title,'width':self.width,'height':self.height,'active':self.active,'guides':self.guides,'studio':self.studio,'layers':[]}
        try:
            with zipfile.ZipFile(temp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=2) as archive:
                if path.suffix.lower()=='.ora': archive.writestr('mimetype','image/openraster',compress_type=zipfile.ZIP_STORED)
                def put(name,im):
                    data=io.BytesIO(); im.save(data,format='PNG'); archive.writestr(name,data.getvalue())
                for l in self.layers:
                    record={k:v for k,v in vars(l).items() if k not in ('image','mask')}
                    for key in ('image','mask'):
                        im=getattr(l,key)
                        if im is not None: record[key]=f'layers/{l.id}-{key}.png'; put(record[key],im)
                    manifest['layers'].append(record)
                if self.selection is not None: put('selection.png',self.selection)
                archive.writestr('manifest.json',json.dumps(manifest,ensure_ascii=False))
                put('mergedimage.png',self.render())
                if path.suffix.lower()=='.ora': self._write_ora(archive,put)
            os.replace(temp,path)
        finally:
            if temp.exists(): temp.unlink()
        if mark_saved: self.path=str(path); self.saved_revision=self.revision
        return {'path':str(path),'bytes':path.stat().st_size,'revision':self.revision}

    def _write_ora(self,archive,put):
        import xml.etree.ElementTree as ET
        root=ET.Element('image',{'w':str(self.width),'h':str(self.height),'name':self.title,'version':'0.0.3'})
        stack=ET.SubElement(root,'stack')
        mapping={'normal':'svg:src-over','multiply':'svg:multiply','screen':'svg:screen','overlay':'svg:overlay','darken':'svg:darken','lighten':'svg:lighten','difference':'svg:difference','exclusion':'svg:exclusion','color_dodge':'svg:color-dodge','color_burn':'svg:color-burn','hard_light':'svg:hard-light','soft_light':'svg:soft-light'}
        def write_stack(parent,node):
            for layer in reversed([l for l in self.layers if l.parent==parent]):
                if layer.blend not in mapping: raise ValueError('OpenRaster cannot preserve the '+layer.blend+' blend mode. Save .compwin or flatten a duplicate.')
                attrs={'name':layer.name,'opacity':str(layer.opacity),'visibility':'visible' if layer.visible else 'hidden','composite-op':mapping.get(layer.blend,'svg:src-over')}
                if layer.kind=='group' and layer.mask is None and not layer.effects:
                    child=ET.SubElement(node,'stack',attrs); write_stack(layer.id,child)
                elif layer.kind in ('group','adjustment') or layer.clipping:
                    # ORA cannot represent these semantics portably. The exact merged
                    # fallback accompanies the complete native manifest; tell the caller.
                    raise ValueError('This document uses adjustment layers, masked groups or clipping. Save .compwin to retain all editing, or flatten a duplicate before OpenRaster export.')
                else:
                    image=pixels.effects(pixels.placed(layer,(self.width,self.height)),layer.effects)
                    name=f'data/{layer.id}.png'; put(name,image); attrs.update(src=name,x='0',y='0'); ET.SubElement(node,'layer',attrs)
        write_stack(None,stack)
        archive.writestr('stack.xml',ET.tostring(root,encoding='utf-8'))

    @classmethod
    def load(cls,path):
        path=Path(path).resolve()
        if path.is_dir(): return cls.load_upstream(path)
        if path.suffix.lower()=='.psd': return cls.load_psd(path)
        if path.suffix.lower() not in ('.compwin','.ora'):
            with Image.open(path) as image: w,h=ImageOps.exif_transpose(image).size
            d=cls(w,h,path.stem); d.execute('import_image',{'path':str(path)}); return d
        with zipfile.ZipFile(path) as archive:
            if 'manifest.json' not in archive.namelist(): return cls.load_ora(archive,path)
            m=json.loads(archive.read('manifest.json'))
            if m.get('format')!='com.compositor.windows' or m.get('version')!=1: raise ValueError('Unsupported document format/version')
            d=cls(m['width'],m['height'],m['title']); d.id=m['id']; d.active=m.get('active'); d.guides=m.get('guides',[]); d.studio=m.get('studio',{})
            for r in m['layers']:
                for key in ('image','mask'):
                    if r.get(key): r[key]=Image.open(io.BytesIO(archive.read(r[key]))).convert('L' if key=='mask' else 'RGBA')
                d.layers.append(Layer(**r))
            if 'selection.png' in archive.namelist(): d.selection=Image.open(io.BytesIO(archive.read('selection.png'))).convert('L')
            d._validate(); d.path=str(path); d.saved_revision=0; return d

    @classmethod
    def load_ora(cls,archive,path):
        import xml.etree.ElementTree as ET
        root=ET.fromstring(archive.read('stack.xml')); d=cls(int(root.get('w')),int(root.get('h')),root.get('name',path.stem))
        reverse={'svg:src-over':'normal',**{'svg:'+m.replace('_','-'):m for m in pixels.BLENDS}}
        def read_stack(node,parent=None):
            for child in reversed(list(node)):
                attrs=dict(name=child.get('name','Layer'),opacity=float(child.get('opacity',1)),visible=child.get('visibility')!='hidden',parent=parent,blend=reverse.get(child.get('composite-op'),'normal'))
                if child.tag=='stack':
                    group=Layer(kind='group',**attrs); d.layers.append(group); read_stack(child,group.id)
                elif child.tag=='layer':
                    im=Image.open(io.BytesIO(archive.read(child.get('src')))).convert('RGBA'); d.layers.append(Layer(image=im,x=float(child.get('x',0)),y=float(child.get('y',0)),**attrs))
        read_stack(root.find('stack'))
        d.active=d.layers[-1].id if d.layers else None; return d

    @classmethod
    def load_psd(cls,path):
        from psd_tools import PSDImage
        psd=PSDImage.open(path); d=cls(psd.width,psd.height,path.stem); report=[]
        def walk(items,parent=None):
            for src in items:
                mode=src.blend_mode.value.decode('ascii',errors='replace')
                modes={'norm':'normal','mul ':'multiply','scrn':'screen','over':'overlay','dark':'darken','lite':'lighten','diff':'difference','sLit':'soft_light','hLit':'hard_light','div ':'color_dodge','idiv':'color_burn','smud':'exclusion','lddg':'linear_dodge','lbrn':'linear_burn','vLit':'vivid_light','lLit':'linear_light','pLit':'pin_light','hMix':'hard_mix','fsub':'subtract','fdiv':'divide'}
                if mode not in modes: report.append(f'{src.name}: {mode} blend imported as normal')
                common=dict(name=src.name,opacity=src.opacity/255,visible=src.visible,parent=parent,blend=modes.get(mode,'normal'),clipping=src.clipping,provenance={'source':str(path)})
                if src.is_group():
                    l=Layer(kind='group',**common)
                    if src.has_mask():
                        raw=src.mask.topil(); l.mask=Image.new('L',(d.width,d.height),src.mask.background_color)
                        if raw is not None: l.mask.paste(raw,(src.mask.left,src.mask.top))
                        l.mask_enabled=not src.mask.disabled
                    d.layers.append(l); walk(src,l.id)
                else:
                    # Stored source channels keep hidden pixels and opacity separate.
                    # composite() would bake masks, opacity and clipping a second time.
                    im=src.topil()
                    if im is None: report.append(f'{src.name}: no renderable pixels'); continue
                    if src.kind!='pixel': report.append(f'{src.name}: {src.kind} appearance imported as pixels')
                    l=Layer(image=im.convert('RGBA'),x=src.left,y=src.top,**common)
                    if src.has_mask(): l.mask=src.mask.topil(layer_sized=True); l.mask_enabled=not src.mask.disabled
                    if src.has_effects(): report.append(f'{src.name}: Photoshop effects need manual recreation')
                    if src.has_vector_mask() and not src.has_mask(): report.append(f'{src.name}: vector mask needs manual recreation')
                    d.layers.append(l)
        walk(psd); d.active=d.layers[-1].id if d.layers else None; d.conversion_report=report; return d

    @classmethod
    def load_upstream(cls,path):
        m=json.loads((path/'manifest.json').read_text(encoding='utf-8'))
        if m.get('format')!='com.compositor.project': raise ValueError('Not an upstream Compositor document')
        d=cls(m['width'],m['height'],path.stem); report=[]
        for r in m['layers']:
            if r.get('adjustment'): report.append(f"{r['name']}: upstream adjustment needs manual recreation"); continue
            im=Image.open(path/'images'/r['imageFile']).convert('RGBA') if r.get('imageFile') else None
            t=r['transform']; origin=t.get('origin',[0,0]); wh=t.get('size',list(im.size) if im else [1,1])
            l=Layer(id=r['id'],name=r['name'],kind='group' if r.get('isGroup') else 'raster',image=im,visible=r['isVisible'],opacity=r.get('opacity',1),parent=r.get('parentID'),x=origin[0],y=origin[1],sx=wh[0]/im.width if im else 1,sy=wh[1]/im.height if im else 1,angle=t.get('rotation',0))
            if t.get('flipX'): l.sx*=-1
            if t.get('flipY'): l.sy*=-1
            if r.get('maskFile'): l.mask=Image.open(path/'images'/r['maskFile']).convert('L')
            l.mask_enabled=r.get('maskEnabled',True); d.layers.append(l)
        d.active=m.get('activeLayerID'); d.conversion_report=report; return d

    def export(self,path,quality=95):
        path=Path(path).resolve()
        if self.path and path==Path(self.path): raise ValueError('Export cannot replace the layered document')
        originals={l.provenance.get('source') for l in self.layers}
        if str(path) in originals: raise ValueError('Export to a new path to preserve your imported original')
        if path.suffix.lower() not in ('.png','.jpg','.jpeg','.webp','.tif','.tiff','.bmp'): raise ValueError('Choose PNG, JPEG, WebP, TIFF or BMP')
        im=self.render(); path.parent.mkdir(parents=True,exist_ok=True)
        if path.suffix.lower() in ('.jpg','.jpeg','.bmp'):
            background=Image.new('RGBA',im.size,'white'); im=Image.alpha_composite(background,im).convert('RGB')
        temp=path.with_name(path.stem+'.'+uid()+path.suffix)
        try: im.save(temp,quality=quality); os.replace(temp,path)
        finally:
            if temp.exists(): temp.unlink()
        return {'path':str(path),'bytes':path.stat().st_size,'width':im.width,'height':im.height,'revision':self.revision}
