"""Optional project connectors. Core editing and generation never require a connector."""
from pathlib import Path
from urllib.parse import urlparse
import urllib.request, json, uuid
from .generation import http_json

class StudioConnector:
    def __init__(self,url,exchange):
        parsed=urlparse(url)
        if parsed.scheme!='http' or parsed.hostname not in ('localhost','127.0.0.1'): raise ValueError('The Studio connector needs a local HTTP service URL')
        self.url=url.rstrip('/'); self.exchange=Path(exchange); self.exchange.mkdir(parents=True,exist_ok=True)

    def state(self): return http_json(self.url+'/api/state',timeout=10)
    def action(self,action,args): return http_json(self.url+'/api/action',{'action':action,'args':args},timeout=300)
    def projects(self):
        return [{k:l.get(k) for k in ('id','title','date','format','collection')} for l in self.state()['lessons']]

    def pull(self,lesson_id,role='background',page=1):
        state=self.state(); project=next(l for l in state['lessons'] if l['id']==lesson_id)
        if role=='page': asset_id=project['comic']['pages'][page-1]['selected']
        else:
            bg=next(b for b in project['scene']['backgrounds'] if b['id']==project['scene']['selected'])
            asset_id=bg['layers'][bg['activeCount']-1]['composition'] if bg['activeCount'] else bg['asset']
        if not asset_id: raise ValueError('Select an image in the project first')
        destination=self.exchange/f'{asset_id}.png'
        with urllib.request.urlopen(self.url+'/asset/'+asset_id,timeout=30) as response: destination.write_bytes(response.read())
        return {'path':str(destination),'title':project['title'],'link':{'connector':'owen-vic','url':self.url,'lessonId':lesson_id,'role':role,'page':page,'sourceAsset':asset_id}}

    def push(self,document,lesson_id,role='background',page=1):
        path=self.exchange/(str(uuid.uuid4())+'.png'); document.export(path)
        return self.action('import_asset',{'lessonId':lesson_id,'role':role,'page':page,'path':str(path),'label':document.title})
