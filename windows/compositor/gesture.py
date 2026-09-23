"""Immutable gesture previews using the same pixel operations as committed edits."""
import math
from .document import Document


class EditPreview:
    def __init__(self,document,operation,arguments):
        self.document_id=document.id; self.revision=document.revision; self.layer_id=document.active
        self.operation=operation; self.arguments={**arguments,'layerId':self.layer_id}
        self.source=document.snapshot()

    def render(self,points):
        width,height,_,layers,_,selection,*_=self.source
        args={**self.arguments,'points':points}
        # Pointwise compositing can render just the stroke footprint. Filters and
        # effects may read neighboring/global pixels, so use the full reference
        # renderer for those documents instead of approximating their appearance.
        local=self.operation in ('brush','erase') and not any(l.effects or l.kind=='adjustment' for l in layers)
        box=(0,0,width,height)
        if local:
            radius=float(args.get('size',32))/2
            pressure=max((float(p[2]) if len(p)>2 else 1 for p in points),default=1)
            pad=math.ceil(radius*max(1,pressure)+radius*2+4)
            box=(max(0,math.floor(min(p[0] for p in points)-pad)),max(0,math.floor(min(p[1] for p in points)-pad)),
                 min(width,math.ceil(max(p[0] for p in points)+pad)),min(height,math.ceil(max(p[1] for p in points)+pad)))
            if box[2]<=box[0] or box[3]<=box[1]: return None
        x,y,right,bottom=box
        preview=Document(); preview.restore(self.source); preview.id=self.document_id
        preview.layers=[layer.clone() for layer in preview.layers]
        if local:
            preview.width=right-x; preview.height=bottom-y
            preview.selection=selection.crop(box) if selection is not None else None
            for layer in preview.layers:
                if layer.kind=='group':
                    if layer.mask is not None: layer.mask=layer.mask.resize((width,height)).crop(box)
                    continue
                # Common pixel layers need no full-canvas allocation per frame.
                # Preserve the source coordinate system for transformed content.
                if layer.kind=='raster' and layer.sx==layer.sy==1 and layer.angle==0 and layer.x==int(layer.x) and layer.y==int(layer.y):
                    crop=(x-int(layer.x),y-int(layer.y),right-int(layer.x),bottom-int(layer.y))
                    size=layer.image.size
                    layer.image=layer.image.crop(crop)
                    if layer.mask is not None: layer.mask=layer.mask.resize(size).crop(crop)
                    layer.x=layer.y=0
                else: layer.x-=x; layer.y-=y
            args['points']=[[p[0]-x,p[1]-y,*p[2:]] for p in points]
        preview._edit(self.operation,args)
        return box,preview.render()
