"""Package the built Windows app as a per-user installer and a portable ZIP."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess, urllib.request, zipfile
from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
NSIS_URL = 'https://downloads.sourceforge.net/project/nsis/NSIS%203/3.12/nsis-3.12.zip'
NSIS_SHA256 = '56581f90db321581c5381193d796fffcf2d24b2f8fed2160a6c6a3baa67f2c4f'


def digest(path):
    with path.open('rb') as source:
        return hashlib.file_digest(source, 'sha256').hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, default=ROOT/'dist/Compositor')
    parser.add_argument('--version', default='0.1.0-preview.1')
    args = parser.parse_args()
    if not re.fullmatch(r'[0-9A-Za-z.-]+', args.version):
        raise ValueError('Use a version containing letters, numbers, dots and hyphens.')
    source = args.source.resolve()
    for name in ('Compositor.exe', 'Compositor-Tools.exe', 'LICENSE.txt', 'THIRD_PARTY_NOTICES.md', '_internal/encoder/encoder-sources.zip'):
        if not (source/name).is_file():
            raise ValueError(f'Build the complete application first: missing {name}')
    encoder = source/'_internal/encoder'
    manifest = json.loads((encoder/'manifest.json').read_text(encoding='utf-8'))
    for name, expected in manifest['files'].items():
        if digest(encoder/name) != expected:
            raise ValueError(f'Encoder package differs from its manifest: {name}')
    tools = ROOT/'windows/local/packaging-tools'
    tools.mkdir(parents=True, exist_ok=True)
    archive = tools/'nsis-3.12.zip'
    if not archive.exists():
        with urllib.request.urlopen(NSIS_URL) as response, archive.open('wb') as output:
            shutil.copyfileobj(response, output)
    if digest(archive) != NSIS_SHA256:
        raise ValueError('NSIS download checksum differs from the published archive.')
    compiler = tools/'nsis-3.12/makensis.exe'
    if not compiler.exists():
        with zipfile.ZipFile(archive) as bundle:
            bundle.extractall(tools)
    output = ROOT/'dist/releases'
    output.mkdir(parents=True, exist_ok=True)
    stem = f'Compositor-{args.version}-Windows-x64'
    installer, portable = output/(stem+'-Setup.exe'), output/(stem+'-Portable.zip')
    icon = tools/'Compositor.ico'
    with Image.open(ROOT/'Compositor/Assets.xcassets/AppIcon.appiconset/app-icon-256.png') as image:
        image.save(icon, format='ICO', sizes=[(16,16),(32,32),(48,48),(64,64),(128,128),(256,256)])
    files = sorted(p for p in source.rglob('*') if p.is_file())
    def nsis_path(path):
        return str(path.relative_to(source)).replace('/', '\\').replace('$', '$$').replace('"', '$\\"')
    removal = tools/'remove-files.nsh'
    lines = [f'Delete "$INSTDIR\\{nsis_path(path)}"' for path in files]
    directories = sorted((p for p in source.rglob('*') if p.is_dir()), key=lambda p:len(p.parts), reverse=True)
    lines.extend(f'RMDir "$INSTDIR\\{nsis_path(path)}"' for path in directories)
    removal.write_text('\n'.join(lines)+'\n', encoding='utf-8')
    subprocess.run([str(compiler), '/V2', '/INPUTCHARSET', 'UTF8', f'/DAPP_VERSION={args.version}',
                    f'/DPAYLOAD={source}', f'/DOUTPUT={installer}', f'/DAPP_ICON={icon}',
                    f'/DREMOVE_FILES={removal}', f'/DQUICK_START={ROOT/"windows/QUICK_START.md"}',
                    str(ROOT/'windows/installer.nsi')], check=True)
    with zipfile.ZipFile(portable, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as bundle:
        for path in files:
            bundle.write(path, 'Compositor/'+path.relative_to(source).as_posix())
        bundle.write(ROOT/'windows/QUICK_START.md', 'Compositor/START-HERE.md')
    hashes = {path.name:digest(path) for path in (installer, portable)}
    (output/'SHA256SUMS.txt').write_text(''.join(f'{value}  {name}\n' for name,value in hashes.items()), encoding='utf-8')
    print(json.dumps({'version':args.version, 'files':hashes, 'directory':str(output)}, indent=2))


if __name__ == '__main__':
    main()
