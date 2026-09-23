import io, json, zipfile
from pathlib import Path
from types import SimpleNamespace
import numpy as np
from PIL import Image
from PySide6.QtWidgets import QApplication
from compositor.document import Document
from compositor.settings import Settings
from compositor.workspace import Workspace
from compositor.chat import ChatSession


def test_openraster_standard_layers_survive_without_native_manifest(tmp_path):
    d=Document(32,24)
    d.execute('add_layer',{'color':'white'})
    d.execute('add_layer',{'kind':'group','name':'Group'})
    group=d.active
    d.execute('add_layer',{'kind':'shape','parent':group,'x':7,'y':5,'params':{'width':8,'height':9,'color':'red'}})
    d.execute('update_layer',{'opacity':.5,'blend':'multiply'})
    original=tmp_path/'native.ora'; d.save(original)
    portable=tmp_path/'portable.ora'
    with zipfile.ZipFile(original) as source,zipfile.ZipFile(portable,'w') as target:
        for name in source.namelist():
            if name!='manifest.json': target.writestr(name,source.read(name))
    loaded=Document.load(portable)
    assert len(loaded.layers)==3
    assert loaded.layers[1].kind=='group'
    assert np.array_equal(d.render(),loaded.render())


def test_native_subscription_candidate_uses_prepared_crop_and_preserves_original(tmp_path):
    app=QApplication.instance() or QApplication([])
    ws=Workspace(Settings(tmp_path),restore=False)
    ws.dispatch('new',{'width':32,'height':32,'background':'red'})
    prepared=ws.dispatch('prepare_generation',{'kind':'patch','box':{'x':8,'y':8,'width':16,'height':16}})
    native=tmp_path/'native.png'; Image.new('RGBA',(24,24),'blue').save(native)
    messages=[]
    session=SimpleNamespace(ws=ws,native_sources={'item-1':prepared},active_document=ws.active,
                            source_revision=ws.document().revision,model='test',display=SimpleNamespace(emit=messages.append))
    ChatSession.native_image(session,{'id':'item-1','savedPath':str(native),'revisedPrompt':'Blue patch'})
    job=next(iter(ws.generation.jobs.values()))
    assert job['status']=='complete' and job['actualSize']==[24,24]
    assert ws.document().render().getpixel((10,10))==(255,0,0,255)
    ws.dispatch('apply_generation',{'jobId':job['id']})
    assert ws.document().render().getpixel((10,10))==(0,0,255,255)
    assert ws.document().render().getpixel((2,2))==(255,0,0,255)
    assert (Path(job['result']).parent/'provider-original').read_bytes()==native.read_bytes()
    assert Image.open(job['result']).size==tuple(prepared['workingSize'])
    ws.generation.pool.shutdown()


def test_login_waits_for_account_discovery():
    events=[]
    session=SimpleNamespace(account=None,after_ready=[lambda:events.append('deferred')],
                            ready=SimpleNamespace(emit=lambda:events.append('ready')),account_changed=SimpleNamespace(emit=lambda:None),
                            status=SimpleNamespace(emit=lambda text:events.append(text)))
    ChatSession.account_response(session,{'account':{'planType':'plus'}})
    assert session.account['planType']=='plus'
    assert events[-2:]==['ready','deferred'] and session.after_ready==[]


def test_psd_hidden_pixels_and_layer_opacity_stay_editable(tmp_path):
    from psd_tools import PSDImage
    psd=PSDImage.new('RGB',(16,16))
    red=psd.create_pixel_layer(Image.new('RGBA',(16,16),'red'),name='Red')
    red.opacity=128
    hidden=psd.create_pixel_layer(Image.new('RGBA',(16,16),'blue'),name='Hidden blue')
    hidden.visible=False
    path=tmp_path/'source.psd'; psd.save(path)
    loaded=Document.load(path)
    assert len(loaded.layers)==2
    assert loaded.layers[1].visible is False
    assert loaded.layers[1].image.getpixel((4,4))==(0,0,255,255)
    assert loaded.render().getpixel((4,4))==(255,0,0,128)
    loaded.execute('update_layer',{'layerId':loaded.layers[1].id,'visible':True})
    assert loaded.render().getpixel((4,4))==(0,0,255,255)
