from pathlib import Path
import os, sys
sys.path.insert(0,str(Path(__file__).resolve().parent))

def main():
    if '--mcp' in sys.argv:
        from compositor.mcp_server import server
        server.run(); return
    # Other Qt applications may set plugin paths for a different Qt build.
    for key in ('QT_PLUGIN_PATH','QT_QPA_PLATFORM_PLUGIN_PATH','QML2_IMPORT_PATH'):
        os.environ.pop(key,None)
    from PySide6.QtWidgets import QApplication, QMessageBox
    from PySide6.QtCore import QTimer, QLockFile, Qt
    from compositor.settings import Settings
    from compositor.workspace import Workspace
    from compositor.server import start_server
    from compositor.ui import Editor
    import pillow_heif
    pillow_heif.register_heif_opener()
    app=QApplication(sys.argv); app.setApplicationName('Compositor'); app.setOrganizationName('Compositor')
    settings=Settings(); lock=QLockFile(str(settings.root/'editor.lock')); lock.setStaleLockTime(0)
    if not lock.tryLock(0):
        from compositor.mcp_server import call
        try:
            for path in sys.argv[1:]:
                if not path.startswith('--'): call('open',{'path':str(Path(path).resolve())})
            if '--background' not in sys.argv: call('show')
        except Exception as e: QMessageBox.warning(None,'Compositor',str(e))
        return
    ws=Workspace(settings)
    try: server=start_server(ws)
    except OSError:
        QMessageBox.information(None,'Compositor','Compositor is already running, or its local operator port is in use.'); return
    window=Editor(ws)
    paths=[p for p in sys.argv[1:] if not p.startswith('--')]
    if paths:
        for path in paths: window.run('open',{'path':path})
    if not ws.documents: ws.dispatch('new',{'title':'Untitled','width':1536,'height':1024})
    if '--background' in sys.argv: window.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
    window.show(); QTimer.singleShot(100,window.canvas.fit)
    result=app.exec(); server.shutdown(); ws.generation.pool.shutdown(wait=False); sys.exit(result)

if __name__=='__main__': main()
