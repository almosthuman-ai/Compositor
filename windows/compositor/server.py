"""Authenticated loopback transport to the Qt owner; never a second document engine."""
from concurrent.futures import Future, TimeoutError
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json, secrets, threading

def start_server(workspace,port=None):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self,*args): pass
        def reply(self,status,value):
            raw=json.dumps(value,ensure_ascii=False).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(raw))); self.end_headers()
            try: self.wfile.write(raw)
            except (BrokenPipeError,ConnectionResetError): pass
        def do_GET(self):
            if self.path=='/health': self.reply(200,{'service':'compositor','version':1}); return
            self.reply(404,{'error':'Not found'})
        def do_POST(self):
            if self.headers.get('Origin') or not secrets.compare_digest(self.headers.get('Authorization',''),'Bearer '+workspace.settings.token): self.reply(403,{'error':'Local operator authentication required'}); return
            if self.path!='/action': self.reply(404,{'error':'Not found'}); return
            try:
                length=int(self.headers.get('Content-Length',0))
                if not 0<length<=16*1024*1024: raise ValueError('Invalid request size')
                body=json.loads(self.rfile.read(length)); future=Future()
                workspace.request_received.emit({'action':body['action'],'args':body.get('args',{}),'future':future})
                try: result=future.result(timeout=180)
                except TimeoutError:
                    if future.cancel(): raise RuntimeError('Editor was busy; request was cancelled before execution')
                    raise RuntimeError('Operation is still running; inspect canonical state before retrying')
                self.reply(200,result)
            except Exception as e: self.reply(400,{'error':str(e)})
    server=ThreadingHTTPServer(('127.0.0.1',port if port is not None else workspace.settings.values['port']),Handler)
    thread=threading.Thread(target=server.serve_forever,daemon=True,name='compositor-operator'); thread.start(); return server
