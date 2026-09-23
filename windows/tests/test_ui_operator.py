import json, threading, time, urllib.request
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QFontDatabase
from PySide6.QtTest import QTest
from compositor.settings import Settings
from compositor.workspace import Workspace
from compositor.server import start_server
from compositor.ui import Editor

def app():
    application=QApplication.instance() or QApplication([])
    QFontDatabase.addApplicationFont('C:/Windows/Fonts/segoeui.ttf')
    return application

def test_native_brush_selection_undo_and_operator_share_one_document(tmp_path):
    application=app(); ws=Workspace(Settings(tmp_path),restore=False); window=Editor(ws); ws.dispatch('new',{'width':128,'height':128}); window.show(); application.processEvents(); window.canvas.fit()
    window.set_tool('brush'); window.color='#ff0000'; window.hardness.setValue(100)
    center=window.canvas.mapFromScene(64,64)
    QTest.mouseClick(window.canvas.viewport(),Qt.MouseButton.LeftButton,pos=center); application.processEvents()
    assert ws.document().render().getpixel((64,64))==(255,0,0,255)
    server=start_server(ws,0); result=[]
    def request():
        url=f'http://127.0.0.1:{server.server_port}/action'; req=urllib.request.Request(url,data=json.dumps({'action':'edit','args':{'operation':'undo'}}).encode(),headers={'Authorization':'Bearer '+ws.settings.token,'Content-Type':'application/json'})
        with urllib.request.urlopen(req) as response: result.append(json.load(response))
    worker=threading.Thread(target=request); worker.start(); end=time.monotonic()+5
    while worker.is_alive() and time.monotonic()<end: application.processEvents(); time.sleep(.01)
    worker.join(1); assert result[0]['id']==ws.document().id; assert ws.document().render().getpixel((64,64))==(255,255,255,255)
    window.close(); server.shutdown(); ws.generation.pool.shutdown()

def test_recovery_reopens_unsaved_work_without_claiming_it_was_saved(tmp_path):
    application=app(); settings=Settings(tmp_path); ws=Workspace(settings,restore=False); ws.dispatch('new',{'width':32,'height':32,'title':'Unfinished'}); ws.dispatch('edit',{'operation':'fill','args':{'color':'blue'}}); ws.save_recovery()
    restored=Workspace(settings); assert restored.document().title=='Unfinished'; assert restored.document().info()['dirty']; assert restored.document().path is None; assert restored.document().render().getpixel((0,0))==(0,0,255,255)
    ws.generation.pool.shutdown(); restored.generation.pool.shutdown()


def test_editor_chrome_changes_real_color_visibility_and_dimensions(tmp_path):
    application=app(); ws=Workspace(Settings(tmp_path),restore=False); window=Editor(ws)
    ws.dispatch('new',{'width':128,'height':128}); window.show(); application.processEvents(); window.canvas.fit()
    # Color controls feed the same foreground that the actual brush uses.
    field=window.color_panel.hex; field.setText('#1357ac'); QTest.keyClick(field,Qt.Key.Key_Return)
    assert window.color=='#1357ac'
    QTest.mouseClick(window.color_panel.plane,Qt.MouseButton.LeftButton,pos=QPoint(window.color_panel.plane.width()-2,2))
    assert window.color==window.color_panel.hex.text() and window.color!='#1357ac'
    # Eye hit target changes canonical visibility and can be undone.
    item=window.layers.item(0); box=window.layers.visualItemRect(item)
    QTest.mouseClick(window.layers.viewport(),Qt.MouseButton.LeftButton,pos=QPoint(16,box.center().y())); application.processEvents()
    assert not ws.document().layer().visible
    assert ws.document().render().getpixel((64,64))[3]==0
    ws.dispatch('edit',{'operation':'undo'}); assert ws.document().layer().visible
    # Width is shown in pixels, converted into the document's nondestructive scale.
    window.transform_fields['sx'].setValue(64); window.transform_fields['sx'].editingFinished.emit()
    assert ws.document().layer().sx==.5
    assert window.transform_fields['sx'].value()==64
    for dock in (window.generation_dock,window.chat_dock,window.production_dock):
        window.show_panel(dock); application.processEvents(); assert window.layers.isVisible()
        assert sum(d.isVisible() for d in (window.generation_dock,window.chat_dock,window.production_dock))==1
    window.production_dock.hide(); window.resize(1280,800); application.processEvents()
    assert 300<=window.layer_dock.width()<=340
    assert window.canvas.viewport().width()>850
    assert window.color_panel.plane.height()>=32
    # All tool shortcuts also maintain the selected icon state.
    window.set_tool('brush'); assert window.tool_actions['brush'].isChecked()
    assert all(not action.icon().isNull() for action in window.tool_actions.values())
    window.close(); ws.generation.pool.shutdown()
