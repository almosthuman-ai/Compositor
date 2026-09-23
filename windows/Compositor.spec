from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH).parent
datas = [(str(root/'windows/compositor/prompts'), 'compositor/prompts')]
datas.append((str(root/'windows/compositor/glitch_assets'),'compositor/glitch_assets'))
upstream_icons = root/'Compositor/Assets.xcassets/AppIcon.appiconset'
datas.append((str(upstream_icons/'app-icon-256.png'), 'compositor/assets'))
binaries = []
hiddenimports = ['keyring.backends.Windows', 'mcp.server.mcpserver']
extra = collect_all('pillow_heif')
ffmpeg = collect_all('imageio_ffmpeg')
datas += ffmpeg[0]
binaries += ffmpeg[1]
hiddenimports += ffmpeg[2]
datas += extra[0]
binaries += extra[1]
hiddenimports += extra[2]
a = Analysis([str(root/'windows/run.py')], pathex=[str(root/'windows')], binaries=binaries,
             datas=datas, hiddenimports=hiddenimports, excludes=[], noarchive=False)
pyz = PYZ(a.pure)
gui = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Compositor', console=False, icon=str(upstream_icons/'app-icon-512.png'))
operator = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Compositor-Tools', console=True, icon=str(upstream_icons/'app-icon-512.png'))
distribution = COLLECT(gui, operator, a.binaries, a.datas, name='Compositor')
