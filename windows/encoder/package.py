"""Pair the actual executable with complete sources and its build instructions."""
from pathlib import Path
import hashlib, json, shutil, zipfile

here = Path(__file__).resolve().parent
root = here.parent / 'local' / 'encoder'
output = root / 'output'
sources = json.loads((here / 'sources.json').read_text())
inputs = [here / name for name in ('sources.json', 'prepare.py', 'build.sh', 'package.py', 'README.md')]
archives = [root / source['file'] for source in sources]
for path in inputs + archives + [output / name for name in ('compositor-encoder.exe', 'toolchain.txt', 'version.txt', 'imports.txt')]:
    if not path.is_file():
        raise RuntimeError(f'Build the encoder first: missing {path}')
with zipfile.ZipFile(output / 'encoder-sources.zip', 'w', zipfile.ZIP_DEFLATED) as bundle:
    for path in inputs:
        bundle.write(path, 'windows/encoder/' + path.name)
    for path in archives:
        bundle.write(path, 'windows/local/encoder/' + path.name)
    for name in ('toolchain.txt', 'version.txt', 'imports.txt'):
        bundle.write(output / name, 'build-record/' + name)
licenses = output / 'licenses'
licenses.mkdir(exist_ok=True)
for source, name in [('ffmpeg-7.1/COPYING.GPLv2', 'FFmpeg-GPLv2.txt'), ('x264/COPYING', 'x264-GPLv2.txt'), ('zlib-1.3.1/README', 'zlib.txt')]:
    shutil.copyfile(root / source, licenses / name)
shutil.copyfile(here / 'README.md', output / 'README.md')
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
manifest = {'sources': sources, 'inputs': {p.name: digest(p) for p in inputs},
            'files': {p.name: digest(p) for p in (output / 'compositor-encoder.exe', output / 'encoder-sources.zip')}}
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(output)
