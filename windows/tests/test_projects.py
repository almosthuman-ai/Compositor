import base64, io, json, zipfile
from pathlib import Path
from PIL import Image
from PySide6.QtWidgets import QApplication
from compositor.settings import Settings
from compositor.workspace import Workspace


def workspace(path):
    app=QApplication.instance() or QApplication([])
    from PySide6.QtGui import QFontDatabase
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/georgia.ttf')
    return app,Workspace(Settings(path),restore=False)


def test_portable_book_retains_layers_prose_references_and_live_edits(tmp_path):
    app,ws=workspace(tmp_path/'first')
    def act(operation,**args): return ws.dispatch('production',{'operation':operation,'args':args})
    project=act('new',title='A book',kind='book',pageCount=2,width=64,height=48)
    first=project['pages'][0]['id']; second=project['pages'][1]['id']
    ws.dispatch('edit',{'operation':'add_layer','args':{'kind':'shape','params':{'width':16,'height':16,'color':'red'}}})
    act('update_page',pageId=first,text='A line of prose.\nAnother paragraph.',prompt='An orange fox')
    act('update_page',pageId=first,title='The first page')
    assert ws.document().title=='The first page'
    reference=tmp_path/'reference.png'; Image.new('RGBA',(10,10),'blue').save(reference)
    act('add_reference',path=str(reference),role='character',label='Fox')
    act('select',pageId=second); ws.dispatch('edit',{'operation':'fill','args':{'color':'green'}})
    bundle=tmp_path/'book.compbook'; act('save',path=str(bundle))
    original_id=project['id']
    loaded=act('open',path=str(bundle))
    assert loaded['id']!=original_id
    assert loaded['pages'][0]['text']=='A line of prose.\nAnother paragraph.'
    assert loaded['references'][0]['role']=='character'
    assert ws.document().render().getpixel((0,0))==(0,128,0,255)
    act('select',pageId=first)
    assert ws.document().layers[-1].kind=='shape'
    assert ws.document().render().getpixel((4,4))==(255,0,0,255)
    assert len(ws.projects.items)==2
    ws.save_recovery(); ws.generation.pool.shutdown()
    restored=Workspace(ws.settings)
    assert len(restored.projects.items)==2
    assert restored.document().layers[-1].kind=='shape'
    restored.generation.pool.shutdown()


def test_reading_export_contains_real_image_and_escaped_authored_prose(tmp_path):
    app,ws=workspace(tmp_path/'data')
    ws.projects.dispatch('new',{'title':'Title <one>','kind':'book','width':64,'height':48,'pageCount':1})
    ws.projects.dispatch('update_page',{'text':'A & B <script>ordinary prose</script>'})
    ws.dispatch('edit',{'operation':'fill','args':{'color':'#123456'}})
    path=tmp_path/'reading.html'; ws.projects.dispatch('export',{'path':str(path)})
    body=path.read_text(encoding='utf-8')
    assert 'A &amp; B &lt;script&gt;' in body and '<script>ordinary' not in body
    raw=base64.b64decode(body.split('base64,',1)[1].split('"',1)[0])
    assert Image.open(io.BytesIO(raw)).getpixel((10,10))==(18,52,86,255)
    pdf=tmp_path/'reading.pdf'; ws.projects.dispatch('export',{'path':str(pdf)})
    assert pdf.read_bytes().startswith(b'%PDF') and pdf.stat().st_size>1000
    from PySide6.QtPdf import QPdfDocument
    from PySide6.QtCore import QSize
    document=QPdfDocument(); document.load(str(pdf))
    assert document.pageCount()>=1
    assert 'ordinary prose' in ''.join(document.getAllText(i).text() for i in range(document.pageCount()))
    rendered=document.render(0,QSize(600,800))
    # PDF image encoding/color conversion may round channels; document PNGs are lossless.
    colored=sum(1 for y in range(0,800,10) for x in range(0,600,10) if max(abs(a-b) for a,b in zip(rendered.pixelColor(x,y).getRgb()[:3],(18,52,86)))<=3)
    assert colored>100
    document.close()
    ws.generation.pool.shutdown()


def test_project_bundle_rejects_path_traversal_before_writing_pages(tmp_path):
    app,ws=workspace(tmp_path/'data')
    project=ws.projects.dispatch('new',{'pageCount':1,'width':8,'height':8})
    project['pages'][0]['id']='../../outside'
    archive=tmp_path/'bad.compbook'
    with zipfile.ZipFile(archive,'w') as z: z.writestr('project.json',json.dumps(project))
    import pytest
    with pytest.raises(ValueError): ws.projects.dispatch('open',{'path':str(archive)})
    assert len(ws.projects.items)==1
    ws.generation.pool.shutdown()


def test_page_drafts_survive_operator_refresh_page_switch_and_restart(tmp_path):
    app,ws=workspace(tmp_path/'data')
    from compositor.ui import Editor
    window=Editor(ws)
    project=ws.dispatch('production',{'operation':'new','args':{'kind':'book','pageCount':2,'width':32,'height':32}})
    first,second=project['pages']
    window.production.text.setPlainText('Unfinished human prose')
    ws.dispatch('edit',{'operation':'fill','args':{'color':'blue'}})
    assert window.production.text.toPlainText()=='Unfinished human prose'
    ws.dispatch('production',{'operation':'select','args':{'pageId':second['id']}})
    window.production.text.setPlainText('Second draft')
    ws.dispatch('production',{'operation':'select','args':{'pageId':first['id']}})
    assert window.production.text.toPlainText()=='Unfinished human prose'
    window.close()
    restored=Workspace(ws.settings); reopened=Editor(restored)
    assert reopened.production.text.toPlainText()=='Unfinished human prose'
    assert reopened.production.save_all_text()
    saved=restored.projects.get(project['id'])
    assert saved['pages'][0]['text']=='Unfinished human prose'
    assert saved['pages'][1]['text']=='Second draft'
    reopened.close(); ws.generation.pool.shutdown(); restored.generation.pool.shutdown()


def test_presentation_navigation_and_operator_share_selected_page(tmp_path):
    app,ws=workspace(tmp_path/'data')
    from compositor.ui import Editor
    window=Editor(ws)
    project=ws.dispatch('production',{'operation':'new','args':{'kind':'comic','pageCount':2,'width':32,'height':64}})
    ws.dispatch('production',{'operation':'present','args':{'projectId':project['id'],'twoPanels':True}})
    app.processEvents(); presentation=window.production.presentation
    assert presentation.isVisible() and ws.view['presentation']['twoPanels']
    presentation.step(1)
    assert ws.view['presentation']['pageId']==project['pages'][1]['id']
    assert ws.active==project['pages'][1]['documentId']
    ws.dispatch('production',{'operation':'select','args':{'pageId':project['pages'][0]['id']}})
    assert presentation.index==0
    ws.dispatch('production',{'operation':'close_presentation','args':{}})
    assert not presentation.isVisible() and 'presentation' not in ws.view
    window.close(); ws.generation.pool.shutdown()
