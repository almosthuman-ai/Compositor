from pathlib import Path
import numpy as np
import pytest
from PIL import Image
from compositor.document import Document, Layer
from compositor.pixels import blend, BLENDS

def test_mask_can_restore_hidden_pixels_and_undo():
    d=Document(64,64); d.execute('add_layer',{'color':'red'}); d.execute('mask',{'mode':'black'})
    assert d.render().getpixel((32,32))[3]==0
    d.execute('brush',{'target':'mask','maskValue':255,'points':[[32,32]],'size':20,'hardness':1})
    assert d.render().getpixel((32,32))==(255,0,0,255)
    d.execute('erase',{'target':'mask','maskValue':0,'points':[[32,32]],'size':10,'hardness':1})
    assert d.render().getpixel((32,32))[3]==0
    d.execute('undo'); assert d.render().getpixel((32,32))[3]==255

def test_selection_constrains_paint_and_clear():
    d=Document(32,32); d.execute('add_layer',{'color':'white'})
    d.execute('selection',{'kind':'rectangle','x':8,'y':8,'width':8,'height':8})
    d.execute('brush',{'points':[[0,12],[32,12]],'size':20,'hardness':1,'color':'blue'})
    assert d.render().getpixel((10,12))==(0,0,255,255)
    assert d.render().getpixel((7,12))==(255,255,255,255)
    d.execute('clear'); assert d.render().getpixel((10,12))[3]==0
    assert d.render().getpixel((7,12))[3]==255

def test_painting_pixels_preserves_a_separate_restorable_mask():
    d=Document(32,32); d.execute('add_layer',{'color':'red'})
    d.execute('mask',{'mode':'black'})
    d.execute('brush',{'points':[[16,16]],'size':8,'hardness':1,'color':'blue'})
    assert d.render().getpixel((16,16))[3]==0
    d.execute('mask',{'mode':'remove'})
    assert d.render().getpixel((16,16))==(0,0,255,255)
    assert d.render().getpixel((0,0))==(255,0,0,255)

def test_transforms_preserve_source_pixels(tmp_path):
    path=tmp_path/'original.png'; Image.new('RGBA',(100,100),'red').save(path)
    d=Document(200,200); d.execute('import_image',{'path':str(path)}); d.execute('update_layer',{'sx':.1,'sy':.1}); d.execute('update_layer',{'sx':1,'sy':1,'x':40,'angle':90})
    assert d.layer().image.size==(100,100)
    assert d.render().getpixel((90,50))==(255,0,0,255)
    assert Image.open(path).size==(100,100)
    with pytest.raises(ValueError): d.export(path)

def test_rejected_edit_is_atomic_and_stale_revision_rejected():
    d=Document(16,16); d.execute('add_layer',{'color':'red'}); revision=d.revision
    with pytest.raises(ValueError): d.execute('update_layer',{'opacity':2,'name':'invalid'})
    assert d.layer().name=='Raster'; assert d.revision==revision
    with pytest.raises(ValueError): d.execute('clear',expected_revision=revision-1)
    assert d.render().getpixel((0,0))[3]==255

def test_layered_roundtrip_and_undo(tmp_path):
    d=Document(80,60); d.execute('add_layer',{'color':'#203040'}); d.execute('add_layer',{'kind':'shape','name':'Circle','x':10,'y':4,'params':{'shape':'ellipse','width':30,'height':30,'color':'#ff8800'}})
    d.execute('update_layer',{'opacity':.7,'effects':{'shadow':{'blur':2}}}); before=np.array(d.render())
    path=tmp_path/'work.compwin'; d.save(path); loaded=Document.load(path)
    assert loaded.layer().kind=='shape'; assert loaded.layer().params['shape']=='ellipse'; assert np.array_equal(before,np.array(loaded.render()))
    d.execute('update_layer',{'x':40}); assert not np.array_equal(before,np.array(d.render()))
    d.execute('undo'); assert np.array_equal(before,np.array(d.render()))
    d.execute('redo'); assert d.layer().x==40

def test_nested_groups_and_clipping():
    d=Document(32,32); d.execute('add_layer',{'kind':'group','name':'group'}); group=d.active
    d.execute('add_layer',{'kind':'shape','parent':group,'params':{'width':8,'height':8,'color':'red'}})
    d.execute('add_layer',{'color':'blue','parent':group}); d.execute('update_layer',{'clipping':True}); d.execute('update_layer',{'layerId':group,'opacity':.5})
    assert d.render().getpixel((4,4))==(0,0,255,128); assert d.render().getpixel((10,10))[3]==0
    with pytest.raises(ValueError): d.execute('update_layer',{'layerId':group,'parent':group})

@pytest.mark.parametrize('mode',BLENDS)
def test_blends_do_not_erase_color_on_transparent_backdrop(mode):
    out=blend(Image.new('RGBA',(2,2)),Image.new('RGBA',(2,2),(180,90,60,128)),mode)
    assert out.getpixel((0,0))==(180,90,60,128)

def test_merge_preserves_opacity_and_effects():
    d=Document(32,32); d.execute('add_layer',{'color':'red'}); d.execute('update_layer',{'opacity':.4}); d.execute('add_layer',{'kind':'shape','x':8,'y':8,'params':{'width':8,'height':8,'color':'blue'}})
    d.execute('update_layer',{'opacity':.6,'effects':{'shadow':{'blur':2}}}); before=np.array(d.render()); d.execute('merge_down')
    assert np.array_equal(before,np.array(d.render()))

def test_adjustment_layer_selection_survives_save(tmp_path):
    d=Document(32,32); d.execute('add_layer',{'color':'red'}); d.execute('selection',{'kind':'rectangle','x':0,'y':0,'width':16,'height':32}); d.execute('add_layer',{'kind':'adjustment','params':{'kind':'invert'}}); d.execute('mask',{'mode':'selection'})
    assert d.render().getpixel((3,3))==(0,255,255,255); assert d.render().getpixel((20,3))==(255,0,0,255)
    d.save(tmp_path/'a.compwin'); loaded=Document.load(tmp_path/'a.compwin'); assert loaded.render().tobytes()==d.render().tobytes()
