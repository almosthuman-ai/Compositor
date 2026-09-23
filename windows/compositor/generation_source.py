"""Separate the area an artist edits from the context an image model sees."""
import math, re
from PIL import Image, ImageDraw, ImageOps
from .pixels import resampling


def requested_dimensions(size,document):
    if not size or str(size).lower() in ('canvas','match canvas'): return document.width,document.height
    match=re.fullmatch(r'\s*(\d+)\s*[xX×]\s*(\d+)\s*',str(size))
    if not match: raise ValueError('Choose Match canvas or enter a size such as 1024x1024')
    from .document import dimensions
    return dimensions(*map(int,match.groups()))


def provider_sizes(config):
    """Legacy GPT Image endpoints accept presets rather than arbitrary dimensions."""
    model=config.get('model','')
    if config.get('provider')=='openai' and (model in ('gpt-image-1','gpt-image-1-mini','gpt-image-1.5') or model.startswith(('gpt-image-1-','gpt-image-1.5-'))):
        return [(1024,1024),(1536,1024),(1024,1536)]
    return None


def working_geometry(width,height,long_edge=1024,integer_scale=False,allowed_sizes=None):
    scale=max(1,max(1024,long_edge)/max(width,height))
    if integer_scale: scale=math.ceil(scale)
    if allowed_sizes:
        # Choose the least unused area, then fit without distorting the artwork.
        ww,wh=min(allowed_sizes,key=lambda s:abs(math.log((s[0]/s[1])/(width/height))))
        scale=min(ww/width,wh/height)
        if integer_scale:
            scale=math.floor(scale)
            if scale<1: raise ValueError('This image model cannot fit the pixel canvas without losing pixels. Select a smaller region or choose an image model with custom output sizes.')
        sw,sh=max(1,round(width*scale)),max(1,round(height*scale))
        left,top=(ww-sw)//2,(wh-sh)//2
        return scale,[ww,wh],[left,top,left+sw,top+sh]
    sw,sh=round(width*scale),round(height*scale)
    ww,wh=math.ceil(sw/64)*64,math.ceil(sh/64)*64
    from .document import dimensions
    dimensions(ww,wh)
    left,top=(ww-sw)//2,(wh-sh)//2
    return scale,[ww,wh],[left,top,left+sw,top+sh]


def prepare_source(document,kind,box,folder,method=None,size=None,allowed_sizes=None):
    method=method or ('nearest' if document.pixel_art else 'smooth'); sampling=resampling(method)
    if kind not in ('generate','edit','patch'): raise ValueError('Generation kind must be generate, edit or patch')
    requested=requested_dimensions(size,document)
    long_edge=max(requested) if size and str(size).lower() not in ('canvas','match canvas') else 1024
    result={'box':None,'resampling':method,'sourcePath':None}
    if kind=='generate':
        fit_canvas=bool(document.pixel_art) or not size or str(size).lower() in ('canvas','match canvas')
        width,height=(document.width,document.height) if fit_canvas else requested
        scale,working,content=working_geometry(width,height,long_edge,bool(document.pixel_art),allowed_sizes)
        result.update(workingSize=working)
        if fit_canvas or allowed_sizes:
            result.update(box=dict(x=0,y=0,width=width,height=height),workingContentBox=content)
            if document.pixel_art: result.update(logicalSize=[width,height],pixelScale=scale)
        return result
    image=document.render(); cx=cy=0; cw,ch=image.size
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
    scale,working,content=working_geometry(cw,ch,long_edge,bool(document.pixel_art),allowed_sizes)
    ww,wh=working; left,top,right,bottom=content; sw,sh=right-left,bottom-top
    # Source proportions and integer pixel cells survive the working enlargement;
    # only padding supplies the remaining multiples of 64.
    import numpy as np
    image=image.resize((sw,sh),sampling)
    image=Image.fromarray(np.pad(np.asarray(image),((top,wh-bottom),(left,ww-right),(0,0)),mode='edge'))
    result.update(box=dict(x=cx,y=cy,width=cw,height=ch),workingSize=working,workingContentBox=content)
    if document.pixel_art: result.update(logicalSize=[cw,ch],pixelScale=scale)
    if kind=='patch':
        area={'x':round((x-cx)*scale)+left,'y':round((y-cy)*scale)+top,'width':round(w*scale),'height':round(h*scale)}
        result.update(selectionBox=dict(x=x,y=y,width=w,height=h),editArea=area)
    image.save(folder/'source.png'); result['sourcePath']=str(folder/'source.png')
    return result


def normalize_candidate(image,source):
    image=image.convert('RGBA')
    if source.get('workingSize'):
        image=ImageOps.fit(image,tuple(source['workingSize']),method=resampling(source.get('resampling','smooth')))
    return image


def region_instruction(source):
    width,height=source['workingSize']; area=source.get('editArea')
    if area:
        direction=(f"Edit the selected area in Image 1: x={area['x']}, y={area['y']}, width={area['width']}, height={area['height']} pixels, measured from the top left. "
                   'The surrounding image provides context. Keep its framing. Compositor will apply the saved selection mask to the result. ')
    elif source.get('sourcePath'): direction='Edit the complete composition in Image 1, preserving its framing. '
    else: direction='Create the complete composition. '
    direction+=f'Return the complete {width} by {height} working image. Both output dimensions are multiples of 64.'
    content=source.get('workingContentBox')
    if content and content!=[0,0,width,height]:
        left,top,right,bottom=content
        direction+=f' The artwork occupies x={left}, y={top}, width={right-left}, height={bottom-top}; the outer padding will be removed during placement.'
    if source.get('logicalSize'):
        lw,lh=source['logicalSize']; scale=source['pixelScale']
        direction+=f' This is pixel art on a {lw} by {lh} logical grid, enlarged {scale:g} times. Keep logical pixels as solid {scale:g} by {scale:g} squares with hard edges.'
    return direction
