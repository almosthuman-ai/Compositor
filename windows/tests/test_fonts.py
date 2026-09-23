from PIL import ImageFont
from compositor import fonts,pixels
from compositor.document import Document,Layer


def test_installed_font_families_resolve_real_faces():
    catalog=fonts.catalog()
    assert len(catalog)>10
    for family,style in [('Arial','Regular'),('Arial','Bold'),('Georgia','Italic')]:
        face=fonts.resolve(family,style); assert face is not None
        actual=ImageFont.truetype(face['path'],32,index=face['index'])
        assert actual.getname()==(face['family'],face['style'])


def test_family_based_text_remains_editable_after_save_and_does_not_need_old_path(tmp_path):
    params={'text':'A considered composition\nType stays editable.','fontFamily':'Georgia','fontStyle':'Bold','font':'Z:/a/different/computer/missing.ttf','size':32,'color':'#242424','align':'center','spacing':9}
    d=Document(600,240); d.execute('add_layer',{'kind':'text','params':params})
    first=d.render().tobytes(); d.save(tmp_path/'type.compwin'); restored=Document.load(tmp_path/'type.compwin')
    assert restored.layer().params['fontFamily']=='Georgia' and restored.render().tobytes()==first
    restored.execute('update_layer',{'params':{**params,'fontFamily':'Arial','fontStyle':'Regular'}})
    assert restored.render().tobytes()!=first
    restored.execute('undo'); assert restored.render().tobytes()==first


def test_text_dialog_creates_and_edits_typography_through_the_shared_document(tmp_path):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer,QPointF
    from compositor.ui import Editor
    from compositor.settings import Settings
    from compositor.workspace import Workspace
    from compositor.text_ui import TextDialog
    app=QApplication.instance() or QApplication([]); ws=Workspace(Settings(tmp_path),restore=False); window=Editor(ws)
    ws.dispatch('new',{'width':800,'height':500}); revision=ws.document().revision
    def compose():
        dialog=app.activeModalWidget(); assert isinstance(dialog,TextDialog)
        dialog.family.setCurrentText('Georgia'); dialog.face.setCurrentText('Bold'); dialog.size.setValue(48)
        dialog.text.setPlainText('Poster title\nSecond line'); dialog.align.setCurrentIndex(1); dialog.update_preview()
        assert not dialog.preview.image.isNull(); dialog.apply()
    QTimer.singleShot(0,compose); window.add_text(QPointF(30,40))
    layer=ws.document().layer(); assert layer.kind=='text' and layer.x==30 and layer.y==40
    assert layer.params['fontFamily']=='Georgia' and layer.params['fontStyle']=='Bold' and layer.params['align']=='center'
    assert ws.document().revision==revision+1
    def revise():
        dialog=app.activeModalWidget(); dialog.text.setPlainText('Revised title'); dialog.apply()
    QTimer.singleShot(0,revise); window.edit_layer_content()
    assert ws.document().layer().params['text']=='Revised title'
    ws.dispatch('edit',{'operation':'undo'}); assert ws.document().layer().params['text']=='Poster title\nSecond line'
    window.close(); ws.generation.pool.shutdown()


def test_text_draft_stays_with_its_document_and_survives_concurrent_edits(tmp_path):
    from PySide6.QtWidgets import QApplication
    from compositor.ui import Editor
    from compositor.settings import Settings
    from compositor.workspace import Workspace
    from compositor.text_ui import TextDialog
    app=QApplication.instance() or QApplication([]); ws=Workspace(Settings(tmp_path),restore=False); window=Editor(ws)
    ws.dispatch('new',{'width':400,'height':300}); original=ws.document()
    original.execute('add_layer',{'kind':'text','params':{'text':'Original','fontFamily':'Arial','size':24}})
    layer=original.layer(); dialog=TextDialog(window,layer.params,commit=window.text_commit(original,'update_layer',{'layerId':layer.id}))
    dialog.text.setPlainText('Human draft'); dialog.show()
    ws.dispatch('new',{'width':100,'height':100}); other=ws.document()
    ws.dispatch('edit',{'documentId':original.id,'operation':'update_layer','args':{'layerId':layer.id,'params':{**layer.params,'text':'Agent revision'}}})
    dialog.apply()
    assert dialog.isVisible() and 'draft is kept' in dialog.message.text()
    assert dialog.text.toPlainText()=='Human draft' and original.layer().params['text']=='Agent revision'
    assert ws.active==other.id and len(other.layers)==1
    dialog.apply()
    assert not dialog.isVisible() and original.layer().params['text']=='Human draft' and ws.active==original.id
    original.execute('undo'); assert original.layer().params['text']=='Agent revision'
    window.close(); ws.generation.pool.shutdown()
