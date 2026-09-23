"""The separately built, source-accompanied animation encoder."""
from pathlib import Path
import sys


def executable():
    if getattr(sys, 'frozen', False):
        path = Path(sys._MEIPASS) / 'encoder' / 'compositor-encoder.exe'
    else:
        path = Path(__file__).resolve().parents[1] / 'local' / 'encoder' / 'output' / 'compositor-encoder.exe'
    if not path.is_file():
        raise ValueError('The animation encoder is missing. Reinstall Compositor; source developers can run windows/encoder/prepare.py and build.sh.')
    return path
