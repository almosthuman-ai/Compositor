import pytest
from PIL import Image, ImageChops
from compositor.document import Document
from compositor.gesture import EditPreview


@pytest.mark.parametrize('operation',['brush','erase'])
@pytest.mark.parametrize('variant',['plain','mask','selection','transform','group','blend','effect','adjustment'])
def test_preview_pixels_equal_the_committed_edit_without_mutating_source(operation,variant):
    d=Document(420,300); d.execute('add_layer',{'color':'#eeddcc'})
    if variant=='group':
        d.execute('add_layer',{'kind':'group'}); group=d.active
    else: group=None
    d.execute('add_layer',{'color':'#3e7189','parent':group})
    if variant=='mask':
        d.execute('mask',{'mode':'black'})
    if variant=='selection': d.execute('selection',{'kind':'ellipse','x':80,'y':90,'width':90,'height':80}); d.execute('selection',{'kind':'feather','radius':5})
    if variant=='transform': d.execute('update_layer',{'x':28,'y':-9,'sx':.8,'sy':-.9,'angle':27})
    if variant=='blend': d.execute('update_layer',{'blend':'multiply','opacity':.63})
    if variant=='effect': d.execute('update_layer',{'effects':{'shadow':{'blur':5,'x':7,'y':3}}})
    target=d.active
    if variant=='adjustment': d.execute('add_layer',{'kind':'adjustment','params':{'kind':'auto_levels'}}); d.active=target
    args={'size':27,'hardness':.23,'opacity':.61,'color':'#ef881f'}
    if variant=='mask': args.update(target='mask',maskValue=255 if operation=='brush' else 0)
    points=[[100,110,.4],[150,132,.8],[190,155,.5]]
    source=d.render().tobytes(); revision=d.revision; history=len(d.history)
    preview=EditPreview(d,operation,args)
    preview.render(points[:1]); preview.render(points[:2])
    box,image=preview.render(points)
    assert d.render().tobytes()==source and d.revision==revision and len(d.history)==history
    d.execute(operation,{**args,'points':points})
    assert image.tobytes()==d.render().crop(box).tobytes()
    # Everything outside the temporary patch must still be the original image.
    combined=Image.frombytes('RGBA',(420,300),source); combined.paste(image,box[:2])
    assert combined.tobytes()==d.render().tobytes()


def test_preview_at_canvas_edge_and_outside():
    d=Document(500,300); d.execute('add_layer',{'color':'white'})
    args={'size':37,'hardness':.1,'color':'red'}
    preview=EditPreview(d,'brush',args); points=[[-5,0],[30,10]]
    box,image=preview.render(points); d.execute('brush',{**args,'points':points})
    assert image.tobytes()==d.render().crop(box).tobytes()
    assert preview.render([[-500,-500]]) is None


def test_pressure_tapers_between_samples_and_group_mask_paints_at_canvas_size():
    d=Document(160,100); d.execute('add_layer',{'color':'white'})
    d.execute('brush',{'size':24,'hardness':1,'color':'red','points':[[20,50,.1],[120,50,1]]})
    assert d.render().getpixel((30,58))==(255,255,255,255)
    assert d.render().getpixel((112,58))==(255,0,0,255)
    d.execute('add_layer',{'kind':'group'}); group=d.active
    d.execute('add_layer',{'color':'blue','parent':group}); d.active=group
    d.execute('mask',{'mode':'black'}); assert d.layer().mask.size==(160,100)
    args={'target':'mask','maskValue':255,'size':20,'hardness':1}; points=[[80,50]]
    preview=EditPreview(d,'brush',args); box,image=preview.render(points)
    d.execute('brush',{**args,'points':points})
    assert image.tobytes()==d.render().crop(box).tobytes()
    assert d.render().getpixel((80,50))==(0,0,255,255)
