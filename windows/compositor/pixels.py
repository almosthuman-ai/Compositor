"""RGBA compositing in sRGB, mirroring upstream SeparableBlend's color contract."""
import math
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont, ImageOps

BLENDS = ['normal', 'multiply', 'screen', 'overlay', 'soft_light', 'hard_light',
          'darken', 'lighten', 'color_dodge', 'color_burn', 'linear_dodge',
          'linear_burn', 'difference', 'exclusion', 'subtract', 'divide',
          'vivid_light', 'linear_light', 'pin_light', 'hard_mix']

def blend(back, front, mode='normal', opacity=1):
    # Separable blend arithmetic has no neighborhood dependency. Bound temporary
    # float arrays by processing strips while retaining exact compositing math.
    if mode!='normal' and back.width*back.height>1_048_576:
        output=Image.new('RGBA',back.size); rows=max(1,1_048_576//back.width)
        for y in range(0,back.height,rows):
            box=(0,y,back.width,min(back.height,y+rows))
            output.paste(blend(back.crop(box),front.crop(box),mode,opacity),(0,y))
        return output
    if opacity != 1:
        front = front.copy()
        front.putalpha(front.getchannel('A').point(lambda x: round(x * opacity)))
    if mode == 'normal':
        return Image.alpha_composite(back, front)
    b = np.asarray(back, dtype=np.float32) / 255
    s = np.asarray(front, dtype=np.float32) / 255
    cb, cs, ab, a = b[..., :3], s[..., :3], b[..., 3:], s[..., 3:]
    dodge = lambda x, y: np.where(y >= 1, 1, np.minimum(1, x / np.maximum(1-y, 1e-7)))
    burn = lambda x, y: np.where(y <= 0, 0, 1-np.minimum(1, (1-x)/np.maximum(y, 1e-7)))
    vivid = lambda: np.where(cs <= .5, burn(cb, 2*cs), dodge(cb, 2*cs-1))
    if mode == 'multiply': c = cb*cs
    elif mode == 'screen': c = 1-(1-cb)*(1-cs)
    elif mode == 'overlay': c = np.where(cb <= .5, 2*cb*cs, 1-2*(1-cb)*(1-cs))
    elif mode == 'hard_light': c = np.where(cs <= .5, 2*cb*cs, 1-2*(1-cb)*(1-cs))
    elif mode == 'soft_light':
        d = np.where(cb <= .25, ((16*cb-12)*cb+4)*cb, np.sqrt(cb))
        c = np.where(cs <= .5, cb-(1-2*cs)*cb*(1-cb), cb+(2*cs-1)*(d-cb))
    elif mode == 'darken': c = np.minimum(cb, cs)
    elif mode == 'lighten': c = np.maximum(cb, cs)
    elif mode == 'color_dodge': c = dodge(cb, cs)
    elif mode == 'color_burn': c = burn(cb, cs)
    elif mode == 'linear_dodge': c = np.minimum(1, cb+cs)
    elif mode == 'linear_burn': c = np.maximum(0, cb+cs-1)
    elif mode == 'difference': c = np.abs(cb-cs)
    elif mode == 'exclusion': c = cb+cs-2*cb*cs
    elif mode == 'subtract': c = np.maximum(0, cb-cs)
    elif mode == 'divide': c = np.minimum(1, cb / np.maximum(cs, 1e-7))
    elif mode == 'vivid_light': c = vivid()
    elif mode == 'linear_light': c = np.clip(cb+2*cs-1, 0, 1)
    elif mode == 'pin_light': c = np.where(cs <= .5, np.minimum(cb, 2*cs), np.maximum(cb, 2*cs-1))
    elif mode == 'hard_mix': c = (vivid() >= .5).astype(np.float32)
    else: raise ValueError(f'Unknown blend mode: {mode}')
    out_a = a+ab*(1-a)
    rgb = ((1-a)*ab*cb+(1-ab)*a*cs+ab*a*c)/np.maximum(out_a, 1e-7)
    return Image.fromarray(np.clip(np.concatenate([rgb, out_a], axis=2)*255+.5, 0, 255).astype('uint8'))

def font(size, name='C:/Windows/Fonts/arial.ttf', index=0, family=None, style='Regular'):
    if family:
        from .fonts import resolve
        face=resolve(family,style)
        if face: name,index=face['path'],face['index']
    try: return ImageFont.truetype(name, max(1, int(size)),index=int(index))
    except OSError: return ImageFont.truetype('C:/Windows/Fonts/arial.ttf', max(1, int(size)))

def content(layer):
    if layer.kind == 'text':
        p = layer.params
        f = font(p.get('size', 48), p.get('font', 'C:/Windows/Fonts/arial.ttf'),p.get('fontIndex',0),p.get('fontFamily'),p.get('fontStyle','Regular'))
        text = p.get('text', '') or ' '
        spacing = p.get('spacing', 8)
        box = ImageDraw.Draw(Image.new('RGBA',(1,1))).multiline_textbbox((0,0), text, font=f, spacing=spacing)
        im = Image.new('RGBA', (max(1,box[2]-box[0]+4), max(1,box[3]-box[1]+4)))
        ImageDraw.Draw(im).multiline_text((2-box[0], 2-box[1]), text, font=f, fill=p.get('color','#ffffff'), spacing=spacing, align=p.get('align','left'))
        return im
    if layer.kind == 'shape':
        p = layer.params
        im = Image.new('RGBA', (int(p.get('width', 300)), int(p.get('height',200))))
        d = ImageDraw.Draw(im); sw = int(p.get('strokeWidth', 2)); inset = sw//2
        box = (inset,inset,im.width-1-inset,im.height-1-inset)
        kw = dict(fill=p.get('color','#ffffff'), outline=p.get('stroke'), width=max(1,sw))
        if p.get('shape') == 'ellipse': d.ellipse(box, **kw)
        elif p.get('shape') == 'line': d.line(box, fill=p.get('color','#ffffff'),width=max(1,sw))
        elif p.get('shape') == 'rounded': d.rounded_rectangle(box, radius=p.get('radius',24), **kw)
        else: d.rectangle(box, **kw)
        return im
    if layer.kind == 'gradient':
        from PIL import ImageColor
        p=layer.params; w,h=int(p.get('width',512)),int(p.get('height',512))
        yy,xx=np.mgrid[:h,:w]; start=p.get('start',[0,0]); end=p.get('end',[w,h]); dx,dy=end[0]-start[0],end[1]-start[1]
        if p.get('radial'): t=np.sqrt((xx-start[0])**2+(yy-start[1])**2)/max(1,math.hypot(dx,dy))
        else: t=((xx-start[0])*dx+(yy-start[1])*dy)/max(1,dx*dx+dy*dy)
        t=np.clip(t,0,1)[...,None]
        a=np.array(ImageColor.getcolor(p.get('color','#000000'),'RGBA')); b=np.array(ImageColor.getcolor(p.get('endColor','#ffffff'),'RGBA'))
        return Image.fromarray((a*(1-t)+b*t).astype('uint8'))
    return layer.image if layer.image is not None else Image.new('RGBA',(1,1))

def placed(layer, size, include_mask=True):
    im=content(layer)
    if include_mask and layer.mask is not None and layer.mask_enabled:
        im=im.copy(); im.putalpha(ImageChops.multiply(im.getchannel('A'),layer.mask.resize(im.size)))
    w,h=max(1,round(im.width*abs(layer.sx))),max(1,round(im.height*abs(layer.sy)))
    if w*h > 100_000_000: raise ValueError('Transformed layer exceeds 100 megapixels')
    if im.size != (w,h): im=im.resize((w,h),Image.Resampling.LANCZOS)
    if layer.sx < 0: im=ImageOps.mirror(im)
    if layer.sy < 0: im=ImageOps.flip(im)
    if layer.angle: im=im.rotate(-layer.angle,Image.Resampling.BICUBIC,expand=True)
    result=Image.new('RGBA',size)
    result.alpha_composite(im,(round(layer.x+(w-im.width)/2),round(layer.y+(h-im.height)/2)))
    return result

def effects(im, params):
    if not params: return im
    alpha=im.getchannel('A'); result=Image.new('RGBA',im.size)
    if params.get('shadow'):
        p=params['shadow']; a=alpha.filter(ImageFilter.GaussianBlur(p.get('blur',12)))
        shadow=Image.new('RGBA',im.size,p.get('color','#000000')); shadow.putalpha(a.point(lambda v:int(v*p.get('opacity',.6))))
        result.alpha_composite(shadow,(int(p.get('x',8)),int(p.get('y',8))))
    if params.get('glow'):
        p=params['glow']; a=alpha.filter(ImageFilter.GaussianBlur(p.get('radius',10)))
        glow=Image.new('RGBA',im.size,p.get('color','#ffffff')); glow.putalpha(a); result=Image.alpha_composite(result,glow)
    if params.get('stroke'):
        p=params['stroke']; n=min(199,max(3,2*int(p.get('width',2))+1))
        outline=Image.new('RGBA',im.size,p.get('color','#ffffff')); outline.putalpha(alpha.filter(ImageFilter.MaxFilter(n)))
        result=Image.alpha_composite(result,outline)
    if params.get('overlay'):
        p=params['overlay']; over=Image.new('RGBA',im.size,p.get('color','#ffffff')); over.putalpha(alpha)
        im=Image.blend(im,over,p.get('opacity',1))
    return Image.alpha_composite(result,im)

def adjustment(im, p):
    import cv2
    kind=p.get('kind','exposure'); alpha=im.getchannel('A')
    a=np.asarray(im.convert('RGB'),dtype=np.float32)/255
    if kind == 'invert': a=1-a
    elif kind == 'exposure': a=a*2**float(p.get('value',0))+float(p.get('offset',0))
    elif kind in ('brightness','contrast'):
        a=a+float(p.get('value',0)) if kind=='brightness' else (a-.5)*float(p.get('value',1))+.5
    elif kind in ('hue_saturation','saturation'):
        hsv=cv2.cvtColor(a,cv2.COLOR_RGB2HSV); hsv[...,0]=(hsv[...,0]+float(p.get('hue',0)))%360
        hsv[...,1]=np.clip(hsv[...,1]*float(p.get('saturation',1)),0,1); hsv[...,2]*=float(p.get('value',1)); a=cv2.cvtColor(hsv,cv2.COLOR_HSV2RGB)
    elif kind == 'levels':
        low,high=float(p.get('black',0)),float(p.get('white',1)); gamma=float(p.get('gamma',1))
        if high <= low or gamma <= 0: raise ValueError('Levels need white > black and positive gamma')
        a=np.clip((a-low)/(high-low),0,1)**(1/gamma)
    elif kind == 'curves':
        points=sorted(p.get('points',[[0,0],[1,1]])); a=np.interp(a,[q[0] for q in points],[q[1] for q in points])
    elif kind == 'gradient_map':
        from PIL import ImageColor
        gray=(a@np.array([.2126,.7152,.0722]))[...,None]
        lo=np.array(ImageColor.getrgb(p.get('color','#000000')))/255; hi=np.array(ImageColor.getrgb(p.get('endColor','#ffffff')))/255; a=lo*(1-gray)+hi*gray
    elif kind in ('noise','grain'):
        a=a+np.random.default_rng(p.get('seed',0)).normal(0,float(p.get('amount',.05)),a.shape[:2]+(1,))
    elif kind in ('gaussian_blur','blur'):
        return im.filter(ImageFilter.GaussianBlur(float(p.get('radius',3))))
    elif kind == 'sharpen': return im.filter(ImageFilter.UnsharpMask(radius=float(p.get('radius',2)),percent=int(p.get('percent',150)),threshold=3))
    elif kind == 'motion_blur':
        n=max(1,min(301,int(p.get('radius',15)))); kernel=np.zeros((n,n),np.float32); kernel[n//2,:]=1/n
        matrix=cv2.getRotationMatrix2D((n/2,n/2),float(p.get('angle',0)),1); kernel=cv2.warpAffine(kernel,matrix,(n,n)); kernel/=max(1e-7,kernel.sum()); a=cv2.filter2D(a,-1,kernel)
    elif kind == 'grayscale': a=np.repeat((a@np.array([.2126,.7152,.0722]))[...,None],3,axis=2)
    elif kind == 'auto_levels':
        lo=np.percentile(a,.5,axis=(0,1)); hi=np.percentile(a,99.5,axis=(0,1)); a=(a-lo)/np.maximum(hi-lo,1/255)
    else: raise ValueError(f'Unknown adjustment: {kind}')
    result=Image.fromarray(np.clip(a*255+.5,0,255).astype('uint8')).convert('RGBA'); result.putalpha(alpha); return result

def render(document):
    size=(document.width,document.height)
    def stack(parent):
        out=Image.new('RGBA',size); clip=None
        for layer in document.layers:
            if layer.parent != parent or not layer.visible: continue
            if layer.kind == 'adjustment':
                changed=adjustment(out,layer.params)
                mask=layer.mask.resize(size) if layer.mask is not None and layer.mask_enabled else Image.new('L',size,255)
                out=Image.composite(changed,out,mask.point(lambda v:int(v*layer.opacity))); continue
            if layer.kind == 'group':
                im=stack(layer.id)
                if layer.mask is not None and layer.mask_enabled:
                    im.putalpha(ImageChops.multiply(im.getchannel('A'),layer.mask.resize(size)))
            else: im=placed(layer,size)
            if layer.clipping and clip is not None:
                im.putalpha(ImageChops.multiply(im.getchannel('A'),clip))
            elif not layer.clipping: clip=im.getchannel('A')
            im=effects(im,layer.effects)
            out=blend(out,im,layer.blend,layer.opacity)
        return out
    return stack(None)
