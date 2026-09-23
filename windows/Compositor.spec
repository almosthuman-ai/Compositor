from pathlib import Path
from PyInstaller.utils.hooks import collect_all

root = Path(SPECPATH).parent
datas = [(str(root/'windows/compositor/prompts'), 'compositor/prompts')]
binaries = []
hiddenimports = ['keyring.backends.Windows', 'mcp.server.mcpserver']
extra = collect_all('pillow_heif')
datas += extra[0]
binaries += extra[1]
hiddenimports += extra[2]
a = Analysis([str(root/'windows/run.py')], pathex=[str(root/'windows')], binaries=binaries,
             datas=datas, hiddenimports=hiddenimports, excludes=[], noarchive=False)
pyz = PYZ(a.pure)
gui = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Compositor', console=False)
operator = EXE(pyz, a.scripts, [], exclude_binaries=True, name='Compositor-Tools', console=True)
distribution = COLLECT(gui, operator, a.binaries, a.datas, name='Compositor')
