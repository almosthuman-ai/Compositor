"""Fetch pinned encoder sources; all build products stay under windows/local."""
from pathlib import Path
import hashlib, json, subprocess, tarfile, urllib.request

here = Path(__file__).resolve().parent
root = here.parent / 'local' / 'encoder'
root.mkdir(parents=True, exist_ok=True)
sources = json.loads((here / 'sources.json').read_text())
for source in sources:
    archive = root / source['file']
    if 'url' in source:
        if not archive.exists():
            with urllib.request.urlopen(source['url']) as response:
                archive.write_bytes(response.read())
        if hashlib.sha256(archive.read_bytes()).hexdigest() != source['sha256']:
            raise RuntimeError(f"Source checksum mismatch: {archive}")
        directory = root / source['file'].split('.tar')[0]
    else:
        directory = root / 'x264'
        if not (directory / '.git').exists():
            if directory.exists():
                raise RuntimeError('Use a fresh build directory; x264 sources without Git metadata already exist.')
            subprocess.run(['git', 'init', str(directory)], check=True)
            subprocess.run(['git', 'remote', 'add', 'origin', source['repository']], cwd=directory, check=True)
        subprocess.run(['git', 'config', 'core.autocrlf', 'false'], cwd=directory, check=True)
        subprocess.run(['git', 'fetch', '--depth', '1', 'origin', source['commit']], cwd=directory, check=True)
        subprocess.run(['git', 'checkout', '--detach', source['commit']], cwd=directory, check=True)
        subprocess.run(['git', 'archive', '--format=tar', '--prefix=x264/', '-o', str(archive), source['commit']], cwd=directory, check=True)
    if not directory.exists():
        with tarfile.open(archive) as bundle:
            bundle.extractall(root, filter='data')
    print(source['file'], flush=True)
