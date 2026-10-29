# -*- mode: python ; coding: utf-8 -*-
# Copyright (c) 2026 KEITER78
"""Windowed, one-directory build; downloaded models are deliberately excluded."""
from pathlib import Path
import re
from xml.dom.minidom import parseString

from PyInstaller.utils.hooks import (
    collect_data_files, collect_dynamic_libs, collect_submodules, copy_metadata,
    get_package_paths,
)
from build_release import msvc_redist_files
from PyInstaller.utils.win32.winmanifest import create_application_manifest

ROOT = Path(SPECPATH).resolve()
APP_NAME = 'LiveScreenTranslator-windows-x64'
PUBLIC_DOCUMENTS = (
    'LICENSE', 'README.md', 'RIGHTS_AND_ATTRIBUTION.md',
    'THIRD_PARTY_NOTICES.md', 'SUPPORTED_LANGUAGES.md', 'dependency-licenses.json',
    'BINARY_TERMS.md', 'BINARY_DISTRIBUTION.md',
)
datas = [(str(ROOT / name), '.') for name in PUBLIC_DOCUMENTS]
datas.append((str(ROOT / 'third_party_licenses'), 'third_party_licenses'))

# EasyOCR loads its character lists and recognition networks dynamically.
datas += collect_data_files('easyocr', excludes=['DBNet/**'])
datas += collect_data_files('transformers')
datas += collect_data_files('ctranslate2')
hiddenimports = collect_submodules('easyocr.model')
hiddenimports += collect_submodules('ctranslate2')
hiddenimports += collect_submodules('transformers.models.m2m_100')
hiddenimports += [
    'PySide6.QtCore', 'PySide6.QtGui', 'PySide6.QtWidgets',
    'transformers.models.auto.configuration_auto',
    'transformers.models.auto.modeling_auto',
    'transformers.models.auto.tokenization_auto',
    'transformers.generation.utils',
    'sentencepiece', 'torch', 'torchvision', 'torchvision.ops',
    'PIL.Image', 'PIL.ImageGrab', 'PIL.ImageOps',
]
_, crt_files = msvc_redist_files()
binaries = [(str(path), '.') for path in crt_files.values()]
binaries += collect_dynamic_libs('ctranslate2')

# Transformers checks installed-distribution metadata even in a frozen app.
for line in (ROOT / 'requirements-lock.txt').read_text(encoding='utf-8').splitlines():
    if '==' in line and not line.lstrip().startswith('#'):
        datas += copy_metadata(line.split('==', 1)[0].strip())

qt_root = Path(get_package_paths('PySide6')[1])
qt_modules = {'QtCore', 'QtGui', 'QtWidgets'}
unused_qt_bindings = sorted([
    'PySide6.' + path.stem for path in qt_root.glob('Qt*.pyi')
    if path.stem not in qt_modules
])
excludes = sorted(set(unused_qt_bindings + [
    'PyQt5', 'PyQt6', 'PySide2', 'tkinter', '_tkinter',
    'tensorflow', 'keras', 'jax', 'jaxlib', 'flax',
    'matplotlib', 'pandas', 'IPython', 'jupyter', 'notebook',
    'pytest', 'PIL._imagingft', 'easyocr.DBNet', 'easyocr.detection_db',
]))

a = Analysis(
    [str(ROOT / 'main.py')], pathex=[str(ROOT)], binaries=binaries,
    datas=datas, hiddenimports=hiddenimports, hookspath=[], hooksconfig={},
    runtime_hooks=[], excludes=excludes, noarchive=False,
)

# Keep only the Qt modules/plugins needed for a widgets-only desktop app.
# In particular QtPdf and the OpenCV FFmpeg plugin are not used by OCR.
qt_dlls = {
    'qt6core.dll', 'qt6gui.dll', 'qt6widgets.dll',
    'qt6opengl.dll', 'qt6svg.dll',
}
qt_plugins = {
    'qwindows.dll', 'qoffscreen.dll', 'qminimal.dll',
    'qwindowsvistastyle.dll', 'qmodernwindowsstyle.dll',
    'qgif.dll', 'qico.dll', 'qjpeg.dll', 'qsvg.dll', 'qtiff.dll', 'qwebp.dll',
    'qsvgicon.dll',
}


def keep_binary(entry):
    destination = entry[0].replace('\\', '/').lower()
    filename = destination.rsplit('/', 1)[-1]
    if filename.startswith(('api-ms-win-', 'ext-ms-win-')) or filename in {'ucrtbase.dll', 'ucrtbased.dll'}:
        return False
    if re.match(r'(?:cudnn|cublas|cufft|curand|cusolver|cusparse|nvrtc|nvcuda|cudart).*\.dll$', filename):
        return False
    if filename.startswith('opencv_videoio_ffmpeg'):
        return False
    if filename == 'opengl32sw.dll':
        return False
    if destination.startswith('pyside6/'):
        if filename.startswith('qt6') and filename.endswith('.dll'):
            return filename in qt_dlls
        if '/plugins/' in destination and filename.endswith('.dll'):
            return filename in qt_plugins
    return True


a.binaries = [entry for entry in a.binaries if keep_binary(entry)]
# Qt, Python and Torch can carry older CRT copies in separate directories.
# Replace all of them with the same redistributable used by our CPU compiler.
a.binaries = [
    (destination, str(crt_files[Path(destination).name.lower()]), kind)
    if Path(destination).name.lower() in crt_files else (destination, source, kind)
    for destination, source, kind in a.binaries
]
# Never publish build-machine paths from pip's direct-install metadata.
a.datas = [entry for entry in a.datas
           if not entry[0].replace('\\', '/').endswith('/direct_url.json')]

manifest = parseString(create_application_manifest())
code_page = manifest.createElement('activeCodePage')
code_page.setAttribute('xmlns', 'http://schemas.microsoft.com/SMI/2019/WindowsSettings')
code_page.appendChild(manifest.createTextNode('UTF-8'))
manifest.getElementsByTagName('windowsSettings')[0].appendChild(code_page)

pyz = PYZ(a.pure)
exe = EXE(
    pyz, a.scripts, [], exclude_binaries=True,
    name='LiveScreenTranslator', debug=False, bootloader_ignore_signals=False,
    strip=False, upx=False, console=False, disable_windowed_traceback=False,
    contents_directory='_internal',
    manifest=manifest.toxml(),
)
collection = COLLECT(
    exe, a.binaries, a.datas, strip=False, upx=False, name=APP_NAME,
)
