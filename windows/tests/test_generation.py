import io, threading, time
from pathlib import Path
import pytest
from PIL import Image
from compositor.document import Document
from compositor.generation import Generation, generate_provider
from compositor.settings import Settings

def test_crop_only_candidate_stale_rejection_and_retained_source(tmp_path):
    settings=Settings(tmp_path); settings.key=lambda _: 'test-only'; finished=threading.Event(); received=[]; calls=[]
    def provider(config,key,prompt,images,size):
        calls.append(images)
        assert Image.open(images[0]).size==(16,16)
        image=Image.new('RGBA',(24,24),'blue'); buf=io.BytesIO(); image.save(buf,'PNG'); return buf.getvalue(),{'test':True}
    def done(job):
        received.append(job)
        if job['status'] in ('complete','failed'): finished.set()
    engine=Generation(settings,done,provider); d=Document(64,64); d.execute('add_layer',{'color':'red'})
    job=engine.submit(d,{'prompt':'a blue square','kind':'patch','box':{'x':16,'y':16,'size':16}})
    assert finished.wait(3); engine.receive(received[-1]); assert Path(calls[0][0]).is_file()
    assert d.render().getpixel((20,20))==(255,0,0,255)
    engine.apply(d,job['id']); assert d.render().getpixel((20,20))==(0,0,255,255); assert d.render().getpixel((10,10))==(255,0,0,255)
    d.execute('undo'); assert d.render().getpixel((20,20))==(255,0,0,255)
    # Native output remains intact even though application resized a copy.
    assert Image.open(received[-1]['result']).size==(24,24)
    engine.pool.shutdown()

def test_late_result_cannot_overwrite_newer_art(tmp_path):
    settings=Settings(tmp_path); settings.key=lambda _: 'test-only'; done=threading.Event(); received=[]
    def provider(*_):
        b=io.BytesIO(); Image.new('RGBA',(16,16),'blue').save(b,'PNG'); return b.getvalue(),None
    def receive(job):
        received.append(job)
        if job['status'] in ('complete','failed'): done.set()
    engine=Generation(settings,receive,provider); d=Document(32,32); d.execute('add_layer',{'color':'red'})
    job=engine.submit(d,{'prompt':'blue','kind':'edit'}); assert done.wait(3); engine.receive(received[-1]); d.execute('rename',{'title':'A human changed this'})
    with pytest.raises(ValueError,match='changed'): engine.apply(d,job['id'])
    assert Path(received[-1]['result']).exists(); assert len(d.layers)==1; engine.pool.shutdown()

def test_restart_marks_interrupted_job_honestly(tmp_path):
    from compositor.settings import atomic_json
    s=Settings(tmp_path); atomic_json(tmp_path/'generations/old/job.json',{'id':'old','status':'running'})
    g=Generation(s,lambda _:None); assert g.jobs['old']['status']=='failed'; assert 'retry' in g.jobs['old']['error']; g.pool.shutdown()
