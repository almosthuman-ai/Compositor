import os, sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')

# A closed Qt window is hidden, not destroyed. Dispose each test's widgets on
# the Qt thread, before cyclic Python collection can tear down an old widget
# tree during a later test's native paint event.
import pytest
@pytest.fixture(autouse=True)
def dispose_test_widgets():
    yield
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QCoreApplication,QEvent
    application=QApplication.instance()
    if application:
        for widget in application.topLevelWidgets(): widget.hide(); widget.deleteLater()
        QCoreApplication.sendPostedEvents(None,QEvent.Type.DeferredDelete)
    import gc
    gc.collect()
