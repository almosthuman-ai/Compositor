from types import SimpleNamespace
import threading,time
import pytest
from PySide6.QtWidgets import QApplication
from compositor.settings import Settings
from compositor.workspace import Workspace
from compositor.ui import Editor
from compositor.chat import ChatSession
from test_generation_route import fake_chat


def test_queued_message_survives_signin_and_pins_its_document(tmp_path):
    app=QApplication.instance() or QApplication([]); ws=Workspace(Settings(tmp_path),restore=False)
    first=ws.dispatch('new',{'width':8,'height':8})
    chat,messages,calls=fake_chat(ws); chat.initialized=False; chat.account_checked=False; chat.account=None
    assert chat.send_message('Make this blue')=='connecting'
    assert not calls and 'Make this blue' not in messages
    with pytest.raises(ValueError,match='current ChatGPT'): chat.send_message('Duplicate')
    ws.dispatch('new',{'width':8,'height':8})
    chat.initialized=True; chat.account_checked=True; assert chat.flush_message()=='awaiting_signin'
    chat.account={'planType':'plus'}; assert chat.flush_message()=='requested'
    assert chat.active_document==first['id'] and 'Make this blue' in messages
    assert len(calls)==1 and not chat.waiting_message
    ws.generation.pool.shutdown()


def test_stop_cancels_message_waiting_for_connection(tmp_path):
    app=QApplication.instance() or QApplication([]); ws=Workspace(Settings(tmp_path),restore=False)
    chat,messages,calls=fake_chat(ws); chat.initialized=False; chat.account_checked=False; chat.turn=None
    chat.send_message('A draft'); ChatSession.interrupt(chat)
    chat.initialized=True; chat.account_checked=True; chat.flush_message()
    assert not calls and not chat.waiting_message and not chat.busy
    ws.generation.pool.shutdown()


def test_first_send_installs_automatically_without_losing_or_redirecting_draft(tmp_path,monkeypatch):
    from compositor import codex_runtime
    app=QApplication.instance() or QApplication([]); ws=Workspace(Settings(tmp_path),restore=False); first=ws.dispatch('new',{'width':8,'height':8}); editor=Editor(ws)
    release=threading.Event(); sent=[]
    def install(root,progress):
        assert release.wait(3)
        return 'C:/example/codex.exe'
    monkeypatch.setattr(codex_runtime,'install_runtime',install)
    def ensure():
        if not ws.settings.values.get('codex_path'): raise RuntimeError('Setup needed')
        return SimpleNamespace(send_message=lambda text,context:sent.append((text,context)))
    monkeypatch.setattr(editor,'ensure_chat',ensure)
    editor.chat_input.setPlainText('Keep this message'); editor.chat_send()
    assert editor.chat_input.toPlainText()=='Keep this message' and not editor.chat_log.toPlainText()
    ws.dispatch('new',{'width':8,'height':8}); release.set()
    deadline=time.monotonic()+3
    while not sent and time.monotonic()<deadline: app.processEvents(); time.sleep(.01)
    assert len(sent)==1 and sent[0][1]['documentId']==first['id']
    editor.chat_input.setPlainText('A newer draft'); editor.chat_message_sent('Keep this message')
    assert editor.chat_input.toPlainText()=='A newer draft'
    editor.close(); ws.generation.pool.shutdown()


def test_working_folder_change_reconnects_only_when_idle(tmp_path):
    app=QApplication.instance() or QApplication([]); ws=Workspace(Settings(tmp_path),restore=False); reconnects=[]
    ws.window=SimpleNamespace(chat=SimpleNamespace(busy=True,waiting_message=None),reconnect_chat=lambda:reconnects.append(True))
    folder=tmp_path/'artwork'
    with pytest.raises(ValueError,match='Stop the current'): ws.dispatch('settings',{'chat_working_directory':str(folder)})
    assert not folder.exists() and 'chat_working_directory' not in ws.settings.values
    ws.window.chat.busy=False; ws.dispatch('settings',{'chat_working_directory':str(folder)})
    assert folder.is_dir() and reconnects==[True]
    ws.generation.pool.shutdown()


def test_window_geometry_and_open_panel_survive_reopening(tmp_path):
    app=QApplication.instance() or QApplication([]); settings=Settings(tmp_path); ws=Workspace(settings,restore=False); editor=Editor(ws)
    # Qt clamps restored windows to the available screen; the offscreen test
    # display is small, so keep the height within its usable area.
    editor.resize(1000,740); editor.show(); editor.show_panel(editor.production_dock); app.processEvents(); expected=editor.size()
    editor.close(); ws.generation.pool.shutdown()
    restored_ws=Workspace(settings,restore=False); restored=Editor(restored_ws)
    assert restored.size()==expected and not restored.production_dock.isHidden() and restored.chat_dock.isHidden()
    restored.close(); restored_ws.generation.pool.shutdown()


def test_reply_markdown_renders_without_changing_user_text():
    from compositor.chat import message_html
    from PySide6.QtGui import QTextDocument
    app=QApplication.instance() or QApplication([])
    document=QTextDocument(); document.setHtml(message_html('assistant','A **bold** choice.\n\n- First\n- Second'))
    assert '**' not in document.toPlainText() and 'bold' in document.toPlainText()
    cursor=document.find('bold'); assert cursor.charFormat().fontWeight()>400
    document.setHtml(message_html('user','Keep **these** and <this>'))
    assert 'Keep **these** and <this>' in document.toPlainText()
