import pytest
from PySide6.QtWidgets import QApplication
from compositor.document import Document
from compositor.settings import Settings
from compositor.workspace import Workspace


def test_undo_to_saved_art_clears_dirty_without_reusing_revision(tmp_path):
    d=Document(8,8); d.execute('add_layer',{'color':'white'}); d.save(tmp_path/'art.compwin'); saved_revision=d.revision
    d.execute('fill',{'color':'red'}); assert d.dirty
    d.execute('undo'); assert not d.dirty and not d.info()['dirty']
    assert d.revision>saved_revision and d.render().getpixel((0,0))==(255,255,255,255)
    with pytest.raises(ValueError,match='Document changed'): d.execute('fill',{'color':'blue'},expected_revision=saved_revision)
    d.execute('redo'); assert d.dirty and d.render().getpixel((0,0))==(255,0,0,255)


def test_saved_checkpoint_survives_history_branch_and_resave(tmp_path):
    d=Document(8,8); d.execute('add_layer',{'color':'white'}); d.save(tmp_path/'art.compwin')
    d.execute('fill',{'color':'red'}); d.save(tmp_path/'art.compwin')
    d.execute('undo'); assert d.dirty
    d.execute('redo'); assert not d.dirty
    d.execute('undo'); d.execute('fill',{'color':'blue'}); assert d.dirty and not d.future
    d.execute('undo'); assert d.dirty


def test_recovery_and_close_use_the_restored_saved_state(tmp_path):
    app=QApplication.instance() or QApplication([]); settings=Settings(tmp_path/'store'); ws=Workspace(settings,restore=False)
    ws.dispatch('new',{'width':8,'height':8}); doc=ws.document(); ws.dispatch('save',{'path':str(tmp_path/'art.compwin')})
    ws.dispatch('edit',{'operation':'fill','args':{'color':'red'}}); ws.dispatch('edit',{'operation':'undo','args':{}})
    ws.save_recovery(); restored=Workspace(settings); assert not restored.document().dirty
    result=ws.dispatch('close',{'documentId':doc.id}); assert doc.id not in ws.documents
    ws.generation.pool.shutdown(); restored.generation.pool.shutdown()
