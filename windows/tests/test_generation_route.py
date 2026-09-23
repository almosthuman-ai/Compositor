import copy,time
from types import SimpleNamespace,MethodType
import pytest
from PySide6.QtWidgets import QApplication
from compositor.workspace import Workspace
from compositor.settings import Settings
from compositor.ui import Editor
from compositor.chat import ChatSession


def fake_chat(ws):
    messages=[]; calls=[]
    signal=SimpleNamespace(emit=messages.append)
    chat=SimpleNamespace(ws=ws,busy=False,generation_waiting=False,initialized=True,account_checked=True,account={'planType':'plus'},
        after_ready=[],thread='conversation',model='account-model',status=signal,display=signal,native_sources={},turn_started_at=time.time(),
        record=lambda *a:None,rpc=lambda method,params,callback:calls.append((method,params)),turn_started=lambda r:None,
        requested_generation=None,login=lambda:messages.append('login'))
    for name in ('send_generation','send_message','start_turn'): setattr(chat,name,MethodType(getattr(ChatSession,name),chat))
    return chat,messages,calls


def test_subscription_route_uses_prepared_project_snapshot_without_an_api_key(tmp_path,monkeypatch):
    app=QApplication.instance() or QApplication([]); ws=Workspace(Settings(tmp_path),restore=False); editor=Editor(ws)
    project=ws.dispatch('production',{'operation':'new','args':{'kind':'comic','pageCount':1,'width':32,'height':32}})
    ws.dispatch('production',{'operation':'set_style','args':{'styleId':'clean-line-comic'}})
    chat,messages,calls=fake_chat(ws); monkeypatch.setattr(editor,'ensure_chat',lambda:chat)
    monkeypatch.setattr(ws.settings,'key',lambda _:pytest.fail('Subscription generation must not fetch an API credential'))
    # Settings.public also reports key readiness; restore that unrelated query for UI refreshes.
    monkeypatch.setattr(ws.settings,'public',lambda:ws.settings.values)
    ws.dispatch('settings',{'generationRoute':'chatgpt'})
    result=ws.dispatch('production',{'operation':'generate','args':{'prompt':'A bicycle courier at dusk.','size':'1024x1024'}})
    assert result['route']=='chatgpt' and result['status']=='requested' and chat.busy
    prepared=copy.deepcopy(chat.requested_generation)
    assert prepared['creativeContext']['projectId']==project['id'] and 'confident ink contours' in prepared['prompt']
    assert prepared['requestedSize']=='1024x1024' and 'preparedGeneration' in calls[0][1]['input'][0]['text']
    original=ws.document(); ws.dispatch('new',{'width':8,'height':8})
    ChatSession.notification(chat,'item/started',{'item':{'type':'imageGeneration','id':'native-1'}})
    assert chat.native_sources['native-1']['documentId']==original.id
    assert chat.native_sources['native-1']['sourceRevision']==original.revision
    assert not ws.generation.jobs and not any(label=='generation' for label,_ in original.history)
    editor.close(); ws.generation.pool.shutdown()


def test_connection_wait_preserves_request_and_does_not_fall_back_when_unsigned(tmp_path):
    app=QApplication.instance() or QApplication([]); ws=Workspace(Settings(tmp_path),restore=False); ws.dispatch('new',{'width':16,'height':16})
    prepared=ws.dispatch('prepare_generation',{'kind':'generate','prompt':'A fox'})
    chat,messages,calls=fake_chat(ws); chat.initialized=False; chat.account_checked=False; chat.account=None
    result=chat.send_generation(prepared); assert result['status']=='connecting' and chat.generation_waiting
    with pytest.raises(ValueError,match='current ChatGPT'): chat.send_generation(prepared)
    chat.initialized=True; chat.account_checked=True; chat.after_ready.pop()()
    assert not chat.generation_waiting and not chat.busy and not calls
    assert 'login' in messages and 'Finish signing in' in messages[-1]
    ws.generation.pool.shutdown()


def test_api_route_can_be_explicit_even_when_user_prefers_subscription(tmp_path,monkeypatch):
    app=QApplication.instance() or QApplication([]); ws=Workspace(Settings(tmp_path),restore=False); ws.dispatch('new',{'width':16,'height':16})
    ws.dispatch('settings',{'generationRoute':'chatgpt'}); submitted=[]
    monkeypatch.setattr(ws.generation,'submit',lambda doc,args:submitted.append(args) or {'status':'queued'})
    result=ws.dispatch('generate',{'prompt':'A fox','route':'api'})
    assert result['status']=='queued' and submitted[0]['userPrompt']=='A fox'
    with pytest.raises(ValueError,match='Open the Compositor'): ws.dispatch('generate',{'prompt':'A fox'})
    ws.generation.pool.shutdown()
