"""Exercise the shipped GUI and MCP binaries together in an isolated store."""
from pathlib import Path
import argparse, base64, json, os, queue, socket, subprocess, tempfile, threading, time
import urllib.request
from PIL import Image


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('distribution',type=Path)
    args=parser.parse_args(); distribution=args.distribution.resolve()
    with tempfile.TemporaryDirectory(prefix='compositor-package-proof-') as temporary:
        root=Path(temporary)
        with socket.socket() as probe:
            probe.bind(('127.0.0.1',0)); port=probe.getsockname()[1]
        (root/'settings.json').write_text(json.dumps({'port':port}),encoding='utf-8')
        env={k:v for k,v in os.environ.items() if k not in ('OPENAI_API_KEY','GEMINI_API_KEY','COMPOSITOR_DATA')}
        env.update(COMPOSITOR_DATA=str(root),QT_QPA_PLATFORM='offscreen')
        flags=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0
        gui=subprocess.Popen([str(distribution/'Compositor.exe')],env=env,creationflags=flags)
        operator=None
        try:
            deadline=time.monotonic()+40
            while True:
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=1) as reply:
                        assert json.load(reply)['service']=='compositor'
                    break
                except OSError:
                    if gui.poll() is not None or time.monotonic()>deadline: raise RuntimeError('Packaged GUI did not start')
                    time.sleep(.1)
            operator=subprocess.Popen([str(distribution/'Compositor-Tools.exe'),'--mcp'],env=env,
                stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,encoding='utf-8',creationflags=flags)
            received=queue.Queue()
            def read():
                for line in operator.stdout:
                    try: received.put(json.loads(line))
                    except ValueError: pass
            threading.Thread(target=read,daemon=True).start()
            sequence=0
            def send(value): operator.stdin.write(json.dumps(value)+'\n'); operator.stdin.flush()
            def rpc(method,params):
                nonlocal sequence
                sequence+=1; request_id=sequence
                send({'jsonrpc':'2.0','id':request_id,'method':method,'params':params})
                while True:
                    result=received.get(timeout=40)
                    if result.get('id')==request_id:
                        assert 'error' not in result,result
                        return result['result']
            def tool(name,arguments):
                result=rpc('tools/call',{'name':name,'arguments':arguments})
                assert not result.get('isError'),result
                return json.loads(result['content'][0]['text'])
            rpc('initialize',{'protocolVersion':'2025-03-26','capabilities':{},'clientInfo':{'name':'distribution-proof','version':'1'}})
            send({'jsonrpc':'2.0','method':'notifications/initialized'})
            catalog=rpc('tools/list',{})
            document=tool('compositor_new_document',{'width':64,'height':64,'title':'Distribution proof','background':'white'})
            edited=tool('compositor_edit',{'operation':'add_layer','documentId':document['id'],'expectedRevision':document['revision'],
                'args':{'kind':'shape','x':16,'y':16,'params':{'width':32,'height':32,'color':'red'}}})
            stale=rpc('tools/call',{'name':'compositor_edit','arguments':{'operation':'clear','args':{},'documentId':document['id'],'expectedRevision':document['revision']}})
            assert stale.get('isError'),stale
            preview=rpc('tools/call',{'name':'compositor_view_image','arguments':{'documentId':document['id']}})
            assert preview['content'][0]['type']=='image'
            saved=tool('compositor_save_document',{'path':str(root/'proof.compwin'),'documentId':document['id']})
            exported=tool('compositor_export',{'path':str(root/'proof.png'),'documentId':document['id']})
            with Image.open(exported['path']) as pixels:
                assert pixels.getpixel((32,32))==(255,0,0,255)
                assert pixels.getpixel((0,0))==(255,255,255,255)
            tool('compositor_edit',{'operation':'undo','args':{},'documentId':document['id']})
            tool('compositor_export',{'path':str(root/'undone.png'),'documentId':document['id']})
            with Image.open(root/'undone.png') as pixels: assert pixels.getpixel((32,32))==(255,255,255,255)
            project=tool('compositor_production',{'operation':'new','args':{'title':'Portable project proof','kind':'book','width':64,'height':64,'pageCount':2}})
            tool('compositor_production',{'operation':'update_page','args':{'projectId':project['id'],'title':'Named page','text':'Portable authored prose'}})
            state=tool('compositor_get_workspace',{})
            assert next(d for d in state['documents'] if d['id']==state['activeDocument'])['title']=='Named page'
            tool('compositor_production',{'operation':'save','args':{'projectId':project['id'],'path':str(root/'project.compbook')}})
            reopened=tool('compositor_production',{'operation':'open','args':{'path':str(root/'project.compbook')}})
            assert reopened['id']!=project['id'] and reopened['pages'][0]['text']=='Portable authored prose'
            tool('compositor_production',{'operation':'export','args':{'projectId':project['id'],'path':str(root/'reading.html')}})
            assert 'Portable authored prose' in (root/'reading.html').read_text(encoding='utf-8')
            print(json.dumps({'passed':True,'tools':len(catalog['tools']),'gui':str(distribution/'Compositor.exe'),
                'verified':['MCP mutation','stale revision rejection','actual canvas image','layered save','exact export pixels','undo','portable production project','reading export']}))
        finally:
            if operator is not None:
                operator.stdin.close()
                try: operator.wait(timeout=5)
                except subprocess.TimeoutExpired: operator.terminate(); operator.wait(timeout=5)
            gui.terminate(); gui.wait(timeout=10)


if __name__=='__main__': main()
