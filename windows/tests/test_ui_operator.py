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
