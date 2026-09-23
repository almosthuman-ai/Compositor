from types import SimpleNamespace
import tomllib
from PySide6.QtWidgets import QApplication,QPushButton,QComboBox
from compositor.settings import Settings
from compositor.workspace import Workspace
from compositor.ui import Editor
from compositor.chat import ChatSession


def test_account_controls_show_only_the_current_action(tmp_path):
    app=QApplication.instance() or QApplication([])
    ws=Workspace(Settings(tmp_path),restore=False); editor=Editor(ws)
    editor.chat=SimpleNamespace(account_checked=False,account=None,shutdown=lambda:None)
    editor.update_chat_account()
    assert editor.login_button.isHidden() and editor.logout_button.isHidden()
    editor.chat.account_checked=True; editor.chat.account={'email':'artist@example.com','planType':'plus'}
    editor.update_chat_account()
    assert editor.login_button.isHidden() and not editor.logout_button.isHidden()
    assert editor.chat_account.text()=='artist@example.com'
    editor.chat_status.setText('Working…')
    assert editor.chat_account.text()=='artist@example.com'
    editor.chat.account=None; editor.update_chat_account()
    assert not editor.login_button.isHidden() and editor.logout_button.isHidden()
    assert not editor.chat_account.text()
    editor.close(); ws.generation.pool.shutdown()


def test_model_defaults_to_sol_and_preserves_explicit_choice(tmp_path):
    settings=Settings(tmp_path)
    chat=SimpleNamespace(ws=SimpleNamespace(settings=settings),models_changed=SimpleNamespace(emit=lambda:None))
    catalog={'data':[{'model':'gpt-6-astra','isDefault':True},{'model':'gpt-6-sol'}]}
    ChatSession.models_response(chat,catalog); assert chat.model=='gpt-6-sol'
    settings.values['chat_model']='another-user-choice'
    ChatSession.models_response(chat,catalog); assert chat.model=='another-user-choice'


def test_owned_mcp_connection_has_explicit_approval_and_no_borrowed_home(tmp_path):
    chat=SimpleNamespace(ws=SimpleNamespace(settings=Settings(tmp_path)),home=tmp_path/'chat')
    chat.home.mkdir(); ChatSession.configure_mcp(chat)
    config=tomllib.loads((chat.home/'config.toml').read_text())
    assert config['mcp_servers']['compositor']['default_tools_approval_mode']=='approve'
    assert config['mcp_servers']['compositor']['env']['COMPOSITOR_DATA']==str(tmp_path)
    assert set(config['mcp_servers'])=={'compositor'}


def test_questions_remain_in_panel_and_submit_actual_option(tmp_path):
    app=QApplication.instance() or QApplication([])
    ws=Workspace(Settings(tmp_path),restore=False); editor=Editor(ws); answers=[]
    editor.chat=SimpleNamespace(answer_request=lambda msg,result:answers.append(result),shutdown=lambda:None)
    request={'id':7,'method':'tool/requestUserInput','params':{'questions':[{'id':'choice','question':'Which version?','options':[{'label':'Warm'},{'label':'Cool'}]}]}}
    editor.show_chat_question(request)
    assert QApplication.activeModalWidget() is None and not editor.isVisible()
    button=editor.chat_questions.findChild(QPushButton); button.click(); assert not answers
    combo=editor.chat_questions.findChild(QComboBox); combo.setCurrentIndex(2); button.click()
    assert answers==[{'answers':{'choice':{'answers':['Cool']}}}]
    editor.clear_chat_questions(); assert editor.chat_questions.isHidden()
    editor.close(); ws.generation.pool.shutdown()


def test_windows_setup_finishes_before_account_discovery(tmp_path,monkeypatch):
    from compositor import chat as module
    monkeypatch.setattr(module.os,'name','nt'); calls=[]
    session=SimpleNamespace(write=lambda p:calls.append(p),rpc=lambda *p:calls.append(p),status=SimpleNamespace(emit=lambda _:None),discover_account=lambda:calls.append('discover'))
    ChatSession.initialized_response(session,{})
    assert calls[-1]==('windowsSandbox/setupStart',{'mode':'unelevated'}) and 'discover' not in calls
    ChatSession.notification(session,'windowsSandbox/setupCompleted',{'success':True})
    assert calls[-1]=='discover'
