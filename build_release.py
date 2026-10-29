# Copyright (c) 2026 KEITER78
"""Build a replaceable-DLL Windows bundle, then package audited release files.

    python build_release.py --build-only
    # Add binary notices and corresponding sources using packaging_licenses.py.
    python build_release.py --package-only

The program never creates a GitHub release or uploads files.
"""
import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import shutil
import struct
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent
APP_NAME = 'LiveScreenTranslator-windows-x64'
PYINSTALLER_VERSION = '6.22.3'
PUBLIC_DOCUMENTS = (
    'LICENSE', 'README.md', 'RIGHTS_AND_ATTRIBUTION.md',
    'THIRD_PARTY_NOTICES.md', 'SUPPORTED_LANGUAGES.md', 'dependency-licenses.json',
    'BINARY_TERMS.md', 'BINARY_DISTRIBUTION.md',
)
APP_SOURCES = (
    'main.py', 'app_window.py', 'app_paths.py', 'setup_dialog.py', 'languages.py',
    'local_translation.py', 'ocr_service.py', 'overlays.py', 'prepare_translation.py',
    'diagnostics.py', 'app_version.py',
    'terms_dialog.py',
)
COMPLIANCE_FILES = ('BINARY_DISTRIBUTION.md', 'SOURCE_OFFER.md', 'BINARY_COMPONENTS.json')
FORBIDDEN_SUFFIXES = {'.pth', '.pt', '.onnx', '.gguf', '.safetensors', '.traineddata', '.reg', '.key', '.log'}


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def checked_output(path):
    path = path.resolve()
    if path == ROOT or not path.is_relative_to(ROOT):
        raise ValueError(f'Build outputs must be in a dedicated directory under {ROOT}.')
    if path.relative_to(ROOT).parts[0] in {'.git', '.venv', 'models', 'third_party_licenses'}:
        raise ValueError('Refusing to use source, model, or interpreter directories as build outputs.')
    return path


def git_state():
    try:
        revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True, stderr=subprocess.DEVNULL).strip()
        dirty = bool(subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True))
        epoch = subprocess.check_output(['git', 'log', '-1', '--format=%ct'], cwd=ROOT, text=True).strip()
        return revision, dirty, epoch
    except (OSError, subprocess.CalledProcessError):
        return None, None, '315532800'


def msvc_redist_files():
    """Use one current x64 CRT family for every copy in the frozen bundle."""
    from build_cpu_backend import vc_environment
    environment = vc_environment()
    redist = Path(environment['VCTOOLSREDISTDIR'])
    files = list(redist.glob('x64/Microsoft.VC*.CRT/*.dll'))
    files += list(redist.glob('x64/Microsoft.VC*.OpenMP/vcomp140.dll'))
    selected = {path.name.lower(): path for path in sorted(files)}
    for name in ('msvcp140.dll', 'vcruntime140.dll', 'vcruntime140_1.dll', 'vcomp140.dll'):
        if name not in selected:
            raise RuntimeError('The current Visual C++ x64 redistributable is incomplete: ' + name)
    return redist.name, selected


def build(dist_dir, work_dir):
    if os.name != 'nt' or struct.calcsize('P') != 8:
        raise RuntimeError('Build the Windows x64 release using 64-bit Python on Windows.')
    if sys.version_info[:3] != (3, 12, 16):
        raise RuntimeError('The release build uses CPython 3.12.16; create its dedicated build environment first.')
    if metadata.version('PyInstaller') != PYINSTALLER_VERSION:
        raise RuntimeError('Install the pinned build dependencies from requirements-build.txt first.')
    required = [ROOT / name for name in APP_SOURCES + PUBLIC_DOCUMENTS]
    required += [ROOT / name for name in (
        'requirements-lock.txt', 'requirements-build.txt', 'LiveScreenTranslator.spec',
        'build_release.py', 'build_cpu_backend.py', 'packaging_licenses.py',
    )]
    missing = [path.name for path in required if not path.is_file()]
    if missing:
        raise RuntimeError('Required build inputs are missing: ' + ', '.join(missing))
    subprocess.run([sys.executable, '-m', 'pip', 'check'], cwd=ROOT, check=True)
    revision, dirty, epoch = git_state()
    environment = dict(os.environ)
    environment.setdefault('SOURCE_DATE_EPOCH', epoch)
    windows_root = Path(os.environ.get('SystemRoot', r'C:\Windows'))
    environment['PATH'] = os.pathsep.join(map(str, (
        Path(sys.executable).parent, Path(sys.base_prefix), Path(sys.base_prefix) / 'DLLs',
        windows_root / 'System32', windows_root,
    )))
    environment['PYTHONNOUSERSITE'] = '1'
    for key in list(environment):
        if key.upper() in {'PYTHONPATH', 'PYTHONHOME', 'PYTHONUSERBASE', 'CUDA_HOME', 'CUDA_ROOT', 'CUDNN_PATH'} or key.upper().startswith('CUDA_PATH'):
            environment.pop(key, None)
    subprocess.run([
        sys.executable, '-m', 'PyInstaller', '--noconfirm',
        '--distpath', str(dist_dir), '--workpath', str(work_dir),
        str(ROOT / 'LiveScreenTranslator.spec'),
    ], cwd=ROOT, env=environment, check=True)
    bundle = dist_dir / APP_NAME
    if not (bundle / 'LiveScreenTranslator.exe').is_file():
        raise RuntimeError('The application executable was not generated.')
    for name in PUBLIC_DOCUMENTS:
        shutil.copy2(ROOT / name, bundle / name)
    shutil.copytree(ROOT / 'third_party_licenses', bundle / 'third_party_licenses', dirs_exist_ok=True)
    build_info = {
        'application': 'LiveScreenTranslator', 'platform': 'windows-x64',
        'version': __import__('app_version').VERSION,
        'python': sys.version.split()[0], 'pyinstaller': PYINSTALLER_VERSION,
        'git_revision': revision, 'source_tree_dirty': dirty,
        'source_sha256': {path.relative_to(ROOT).as_posix(): digest(path) for path in required},
        'bundled_models': False, 'format': 'onedir',
    }
    crt_version, crt_files = msvc_redist_files()
    build_info['msvc_runtime_family'] = crt_version
    build_info['msvc_runtime_sha256'] = {name: digest(path) for name, path in crt_files.items()}
    (bundle / 'BUILD_INFO.json').write_text(json.dumps(build_info, indent=2) + '\n', encoding='utf-8')
    print(f'Built: {bundle}', flush=True)
    return bundle


def check_bundle(bundle):
    if not (bundle / 'LiveScreenTranslator.exe').is_file():
        raise RuntimeError('Build the application first; no executable was found.')
    for name in PUBLIC_DOCUMENTS + COMPLIANCE_FILES + ('BUILD_INFO.json',):
        if not (bundle / name).is_file():
            raise RuntimeError(f'Required release document is missing: {name}')
    if not (bundle / 'licenses').is_dir() or not any((bundle / 'licenses').rglob('*')):
        raise RuntimeError('Assemble binary-component licenses before packaging.')
    files = []
    forbidden = []
    build_info = json.loads((bundle / 'BUILD_INFO.json').read_text(encoding='utf-8'))
    expected_crt = build_info.get('msvc_runtime_sha256', {})
    for path in sorted(bundle.rglob('*')):
        if path.is_symlink():
            raise RuntimeError('Release files must not contain symlinks.')
        if not path.is_file():
            continue
        relative = path.relative_to(bundle)
        if any(part in {'.git', '.venv', '.publish-audit', 'backup', '__pycache__'} for part in relative.parts):
            forbidden.append(relative.as_posix())
        if relative.parts[0] == 'models' or relative.parts[:2] == ('_internal', 'models'):
            forbidden.append(relative.as_posix())
        if path.suffix.lower() in FORBIDDEN_SUFFIXES or path.name.startswith('.env'):
            forbidden.append(relative.as_posix())
        if path.suffix.lower() == '.pem' and relative.as_posix() != '_internal/certifi/cacert.pem':
            forbidden.append(relative.as_posix())
        # This is a general CPU release; vendor GPU redistributables have
        # separate terms and must not accidentally enter the portable bundle.
        if re.match(r'(?:cudnn|cublas|cufft|curand|cusolver|cusparse|nvrtc|nvcuda|cudart).*\.dll$', path.name, re.I):
            forbidden.append(relative.as_posix())
        if path.name.lower().startswith(('qt6pdf', 'qt6qml', 'qt6quick')) and path.suffix.lower() == '.dll':
            forbidden.append(relative.as_posix())
        if path.name.lower() == 'opengl32sw.dll' or path.name.lower().startswith('opencv_videoio_ffmpeg'):
            forbidden.append(relative.as_posix())
        if path.name.lower().startswith(('api-ms-win-', 'ext-ms-win-')) or path.name.lower() in {'ucrtbase.dll', 'ucrtbased.dll'}:
            forbidden.append(relative.as_posix())
        if path.name.lower() in expected_crt and digest(path) != expected_crt[path.name.lower()]:
            raise RuntimeError('A stale Visual C++ runtime entered the bundle: ' + relative.as_posix())
        files.append(path)
    if forbidden:
        raise RuntimeError('Private or model files found in bundle: ' + ', '.join(sorted(set(forbidden))))
    return files


def package(dist_dir, release_dir, source_archive):
    bundle = dist_dir / APP_NAME
    files = check_bundle(bundle)
    if not source_archive.is_file() or source_archive.stat().st_size == 0:
        raise RuntimeError('Create the corresponding-sources ZIP before packaging the application.')
    release_dir.mkdir(parents=True, exist_ok=True)
    archive = release_dir / f'{APP_NAME}.zip'
    temporary = archive.with_suffix('.zip.part')
    with zipfile.ZipFile(temporary, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as output:
        for path in files:
            info = zipfile.ZipInfo((Path(APP_NAME) / path.relative_to(bundle)).as_posix(), (1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (0o100644 << 16)
            with path.open('rb') as source, output.open(info, 'w', force_zip64=True) as destination:
                shutil.copyfileobj(source, destination, length=4 * 1024 * 1024)
    if temporary.stat().st_size >= 2 * 1024 ** 3:
        raise RuntimeError('The archive exceeds GitHub Releases single-file size limits.')
    temporary.replace(archive)
    checksum = digest(archive)
    archive.with_suffix('.zip.sha256').write_text(f'{checksum}  {archive.name}\n', encoding='ascii')
    report = {
        'archive': archive.name, 'sha256': checksum, 'bytes': archive.stat().st_size,
        'bundled_files': len(files), 'bundled_models': False,
        'corresponding_sources': source_archive.name,
        'corresponding_sources_sha256': digest(source_archive),
    }
    (release_dir / 'release-manifest.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)
    return archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument('--build-only', action='store_true', help='Build the onedir application without creating a ZIP.')
    mode.add_argument('--package-only', action='store_true', help='ZIP an existing bundle after compliance resources have been added.')
    parser.add_argument('--dist-dir', type=Path, default=ROOT / 'dist')
    parser.add_argument('--work-dir', type=Path, default=ROOT / 'build' / 'PyInstaller')
    parser.add_argument('--release-dir', type=Path, default=ROOT / 'release')
    parser.add_argument('--source-archive', type=Path)
    args = parser.parse_args()
    dist_dir, work_dir, release_dir = map(checked_output, (args.dist_dir, args.work_dir, args.release_dir))
    source_archive = args.source_archive.resolve() if args.source_archive else release_dir / 'LiveScreenTranslator-corresponding-sources.zip'
    if not args.package_only:
        build(dist_dir, work_dir)
    if not args.build_only:
        package(dist_dir, release_dir, source_archive)


if __name__ == '__main__':
    main()
