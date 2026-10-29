# Copyright (c) 2026 KEITER78
"""Prepare notices, exact-source archives and a manifest for a Windows release."""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
from urllib.parse import quote
import zipfile


ROOT = Path(__file__).resolve().parent
SOURCE_ASSET = 'LiveScreenTranslator-corresponding-sources.zip'
PUBLIC_EXTRAS = {'BINARY_DISTRIBUTION.md', 'BINARY_TERMS.md', 'SOURCE_OFFER.md'}
QT_BASE_DLLS = {'core', 'gui', 'widgets', 'opengl', 'openglwidgets', 'concurrent',
                'network', 'printsupport', 'sql', 'dbus', 'xml', 'test'}
QT_EXTRA_DLLS = {'svg', 'svgwidgets'}
NOTICE_NAME = re.compile(r'licen[cs]e|copying|notice|copyright|authors|third[-_]party|redist', re.I)
FORBIDDEN_NATIVE = re.compile(r'^(?:cudnn|cublas|cudart|nvcuda|nvrtc|torch_cuda|opencv_videoio_ffmpeg)', re.I)


def digest(path: Path) -> str:
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def git(*args: str) -> bytes:
    return subprocess.check_output(['git', *args], cwd=ROOT)


def notice_file(path: Path) -> bool:
    return (bool(NOTICE_NAME.search(path.name)) or any(part.lower() in {'licenses', 'licences'} for part in path.parts)) and path.suffix.lower() not in {
        '.py', '.pyc', '.dll', '.pyd', '.exe', '.so'}


def safe_name(value: str) -> str:
    return re.sub(r'[^A-Za-z0-9_.-]', '-', value)


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.part')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def download(spec: dict, cache: Path) -> Path:
    target = cache / spec['filename']
    if target.is_file() and digest(target) == spec['sha256']:
        return target
    import requests
    session = requests.Session()
    session.trust_env = False
    print(f"対応ソースを取得: {spec['filename']}", flush=True)
    response = session.get(spec['url'], stream=True, timeout=(20, 180))
    response.raise_for_status()
    partial = target.with_name(target.name + '.part')
    with partial.open('wb') as stream:
        for block in response.iter_content(1024 * 1024):
            stream.write(block)
    if digest(partial) != spec['sha256']:
        raise RuntimeError(f"対応ソースのSHA-256が一致しません: {spec['filename']}")
    partial.replace(target)
    return target


def inspect_bundle(bundle: Path) -> list[dict]:
    if not (bundle / 'LiveScreenTranslator.exe').is_file():
        raise RuntimeError('ビルド済みのonedir版LiveScreenTranslator.exeが見つかりません。')
    inventory = []
    qt_modules = set()
    for path in sorted(bundle.rglob('*')):
        if not path.is_file() or path.suffix.lower() not in {'.dll', '.pyd', '.exe'}:
            continue
        relative = path.relative_to(bundle).as_posix()
        if FORBIDDEN_NATIVE.match(path.name):
            raise RuntimeError(f'CPU版の配布対象外のライブラリが含まれています: {relative}')
        if path.name.lower().startswith('qt6') and path.suffix.lower() == '.dll':
            module = path.stem[3:].lower()
            if module not in QT_BASE_DLLS | QT_EXTRA_DLLS:
                raise RuntimeError(f'対応ソースを定義していないQtモジュールです: {relative}')
            qt_modules.add(module)
        inventory.append({'path': relative, 'bytes': path.stat().st_size, 'sha256': digest(path)})
    if not {'core', 'gui', 'widgets'}.issubset(qt_modules):
        raise RuntimeError('QtCore・QtGui・QtWidgetsの動的ライブラリが不足しています。')
    if not any('python312' in item['path'].lower() for item in inventory):
        raise RuntimeError('このリリースは検証済みのPython 3.12版を対象にします。')
    for path in bundle.rglob('*'):
        if path.is_file() and path.suffix.lower() in {'.ttf', '.otf', '.woff', '.woff2'}:
            raise RuntimeError(f'再配布を確認していないフォントが含まれています: {path.name}')
    openmp_provenance = json.loads((ROOT / 'third_party_licenses/intel-openmp-2025.2.0/PROVENANCE.json').read_text(encoding='utf-8'))
    openmp = [item for item in inventory if Path(item['path']).name.lower() == 'libiomp5md.dll']
    if not openmp or any(item['sha256'] != openmp_provenance['torch_dll_sha256'] for item in openmp):
        raise RuntimeError('PyTorchのIntel OpenMP DLLが確認済みの原配布物と一致しません。')
    return inventory


def microsoft_runtime(bundle: Path, inventory: list[dict]) -> dict:
    build = json.loads((bundle / 'BUILD_INFO.json').read_text(encoding='utf-8'))
    expected = build.get('msvc_runtime_sha256', {})
    if not expected or not build.get('msvc_runtime_family'):
        raise RuntimeError('Microsoftランタイムの配布元情報がありません。')
    for name, sha256 in expected.items():
        copies = [item for item in inventory if Path(item['path']).name.lower() == name.lower()]
        if not copies or any(item['sha256'] != sha256 for item in copies):
            raise RuntimeError(f'Microsoftランタイムの原配布物と一致しません: {name}')
    return {'origin': 'Visual Studio 2026 / VC x64 redistributable',
            'family': build['msvc_runtime_family'], 'sha256': expected,
            'license': 'third_party_licenses/microsoft-vc-runtime/VISUAL_STUDIO_2026_COMMUNITY_TERMS.txt',
            'redistribution_list': 'third_party_licenses/microsoft-vc-runtime/VISUAL_STUDIO_2026_REDISTRIBUTION.html'}


def collect_notices(bundle: Path, runtime: Path, source_specs: list[dict], cache: Path) -> list[dict]:
    destination = bundle / 'licenses'
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(ROOT / 'third_party_licenses', destination / 'third_party', dirs_exist_ok=True)
    shutil.copytree(ROOT / 'third_party_licenses', bundle / 'third_party_licenses', dirs_exist_ok=True)
    python_notice = runtime / 'LICENSE.txt'
    if not python_notice.is_file():
        raise RuntimeError('実際にビルドに使ったPythonのLICENSE.txtがありません。')
    (destination / 'python').mkdir(exist_ok=True)
    shutil.copy2(python_notice, destination / 'python' / 'LICENSE.txt')
    packages = []
    for distribution in sorted(importlib.metadata.distributions(), key=lambda dist: dist.metadata['Name'].lower()):
        name = distribution.metadata['Name']
        copied = []
        for relative in distribution.files or []:
            relative_path = Path(relative)
            if relative_path.is_absolute() or not notice_file(relative_path):
                continue
            source = Path(distribution.locate_file(relative)).resolve()
            if not source.is_file():
                continue
            # Wheel RECORD entries may locate notices under share/doc using
            # ../../ paths. Only accept files inside this actual build environment.
            prefix = Path(sys.prefix).resolve()
            if not source.is_relative_to(prefix):
                raise RuntimeError(f'ビルド環境外のライセンスファイルです: {name}')
            target_relative = (Path('environment') / source.relative_to(prefix)
                               if '..' in relative_path.parts else relative_path)
            target = destination / 'installed' / safe_name(name) / target_relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            copied.append(target.relative_to(bundle).as_posix())
        summary = distribution.metadata.get('License-Expression')
        if not summary:
            summary = (distribution.metadata.get('License') or '').splitlines()[0:1]
            summary = summary[0][:200] if summary else ''
        packages.append({'name': name, 'version': distribution.version,
                         'declared_license': summary, 'notice_files': copied})
    # Keep the copyright and license texts of Qt's compiled third-party code,
    # plus the Rust dependencies linked into python-bidi.
    for spec in source_specs:
        if spec['component'] not in {'qtbase', 'qtsvg', 'qtimageformats', 'pyside-setup', 'ctranslate2-cpu-source', 'eigen'} and not spec['component'].startswith('rust-'):
            continue
        with tarfile.open(cache / spec['filename'], mode='r|*') as archive:
            for member in archive:
                source_name = Path(member.name)
                if not member.isfile() or not (notice_file(source_name)
                        or source_name.name == 'qt_attribution.json'
                        or source_name.name.upper() in {'FTL.TXT', 'OFL.TXT', 'README.IJG', 'LEGAL'}):
                    continue
                source = archive.extractfile(member)
                if source is None:
                    continue
                relative = Path(*Path(member.name).parts[1:])
                if '..' in relative.parts or relative.is_absolute():
                    raise RuntimeError('不正なRustソースのパスです。')
                target = destination / 'upstream' / spec['component'] / spec['version'] / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(source.read())
    if not any(item['name'].lower() == 'pyinstaller' and item['notice_files'] for item in packages):
        raise RuntimeError('PyInstallerの原文・ブートローダー例外を収集できませんでした。')
    if not any(item['name'].lower().replace('_', '-') == 'mkl-static' and item['notice_files'] for item in packages):
        raise RuntimeError('CPUバックエンドにリンクしたMKLの原文がありません。')
    return packages


def snapshot_cpu_backend(source: Path, cache: Path) -> dict:
    if not (source / 'CMakeLists.txt').is_file():
        raise RuntimeError('実際のCPUバックエンドのソースチェックアウトがありません。')
    revision = subprocess.check_output(['git', '-C', str(source), 'rev-parse', 'HEAD'], text=True).strip()
    if revision != '617405f4b050e994e829d527da6caa0e0030afe7':
        raise RuntimeError('CTranslate2の上流リビジョンが確認済みのv4.6.0と異なります。')
    names = subprocess.check_output(['git', '-C', str(source), 'ls-files', '--recurse-submodules', '-z']).decode('utf-8').split('\0')
    target = cache / 'CTranslate2-4.6.0-cpu-source.tar.gz'
    temporary = target.with_name(target.name + '.part')
    with tarfile.open(temporary, mode='w:gz', compresslevel=4) as archive:
        for relative in sorted(names):
            if not relative:
                continue
            path = (source / relative).resolve()
            if not path.is_relative_to(source) or not path.is_file():
                continue
            archive.add(path, arcname='CTranslate2-4.6.0-cpu/' + relative, recursive=False)
    if not (source / 'src/cpu/vec.h').is_file():
        raise RuntimeError('Eigen由来の演算実装を含むCPUバックエンドのソースがありません。')
    temporary.replace(target)
    return {'component': 'ctranslate2-cpu-source', 'version': '4.6.0+cpu',
            'license': 'MIT AND MPL-2.0 AND upstream third-party licenses',
            'filename': target.name, 'url': 'https://github.com/OpenNMT/CTranslate2/tree/' + revision,
            'upstream_revision': revision, 'sha256': digest(target), 'bytes': target.stat().st_size,
            'modifications': 'CPU-only build; packaging and version changes reproduced by application/build_cpu_backend.py. Includes exact recursive submodule source and Eigen-derived src/cpu/vec.h; original Eigen 3.4.0 source is supplied separately.'}


def public_source_files() -> list[Path]:
    paths = git('ls-files', '--cached', '--others', '--exclude-standard', '-z').decode('utf-8').split('\0')
    paths += list(PUBLIC_EXTRAS)
    result = set()
    for relative in paths:
        if not relative:
            continue
        path = (ROOT / relative).resolve()
        if not path.is_relative_to(ROOT) or not path.is_file():
            continue
        parts = path.relative_to(ROOT).parts
        if any(part in {'.git', '.publish-audit', '.venv', 'models', 'release', 'dist', 'build', 'backup'} for part in parts):
            continue
        if path.suffix.lower() in {'.exe', '.dll', '.pyd', '.log', '.ini', '.reg', '.key', '.pem', '.zip'}:
            continue
        result.add(path)
    return sorted(result)


VENDOR_HELPER = '''"""Create an offline Cargo vendor tree from the supplied exact crate archives."""
import hashlib, json, pathlib, sys, tarfile, tomllib
source, archives = map(pathlib.Path, sys.argv[1:3])
lock = tomllib.loads((source / 'Cargo.lock').read_text(encoding='utf-8'))
vendor = source / 'vendor'
vendor.mkdir(exist_ok=True)
for package in lock['package']:
    if not package.get('source', '').startswith('registry+'):
        continue
    name = f"{package['name']}-{package['version']}"
    archive = archives / (name + '.crate')
    assert hashlib.sha256(archive.read_bytes()).hexdigest() == package['checksum']
    with tarfile.open(archive) as stream:
        for member in stream.getmembers():
            if member.isdir():
                continue
            assert member.isfile() and pathlib.PurePosixPath(member.name).parts[0] == name
            target = vendor.joinpath(*pathlib.PurePosixPath(member.name).parts)
            assert target.resolve().is_relative_to(vendor.resolve())
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(stream.extractfile(member).read())
    directory = vendor / name
    files = {path.relative_to(directory).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
             for path in directory.rglob('*') if path.is_file() and path.name != '.cargo-checksum.json'}
    (directory / '.cargo-checksum.json').write_text(json.dumps({'package': package['checksum'], 'files': files}))
(source / '.cargo').mkdir(exist_ok=True)
(source / '.cargo' / 'config.toml').write_text('[source.crates-io]\\nreplace-with = "vendored-sources"\\n[source.vendored-sources]\\ndirectory = "vendor"\\n')
print('Offline Cargo source tree prepared:', source)
'''


REBUILD_GUIDE = '''# 対応ソースとライブラリの差し替え

`application/` はこのバイナリの作成時点の本体ソース・ビルドスクリプトです。
`upstream/` に版とSHA-256を固定した上流ソースを、`SOURCE_COMPONENTS.json` に取得元とハッシュを収録します。
出版社から取得したリリースアーカイブは原形を保持します。CPUバックエンドのソーススナップショットには
`build_cpu_backend.py` が再現するCMake・パッケージ構成の変更を含みます。
ビルドに必要なコンパイラ・SDKは通常の開発ツールとして別途用意します。

## 本体の再ビルド

Windows x64、Python 3.12、Visual StudioのC++ビルドツールを使用します。
`application/requirements-lock.txt` とビルド用依存を専用環境に導入し、同梱の
`build_cpu_backend.py`、`build_release.py` の手順でCPUバックエンドとonedir版を作成します。
独自に変更したLGPLライブラリをビルド環境へ先にインストールすると、同じ本体ソースから改変ライブラリを使う版を作れます。

## Qt / PySide6 / shiboken6（LGPLv3）

Qt 6.9.2のqtbase、qtsvg、qtimageformats、およびPySide6 / shiboken6 6.9.2の
完全なリリースソースとCMake・setup.py等のビルドスクリプトを提供します。
Qtは共有ライブラリとしてビルドします。qtbaseをVisual Studioのx64開発用シェルから
`cmake -S <qtbase-source> -B <qtbase-build> -G Ninja -DCMAKE_BUILD_TYPE=Release -DQT_BUILD_TESTS=OFF -DQT_BUILD_EXAMPLES=OFF -DCMAKE_INSTALL_PREFIX=<qt-install>`
で構成し、`cmake --build <qtbase-build>` と `cmake --install <qtbase-build>` を実行します。
qtsvg / qtimageformatsはそのQtをCMAKE_PREFIX_PATHに指定して同様にビルドします。
PySide6ソース付属のREADMEおよびビルド手順を使い、そのQtのqtpaths.exeを指定して
PySide6 / shiboken6をビルドします。Python ABIとQtのメジャー版を合わせてください。
配布フォルダーの `_internal/PySide6/` 等にある同名DLL・pyd・プラグインは置き換え可能です。
完全なフォルダー構造とDLL間のABI整合性を維持してください。本体には署名照合による差し替え制限はありません。

## python-bidi（LGPLv3以降）

python-bidi 0.6.11のPython/Rustソース、Cargo.lockと、そのロックに記載された15個の
Rust依存の完全なcrateソースを収録しています。`prepare_rust_vendor.py <python-bidi-source> <upstream-directory>`
をPython 3.12で実行すると、ハッシュを検証してオフライン用Cargo vendorディレクトリを作成します。
RustのMSVCツールチェーンとMaturinを用意し、上流のpyproject.tomlに従ってwheelをビルドします。
変更したwheelを本体のビルド環境にインストールし、本体を再ビルドできます。
生成した `_bidi` pydは同じPython ABIであれば同梱のものと差し替えることもできます。

## GEOS（LGPLv2.1以降）

GEOS 3.13.1の完全なソースを提供します。Visual Studio x64環境で
`cmake -S <geos-source> -B <geos-build> -DBUILD_SHARED_LIBS=ON -DBUILD_TESTING=OFF`
により構成し、`cmake --build <geos-build> --config Release` で共有ライブラリを作成します。
Shapely 2.1.2のソースも収録しています。GEOS C APIの互換性を保ち、
`_internal/shapely.libs/` 等にあるGEOS DLLを生成した同等のライブラリで置き換えられます。

## NumPyに含まれるlibquadmath（LGPLv2.1以降）

NumPy 1.26.4のWindows版OpenBLAS共有ライブラリは、GCC 10.3.0のlibquadmathを静的に含みます。
そのためOpenBLASの正確なコミットc2f4bdbb系列、GCC 10.3.0の完全なソース
（libquadmath、libgcc、libgfortranおよびビルド用スクリプトを含む）、NumPy 1.26.4のソースを提供します。
MinGW-w64 GCC / GFortran 10.3.0環境を用意し、必要なlibquadmathの変更をGCCソースからビルドした上で、
OpenBLAS付属Makefileを使って64ビット整数APIの共有ライブラリを作成します。
NumPyの構成に合わせる主なオプションは `BINARY=64 INTERFACE64=1 SYMBOLSUFFIX=64_ DYNAMIC_ARCH=1 NO_AFFINITY=1 MAX_THREADS=2` です。
ソースにはMakefileとWindowsビルドの説明、NumPyの `tools/openblas_support.py` も含まれます。
生成したDLLは、NumPyバイナリが参照する元のDLLと同じファイル名・APIで
`_internal/numpy.libs/` 等に配置できます。本体のオブジェクトを再リンクする必要はありません。

## certifi（MPL 2.0）

certifi 2026.10.18の完全なソースを提供します。変更したソースからwheelを作成して
本体のビルド環境に導入し、PyInstallerで本体を再ビルドできます。
証明書データ `cacert.pem` が外部ファイルとして配置されている場合は、そのファイルも置き換え可能です。

## CTranslate2に含まれるEigen（MPL 2.0）

CPUバックエンドに使用したCTranslate2 v4.6.0のチェックアウトと再帰サブモジュールを
`CTranslate2-4.6.0-cpu-source.tar.gz` に収録します。`src/cpu/vec.h` が演算実装の参照元として
指定するMPL 2.0のEigen 3.4.0の全ソースも、別のアーカイブで提供します。
アプリの `build_cpu_backend.py` はCUDA / cuDNNを無効にした同じ構成を再現します。
Eigenの変更後に同スクリプトでバックエンドを作り直し、本体を再ビルドできます。
Intel MKLのSDKは別途Intelから取得し、原文の許諾条件に従って利用してください。

## PyInstaller

バイナリのブートローダーに対応するPyInstaller 6.22.3の完全なソースとビルドスクリプトも収録します。
ブートローダーには上流のライセンスと、アプリケーションの配布を認める例外が適用されます。
本体のMITライセンスをPyInstallerや第三者ライブラリへ拡張しているわけではありません。
'''


def make_source_archive(asset: Path, sources: list[dict], cache: Path, revision: str) -> dict:
    application = public_source_files()
    source_manifest = {'git_revision': revision, 'upstream_sources': sources,
        'application_files': [{'path': path.relative_to(ROOT).as_posix(), 'sha256': digest(path)} for path in application]}
    temporary = asset.with_name(asset.name + '.part')
    with zipfile.ZipFile(temporary, 'w', allowZip64=True) as archive:
        for path in application:
            archive.write(path, 'application/' + path.relative_to(ROOT).as_posix(), compress_type=zipfile.ZIP_DEFLATED)
        for spec in sources:
            archive.write(cache / spec['filename'], 'upstream/' + spec['filename'], compress_type=zipfile.ZIP_STORED)
        archive.writestr('SOURCE_COMPONENTS.json', json.dumps(source_manifest, ensure_ascii=False, indent=2))
        archive.writestr('BUILD_AND_RELINK.md', REBUILD_GUIDE)
        archive.writestr('prepare_rust_vendor.py', VENDOR_HELPER)
    temporary.replace(asset)
    return {'filename': asset.name, 'sha256': digest(asset), 'bytes': asset.stat().st_size,
            'source_components': len(sources), 'application_files': len(application)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bundle', type=Path, required=True)
    parser.add_argument('--python-runtime', type=Path, required=True)
    parser.add_argument('--release-tag', required=True)
    parser.add_argument('--cpu-backend-source', type=Path, default=ROOT / '.publish-audit/cpu-backend/CTranslate2')
    parser.add_argument('--cache', type=Path, default=ROOT / '.publish-audit/compliance/upstream')
    parser.add_argument('--output-directory', type=Path, default=ROOT / 'release')
    args = parser.parse_args()
    bundle, runtime, cache = args.bundle.resolve(), args.python_runtime.resolve(), args.cache.resolve()
    if not bundle.is_relative_to(ROOT / 'dist'):
        raise RuntimeError('配布フォルダーはこのプロジェクトのdist内を指定してください。')
    if not re.fullmatch(r'[A-Za-z0-9_.-]+', args.release_tag):
        raise RuntimeError('リリースタグが不正です。')
    inventory = inspect_bundle(bundle)
    microsoft = microsoft_runtime(bundle, inventory)
    if sys.version_info[:3] != (3, 12, 16):
        raise RuntimeError('パッケージ情報の取得には実際のPython 3.12.16ビルド環境で実行してください。')
    metadata = json.loads((ROOT / 'third_party_licenses/binary-source-lock.json').read_text(encoding='utf-8'))
    sources = metadata['sources']
    cache.mkdir(parents=True, exist_ok=True)
    for spec in sources:
        download(spec, cache)
    sources.append(snapshot_cpu_backend(args.cpu_backend_source.resolve(), cache))
    packages = collect_notices(bundle, runtime, sources, cache)
    revision = git('rev-parse', 'HEAD').decode().strip()
    args.output_directory.mkdir(parents=True, exist_ok=True)
    source_asset = make_source_archive(args.output_directory / SOURCE_ASSET, sources, cache, revision)
    source_asset['url'] = f'https://github.com/KEITER78/LiveScreenTranslator/releases/download/{quote(args.release_tag)}/{SOURCE_ASSET}'
    notice = f'''# 対応ソースの提供とライブラリ変更の権利

このバイナリはPySide6 / Qt / shiboken6、python-bidi、GEOS、NumPy内libquadmath、certifiを使用します。
各LGPL/MPLライセンスの原文と著作権表示は `licenses/` にあります。
対応する完全なソースと本体コード・ビルド手順を、同じGitHub Releaseから無償で取得できます。

- 対応ソース: [{SOURCE_ASSET}]({source_asset['url']})
- SHA-256: `{source_asset['sha256']}`
- 本体ソースのGitリビジョン: `{revision}`

対応ソースZIPの `BUILD_AND_RELINK.md` に再ビルドと差し替え手順を記載しています。
LGPL対象ライブラリの改変・差し替え、改変のデバッグに必要な解析を本体側で禁止しません。
動的DLLはonedir配布の `_internal/` に保持し、ライブラリの差し替えを検証する仕組みで排除しません。
本体ソースもMITで提供するため、改変したライブラリを使う本体の再ビルドが可能です。
この提供方法は、電子配布と同じ場所から対応ソースを提供する方式です。
配布者へ郵送等を申し込む方式の書面オファーではありません。
'''
    (bundle / 'SOURCE_OFFER.md').write_text(notice, encoding='utf-8')
    shutil.copy2(ROOT / 'BINARY_TERMS.md', bundle / 'BINARY_TERMS.md')
    shutil.copy2(ROOT / 'BINARY_DISTRIBUTION.md', bundle / 'BINARY_DISTRIBUTION.md')
    report = {'schema': 1, 'release_tag': args.release_tag, 'git_revision': revision,
        'python': {'version': sys.version.split()[0], 'distribution': 'Astral python-build-standalone / CPython',
                   'license_notice': 'licenses/python/LICENSE.txt'},
        'microsoft_runtime': microsoft,
        'license_scope': 'The application is MIT; bundled third-party components retain their own licenses.',
        'native_binaries': inventory, 'notice_inventory': packages, 'corresponding_sources': source_asset,
        'nvidia_runtime_included': False, 'ffmpeg_runtime_included': False,
        'source_integrity': 'All source archive SHA-256 digests verified against binary-source-lock.json.'}
    atomic_json(bundle / 'BINARY_COMPONENTS.json', report)
    atomic_json(ROOT / '.publish-audit/compliance/bundle-license-report.json', report)
    print(json.dumps({'bundle': bundle.name, 'native_binaries': len(inventory),
        'notice_packages': len(packages), 'corresponding_sources': source_asset}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
