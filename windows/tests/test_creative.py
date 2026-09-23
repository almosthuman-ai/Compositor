import io,time
from pathlib import Path
import pytest
from PIL import Image
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from compositor.workspace import Workspace
from compositor.settings import Settings


def setup(tmp_path):
    app=QApplication.instance() or QApplication([]); ws=Workspace(Settings(tmp_path/'data'),restore=False)
    def act(operation,**args): return ws.dispatch('production',{'operation':operation,'args':args})
    project=act('new',kind='comic',title='The night courier',pageCount=2,width=96,height=64)
    image=tmp_path/'reference.png'; Image.new('RGBA',(32,24),'#b73c46').save(image)
    return app,ws,act,project,image


def test_project_prompt_cast_reference_order_and_portable_style_snapshot(tmp_path):
    app,ws,act,project,image=setup(tmp_path)
    style=ws.dispatch('save_style',{'name':'Evening ink','prefix':'INK BEFORE','suffix':'INK AFTER','references':[str(image)]})
    act('set_style',styleId=style['id']); act('update',story='A courier loses the moon.',artDirection='Blue nights and amber windows.')
    first=act('add_character',name='Mina',description='Round glasses and a red coat.')['characters'][-1]
    second=act('add_character',name='Bird',description='A tiny blue bird.')['characters'][-1]
    act('add_reference',path=str(image),characterId=first['id']); act('add_reference',path=str(image),characterId=second['id'])
    act('update_page',characterIds=[first['id']],prompt='Mina waits under a streetlight.')
    request=ws.dispatch('preview_generation',{'prompt':'Mina waits under a streetlight.','kind':'patch','box':{'x':8,'y':8,'width':16,'height':16}})
    assert request['prompt'].startswith('INK BEFORE') and '\n\nINK AFTER\n\n' in request['prompt']
    assert 'Image 1 is the source region' in request['prompt'] and 'Image 2: style reference' in request['prompt'] and 'Image 3: character reference — Mina' in request['prompt']
    assert 'Bird' not in request['prompt'] and [c['id'] for c in request['creativeContext']['characters']]==[first['id']]
    assert len(request['references'])==2 and 'courier loses' in request['prompt']
    ws.dispatch('save_style',{**style,'prefix':'CHANGED LATER','references':[]})
    assert ws.dispatch('preview_generation',{'prompt':'New scene'})['prompt'].startswith('INK BEFORE')
    bundle=tmp_path/'courier.compbook'; act('save',path=str(bundle))
    other=Workspace(Settings(tmp_path/'other'),restore=False); loaded=other.dispatch('production',{'operation':'open','args':{'path':str(bundle)}})
    assert loaded['style']['prefix']=='INK BEFORE' and loaded['pages'][0]['characterIds']==[first['id']]
    copy=other.dispatch('preview_generation',{'prompt':'Mina waits under a streetlight.','kind':'patch','box':{'x':8,'y':8,'width':16,'height':16}})
    assert copy['prompt']==request['prompt'] and all(Path(r['path']).is_file() for r in copy['references'])
    assert all(str(tmp_path/'other') in r['path'] for r in copy['references'])
    act('select',pageId=project['pages'][1]['id'])
    empty_cast=ws.dispatch('preview_generation',{'prompt':'The empty street'})
    assert len(empty_cast['references'])==1 and 'Characters in this image:' not in empty_cast['prompt']
    ws.generation.pool.shutdown(); other.generation.pool.shutdown()


def test_character_generation_retains_candidate_until_explicit_acceptance(tmp_path,monkeypatch):
    app,ws,act,project,image=setup(tmp_path); calls=[]
    monkeypatch.setattr(ws.settings,'key',lambda _: 'test-only')
    def provider(config,key,prompt,images,size):
        calls.append((prompt,list(images))); return image.read_bytes(),{}
    ws.generation.provider=provider
    character=act('add_character',name='Mina',description='Round glasses, red coat.')['characters'][-1]
    act('set_style',styleId='clean-line-comic'); document=ws.document(); before=document.render().tobytes(); revision=document.revision
    job=act('generate_character',characterId=character['id'])
    deadline=time.monotonic()+5
    while ws.generation.jobs[job['id']]['status'] in ('queued','running') and time.monotonic()<deadline: app.processEvents(); time.sleep(.01)
    finished=ws.generation.jobs[job['id']]; assert finished['status']=='complete'
    assert ws.document().revision==revision and ws.document().render().tobytes()==before
    assert not ws.projects.get()['references'] and finished['creativeContext']['characterId']==character['id']
    assert 'Round glasses' in calls[0][0] and 'confident ink contours' in calls[0][0]
    act('accept_character_reference',characterId=character['id'],jobId=job['id'])
    ref=ws.projects.get()['references'][0]; assert ref['generationId']==job['id'] and ref['characterId']==character['id']
    assert (ws.projects.folder(ws.projects.get())/ref['file']).read_bytes()==Path(finished['result']).read_bytes()
    with pytest.raises(ValueError,match='already'): act('accept_character_reference',characterId=character['id'],jobId=job['id'])
    act('update_page',characterIds=[character['id']]); act('generate',prompt='Mina opens the door.')
    ws.generation.pool.shutdown(); app.processEvents()
    assert len(calls[-1][1])==1 and 'Mina opens the door.' in calls[-1][0]
    assert ws.document().revision==revision


def test_subscription_preparation_captures_style_and_cast_images_immutably(tmp_path):
    app,ws,act,project,image=setup(tmp_path)
    character=act('add_character',name='Mina',description='Red coat.')['characters'][-1]
    act('add_reference',characterId=character['id'],path=str(image)); act('update_page',characterIds=[character['id']]); act('set_style',styleId='watercolor-ink')
    prepared=ws.dispatch('prepare_generation',{'prompt':'Mina at the harbor','kind':'edit'})
    assert len(prepared['inputs'])==2 and prepared['inputs'][0]==prepared['sourcePath']
    assert 'Image 2: character reference — Mina' in prepared['prompt']
    original=Path(prepared['inputs'][1]).read_bytes()
    Image.new('RGBA',(32,24),'black').save(image)
    act('remove_reference',referenceId=ws.projects.get()['references'][0]['id'])
    assert Path(prepared['inputs'][1]).read_bytes()==original
    standalone=ws.dispatch('new',{'width':16,'height':16})
    fresh=ws.dispatch('prepare_generation',{'prompt':'A lighthouse','kind':'generate','styleId':'cinematic-concept'})
    assert fresh['sourcePath'] is None and fresh['inputs']==[] and 'cinematic concept' in fresh['prompt']
    ws.generation.pool.shutdown()


def test_artist_style_and_comic_cast_controls_use_canonical_workspace(tmp_path):
    from compositor.ui import Editor
    from compositor.creative_ui import StyleDialog,CharacterDialog
    app,ws,act,project,image=setup(tmp_path); window=Editor(ws); window.resize(1280,800); window.show()
    style=StyleDialog(window,ws.projects.get()); style.choice.setCurrentIndex(style.choice.findData('painted-storybook')); style.apply()
    assert ws.projects.get()['style']['id']=='painted-storybook'
    first=act('add_character',name='Mina',description='Red coat.')['characters'][-1]
    second=act('add_character',name='Bird',description='Blue wings.')['characters'][-1]
    cast=CharacterDialog(window,ws.projects.get()); cast.show(); app.processEvents()
    assert cast.current==first['id']
    cast.description.setPlainText('Round glasses and a red coat.'); cast.cast.setCurrentRow(1)
    assert ws.projects.character(ws.projects.get(),first['id'])['description']=='Round glasses and a red coat.'
    assert cast.current==second['id']
    cast.accept(); window.production.cast.item(0).setCheckState(Qt.CheckState.Checked)
    assert ws.projects.page(ws.projects.get())['characterIds']==[first['id']]
    assert 'Mina' in window.gen_context.text()
    window.show_panel(window.production_dock); app.processEvents()
    assert window.height()==800 and window.layer_dock.isVisible()
    window.close(); ws.generation.pool.shutdown()
