# Copyright (c) 2026 KEITER78
"""Read-only application resources and per-user writable setup data."""
import os
from pathlib import Path
import sys

FROZEN = bool(getattr(sys, 'frozen', False))
RESOURCE_ROOT = Path(getattr(sys, '_MEIPASS', Path(__file__).resolve().parent))
SOURCE_ROOT = Path(__file__).resolve().parent
_local = Path(os.environ.get('LOCALAPPDATA') or Path.home() / 'AppData' / 'Local')
DATA_DIR = Path(os.environ.get('LST_DATA_DIR') or _local / 'LiveScreenTranslator').expanduser().resolve()
MODEL_DIR = DATA_DIR / 'models' / 'm2m100-int8'
MODEL_DOWNLOAD_DIR = DATA_DIR / 'models' / 'downloads' / 'm2m100'
TESSDATA_DIR = DATA_DIR / 'models' / 'tessdata'
EASYOCR_MODEL_DIR = DATA_DIR / 'models' / 'easyocr'
EASYOCR_NETWORK_DIR = DATA_DIR / 'models' / 'easyocr-network'


def resource_path(*parts):
    return RESOURCE_ROOT.joinpath(*parts)


def application_settings(organization='KEITER78', application='LiveScreenTranslator'):
    """Keep explicit test/demo profiles separate from the real user registry."""
    from PySide6.QtCore import QSettings
    if os.environ.get('LST_DATA_DIR'):
        folder = DATA_DIR / 'settings'
        folder.mkdir(parents=True, exist_ok=True)
        return QSettings(str(folder / f'{organization}-{application}.ini'), QSettings.IniFormat)
    return QSettings(organization, application)
