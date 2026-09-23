"""Inspectably reduce an image to a real pixel grid and a finite palette."""
from PIL import Image, ImageColor, ImageFilter
import numpy as np


def convert(image,args):
    width,height=int(args.get('width',256)),int(args.get('height',256))
    if not 1<=width<=2048 or not 1<=height<=2048: raise ValueError('Choose a pixel canvas between 1 and 2048 pixels per side')
    colors=int(args.get('colors',32))
    if not 2<=colors<=256: raise ValueError('Choose between 2 and 256 colors')
    method=args.get('sampling','nearest')
    methods={'area':Image.Resampling.BOX,'nearest':Image.Resampling.NEAREST}
    if method not in methods: raise ValueError('Choose area averaging or nearest-neighbor sampling')
    smoothing=int(args.get('simplify',0))
    if not 0<=smoothing<=3: raise ValueError('Simplification must be between 0 and 3')
    image=image.convert('RGBA').resize((width,height),methods[method])
    if smoothing: image=image.filter(ImageFilter.MedianFilter(2*smoothing+1))
    alpha=image.getchannel('A').point(lambda v:255 if v>=int(args.get('alphaThreshold',128)) else 0)
    rgb=image.convert('RGB'); visible=np.asarray(alpha)>0
    custom=args.get('palette')
    if custom:
        if not 2<=len(custom)<=256: raise ValueError('A palette needs 2 to 256 colors')
        entries=[ImageColor.getrgb(color) for color in custom]
        palette=Image.new('P',(1,1)); values=[channel for color in entries for channel in color]
        palette.putpalette(values+list(entries[-1])*(256-len(entries)))
    else:
        # Transparent pixels must not consume colors in the artwork's palette.
        samples=np.asarray(rgb)[visible]
        if not len(samples): samples=np.array([[0,0,0]],dtype=np.uint8)
        reduced=Image.fromarray(samples.reshape(1,-1,3)).quantize(colors=colors,method=Image.Quantize.MAXCOVERAGE,kmeans=3)
        table=reduced.getpalette(); entries=[table[index*3:index*3+3] for _,index in reduced.getcolors()]
        palette=Image.new('P',(1,1)); values=[channel for color in entries for channel in color]
        palette.putpalette(values+list(entries[-1])*(256-len(entries)))
    indexed=rgb.quantize(palette=palette,dither=Image.Dither.FLOYDSTEINBERG if args.get('dither',False) else Image.Dither.NONE)
    result=indexed.convert('RGBA'); result.putalpha(alpha)
    used=sorted({tuple(color) for color in np.asarray(result)[visible,:3]})
    return result,{'palette':['#%02x%02x%02x'%color for color in used],'conversion':{**args,'width':width,'height':height},'sampling':'nearest'}


def source(document,args):
    image=document.render()
    if args.get('useSelection'):
        if document.selection is None or not document.selection.getbbox(): raise ValueError('Make a selection first')
        from PIL import ImageChops
        image=image.copy(); image.putalpha(ImageChops.multiply(image.getchannel('A'),document.selection))
        image=image.crop(document.selection.getbbox())
    return image
