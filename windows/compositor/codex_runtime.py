"""Install the official Windows Codex runtime without requiring Node or a terminal."""
from pathlib import Path
import base64, hashlib, hmac, io, json, os, tarfile, urllib.request, uuid

VERSION='0.156.0'
def install_runtime(root,progress=lambda text:None):
    destination=Path(root)/'runtimes'/('codex-'+VERSION)
    executable=destination/'package/vendor/x86_64-pc-windows-msvc/bin/codex.exe'
    if executable.is_file(): return str(executable)
    progress('Downloading ChatGPT support…')
    with urllib.request.urlopen('https://registry.npmjs.org/@openai%2Fcodex/'+VERSION+'-win32-x64',timeout=30) as response: metadata=json.load(response)
    dist=metadata['dist']; integrity=dist['integrity']; algorithm,expected=integrity.split('-',1)
    if algorithm!='sha512': raise ValueError('The official runtime package has an unsupported integrity format')
    with urllib.request.urlopen(dist['tarball'],timeout=180) as response: raw=response.read()
    if not hmac.compare_digest(base64.b64encode(hashlib.sha512(raw).digest()).decode(),expected): raise ValueError('The runtime download did not match its published checksum')
    staging=destination.with_name(destination.name+'-'+str(uuid.uuid4())); staging.mkdir(parents=True)
    progress('Installing ChatGPT support…')
    with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
        for member in archive.getmembers():
            target=(staging/member.name).resolve()
            if not target.is_relative_to(staging.resolve()) or member.issym() or member.islnk(): raise ValueError('Unexpected path in the runtime package')
        archive.extractall(staging,filter='data')
    candidate=staging/'package/vendor/x86_64-pc-windows-msvc/bin/codex.exe'
    if not candidate.is_file(): raise ValueError('The downloaded package contains no Windows runtime')
    destination.parent.mkdir(parents=True,exist_ok=True); os.replace(staging,destination)
    progress('ChatGPT support is ready'); return str(executable)
