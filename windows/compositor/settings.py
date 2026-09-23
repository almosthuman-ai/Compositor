"""Per-user public configuration; no dependency on a developer's workspace."""
from pathlib import Path
import json, os, secrets

def data_root():
    return Path(os.environ.get('COMPOSITOR_DATA',str(Path(os.environ.get('LOCALAPPDATA',Path.home()/'.local/share'))/'Compositor')))

def atomic_json(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix(path.suffix+'.tmp'); temp.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8'); os.replace(temp,path)

class Settings:
    def __init__(self,root=None):
        self.root=Path(root) if root else data_root(); self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'settings.json'
        self.values=json.loads(self.path.read_text(encoding='utf-8')) if self.path.exists() else {}
        self.values.setdefault('provider','openai'); self.values.setdefault('model','gpt-image-1')
        self.values.setdefault('openai_url','https://api.openai.com/v1'); self.values.setdefault('gemini_url','https://generativelanguage.googleapis.com/v1beta')
        self.values.setdefault('studio_url',''); self.values.setdefault('port',47841)
        self.values.setdefault('generationRoute','api')
        self.values.setdefault('chat_model','gpt-6-sol')
        token_path=self.root/'operator-token'
        if not token_path.exists(): token_path.write_text(secrets.token_urlsafe(32),encoding='utf-8')
        self.token=token_path.read_text(encoding='utf-8').strip()

    def save(self): atomic_json(self.path,self.values)

    def key(self,provider):
        env='OPENAI_API_KEY' if provider=='openai' else 'GEMINI_API_KEY'
        if os.environ.get(env): return os.environ[env]
        # Windows Credential Manager via keyring. Keys never appear in settings or MCP replies.
        try:
            import keyring
            return keyring.get_password('Compositor',provider) or ''
        except ImportError: return ''

    def set_key(self,provider,value):
        import keyring
        keyring.set_password('Compositor',provider,value)

    def public(self):
        return {**self.values,'providers':{p:bool(self.key(p)) for p in ('openai','gemini')}}
