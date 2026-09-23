"""Discover installed font faces; documents name a family and retain a file hint."""
from functools import lru_cache
from pathlib import Path
import os
from PIL import ImageFont


@lru_cache(maxsize=1)
def faces():
    system=Path(os.environ.get('WINDIR','C:/Windows'))/'Fonts'
    user=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'Microsoft/Windows/Fonts'
    paths=set()
    for folder in (system,user):
        if folder.is_dir(): paths.update(p.resolve() for p in folder.iterdir() if p.suffix.lower() in ('.ttf','.otf','.ttc'))
    if os.name=='nt':
        import winreg
        for hive in (winreg.HKEY_LOCAL_MACHINE,winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(hive,r'SOFTWARE\Microsoft\Windows NT\CurrentVersion\Fonts') as key:
                    for i in range(winreg.QueryInfoKey(key)[1]):
                        value=winreg.EnumValue(key,i)[1]
                        if isinstance(value,str):
                            path=Path(value); path=path if path.is_absolute() else system/path
                            if path.suffix.lower() in ('.ttf','.otf','.ttc') and path.is_file(): paths.add(path.resolve())
            except OSError: pass
    result=[]
    for path in sorted(paths):
        for index in range(64 if path.suffix.lower()=='.ttc' else 1):
            try:
                face=ImageFont.truetype(str(path),16,index=index); family,style=face.getname()
                result.append({'family':family,'style':style,'path':str(path),'index':index})
            except OSError: break
    return tuple(sorted(result,key=lambda f:(f['family'].casefold(),f['style'].casefold())))


def families(): return sorted({face['family'] for face in faces()},key=str.casefold)

def styles(family): return list(dict.fromkeys(face['style'] for face in faces() if face['family']==family))

def resolve(family,style='Regular'):
    choices=[face for face in faces() if face['family'].casefold()==family.casefold()]
    return next((f for f in choices if f['style'].casefold()==style.casefold()),None) or next((f for f in choices if f['style'] in ('Regular','Normal','Book','Roman')),None) or (choices[0] if choices else None)


def identify(params):
    if params.get('fontFamily'): return resolve(params['fontFamily'],params.get('fontStyle','Regular'))
    try:
        face=ImageFont.truetype(params.get('font','C:/Windows/Fonts/arial.ttf'),16,index=int(params.get('fontIndex',0)))
        family,style=face.getname(); return resolve(family,style)
    except OSError: return None


def catalog(): return [{'family':name,'styles':styles(name)} for name in families()]
