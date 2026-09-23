"""Per-user public configuration; no dependency on a developer's workspace."""
from pathlib import Path
import json, os, re, secrets

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

    def model_for(self,provider):
        from .providers import MODELS
        if provider==self.values['provider']:return self.values['model']
        return self.values.get('provider_models',{}).get(provider,MODELS[provider][0][1])

    def artwork_directory(self,source_path=None):
        """Choose a visible initial location, independent of process working directory."""
        configured=self.values.get('artwork_directory')
        if configured and Path(configured).is_dir(): return Path(configured).resolve()
        if source_path:
            folder=Path(source_path).resolve().parent
            private=[self.root.resolve()]+[Path(os.environ[key]).resolve() for key in ('LOCALAPPDATA','APPDATA') if os.environ.get(key)]
            if folder.is_dir() and not any(folder.is_relative_to(root) for root in private) and not any(part.startswith('.') for part in folder.parts):
                return folder
        from PySide6.QtCore import QStandardPaths
        for location in (QStandardPaths.StandardLocation.PicturesLocation,QStandardPaths.StandardLocation.DocumentsLocation):
            value=QStandardPaths.writableLocation(location)
            if value and Path(value).is_dir(): return Path(value).resolve()
        return Path.home()

    def file_dialog_path(self,purpose,name='',source_path=None):
        remembered=self.values.get('file_dialog_directories',{}).get(purpose)
        folder=Path(remembered) if remembered and Path(remembered).is_dir() else self.artwork_directory(source_path)
        name=re.sub(r'[<>:"/\\|?*\x00-\x1f]','_',name).rstrip(' .')
        return str(folder.resolve()/name) if name else str(folder.resolve())

    def remember_file_dialog(self,purpose,path):
        self.values.setdefault('file_dialog_directories',{})[purpose]=str(Path(path).resolve().parent)
        self.save()

    def key(self,provider):
        # Windows Credential Manager via keyring. Keys never appear in settings or MCP replies.
        try:
            import keyring
            saved=keyring.get_password('Compositor',provider)
            if saved:return saved
        except ImportError:pass
        names=('OPENAI_API_KEY',) if provider=='openai' else ('GEMINI_API_KEY','GOOGLE_API_KEY')
        return next((os.environ[name] for name in names if os.environ.get(name)),'')

    def set_key(self,provider,value):
        import keyring
        keyring.set_password('Compositor',provider,value)

    def public(self):
        return {**self.values,'providers':{p:bool(self.key(p)) for p in ('openai','gemini')}}
