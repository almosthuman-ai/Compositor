"""Separate the area an artist edits from the context an image model sees."""
import math
from PIL import Image, ImageDraw
from .pixels import resampling


def prepare_source(document,kind,box,folder,method=None):
    method=method or ('nearest' if document.pixel_art else 'smooth'); sampling=resampling(method)
    if kind not in ('generate','edit','patch'): raise ValueError('Generation kind must be generate, edit or patch')
    if kind=='generate': return {'sourcePath':None,'box':None,'resampling':method}
    image=document.render()
    result={'box':None,'resampling':method}
    if kind=='patch':
        if box is None and document.selection is not None:
            bounds=document.selection.getbbox()
            if bounds: box=dict(x=bounds[0],y=bounds[1],width=bounds[2]-bounds[0],height=bounds[3]-bounds[1])
        if not box: raise ValueError('Select an area to refine')
        x,y=int(box['x']),int(box['y']); w=int(box.get('width',box.get('size',0))); h=int(box.get('height',box.get('size',0)))
        if min(x,y)<0 or min(w,h)<1 or x+w>image.width or y+h>image.height: raise ValueError('Generation region must fit inside the canvas')
        # Keep generous real context around the selection. Canvas edges bound
        # this crop; small documents are enlarged for the model below.
        span=max(1024,2*w,2*h)
        cw,ch=min(image.width,span),min(image.height,span)
        cx=max(0,min(image.width-cw,x+w//2-cw//2)); cy=max(0,min(image.height-ch,y+h//2-ch//2))
        image=image.crop((cx,cy,cx+cw,cy+ch))
        selection=Image.new('L',(document.width,document.height))
        ImageDraw.Draw(selection).rectangle((x,y,x+w-1,y+h-1),fill=255)
        if document.selection is not None:
            from PIL import ImageChops
            selection=ImageChops.multiply(selection,document.selection)
        selection.crop((cx,cy,cx+cw,cy+ch)).save(folder/'selection.png')
        scale=max(1,1024/max(cw,ch))
        sw,sh=round(cw*scale),round(ch*scale)
        ww,wh=math.ceil(sw/64)*64,math.ceil(sh/64)*64
        left,top=(ww-sw)//2,(wh-sh)//2
        # Edge padding preserves aspect ratio; application removes it again.
        import numpy as np
        image=image.resize((sw,sh),sampling)
        image=Image.fromarray(np.pad(np.asarray(image),((top,wh-sh-top),(left,ww-sw-left),(0,0)),mode='edge'))
        area={'x':round((x-cx)*scale)+left,'y':round((y-cy)*scale)+top,'width':round(w*scale),'height':round(h*scale)}
        result.update(box=dict(x=cx,y=cy,width=cw,height=ch),selectionBox=dict(x=x,y=y,width=w,height=h),workingSize=[ww,wh],workingContentBox=[left,top,left+sw,top+sh],editArea=area)
    image.save(folder/'source.png'); result['sourcePath']=str(folder/'source.png')
    return result


def normalize_candidate(image,source):
    image=image.convert('RGBA')
    if source.get('workingSize'):
        image=image.resize(tuple(source['workingSize']),resampling(source.get('resampling','smooth')))
    return image


def region_instruction(source):
    if not source.get('editArea'): return ''
    area=source['editArea']; width,height=source['workingSize']
    return (f"Edit the selected area in Image 1: x={area['x']}, y={area['y']}, width={area['width']}, height={area['height']} pixels, measured from the top left of the {width} by {height} working image. "
            f'The surrounding image provides context. Keep the framing and return the complete {width} by {height} image with the change in that area. Both output dimensions must be multiples of 64. Compositor will apply the selection mask to the result.')
