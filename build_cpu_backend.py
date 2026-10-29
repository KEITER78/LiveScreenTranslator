# Copyright (c) 2026 KEITER78
"""Build CTranslate2 without CUDA/cuDNN for the portable CPU application.

Run with the dedicated CPython 3.12.16 build environment after installing
requirements-build.txt. Visual Studio C++ x64 build tools are prerequisites.
The ordinary development/runtime .venv is deliberately protected.

    python build_cpu_backend.py --install

The upstream revision stays pinned. Local changes pair sequential MKL with
compiler OpenMP on Windows, enforce UTF-8 compilation, apply a +cpu version
label, and include component licenses and sanitized build provenance.
"""
import argparse
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
REVISION = '617405f4b050e994e829d527da6caa0e0030afe7'
SOURCE_URL = 'https://github.com/OpenNMT/CTranslate2.git'
MKL_VERSION = '2026.1.0'
COMMAND_LOG = None


def run(command, cwd=None, env=None):
    command = list(map(str, command))
    if COMMAND_LOG is None:
        subprocess.run(command, cwd=cwd, env=env, check=True)
        return
    print('Running: ' + Path(command[0]).name + ' ' + ' '.join(command[1:3]), flush=True)
    with COMMAND_LOG.open('ab') as log:
        result = subprocess.run(command, cwd=cwd, env=env, stdout=log, stderr=subprocess.STDOUT)
    if result.returncode:
        print('\n'.join(COMMAND_LOG.read_text(encoding='utf-8', errors='replace').splitlines()[-45:]), flush=True)
        raise subprocess.CalledProcessError(result.returncode, command)


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            result.update(chunk)
    return result.hexdigest()


def vc_environment():
    vswhere = Path(os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')) / 'Microsoft Visual Studio/Installer/vswhere.exe'
    if not vswhere.is_file():
        raise RuntimeError('Visual Studio Installer/vswhere.exe was not found.')
    install = subprocess.check_output([
        str(vswhere), '-latest', '-products', '*', '-requires',
        'Microsoft.VisualStudio.Component.VC.Tools.x86.x64',
        '-property', 'installationPath',
    ], text=True).strip()
    vcvars = Path(install) / 'VC/Auxiliary/Build/vcvars64.bat'
    if not vcvars.is_file():
        raise RuntimeError('Install the Visual Studio C++ x64 build tools first.')
    # This shell only initializes the installed compiler environment. File
    # operations and all compiler/build commands below use structured argv.
    command = f'"{os.environ.get("COMSPEC", "cmd.exe")}" /d /s /c ""{vcvars}" >nul && set"'
    result = subprocess.run(command, check=True, capture_output=True, text=True, encoding='mbcs')
    env = dict(os.environ)
    env.update((key.upper(), value)
               for key, value in (line.split('=', 1) for line in result.stdout.splitlines()
                                  if '=' in line and not line.startswith('=')))
    env['PATH'] = str(Path(sys.executable).parent) + os.pathsep + env.get('PATH', '')
    env['CMAKE_BUILD_PARALLEL_LEVEL'] = '8'
    env['VSLANG'] = '1033'
    return env


def build(work_dir, install_wheel):
    global COMMAND_LOG
    if os.name != 'nt' or sys.version_info[:3] != (3, 12, 16):
        raise RuntimeError('Use the dedicated Windows CPython 3.12.16 build environment.')
    prefix = Path(sys.prefix).resolve()
    if prefix == Path(sys.base_prefix).resolve() or prefix == (ROOT / '.venv').resolve():
        raise RuntimeError('Use a separate build venv; the application .venv must remain unchanged.')
    work_dir = work_dir.resolve()
    if not work_dir.is_relative_to(ROOT / '.publish-audit'):
        raise RuntimeError('Native compilation outputs must remain under .publish-audit/.')
    for package in ('mkl-static', 'mkl-include'):
        if metadata.version(package) != MKL_VERSION:
            raise RuntimeError('Install the pinned build requirements first.')
    work_dir.mkdir(parents=True, exist_ok=True)
    COMMAND_LOG = work_dir / 'build.log'
    source = work_dir / 'CTranslate2'
    if not source.exists():
        run(['git', 'clone', '--depth', '1', '--branch', 'v4.6.0',
             '--recurse-submodules', '--shallow-submodules', SOURCE_URL, source])
    revision = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip()
    if revision != REVISION:
        raise RuntimeError('The CTranslate2 source checkout does not match the pinned revision.')
    # Use compiler OpenMP for CT2's parallel loops and sequential MKL for GEMM.
    # This avoids Windows TLS-destructor joins in the fallback thread-pool path.
    cmake_file = source / 'CMakeLists.txt'
    cmake_text = cmake_file.read_text(encoding='utf-8')
    cmake_text = cmake_text.replace(
        'message(FATAL_ERROR "Building with MKL requires Intel OpenMP")',
        'list(APPEND MKL_LIBRARIES ${MKL_LIBRARY_DIR}/mkl_sequential.lib)')
    cmake_file.write_text(cmake_text, encoding='utf-8')
    env = vc_environment()
    cmake = Path(sys.executable).parent / 'cmake.exe'
    if not cmake.is_file():
        raise RuntimeError('Install CMake from requirements-build.txt first.')
    mkl_root = prefix / 'Library'
    for relative in ('include/mkl.h', 'lib/mkl_core.lib', 'lib/mkl_intel_ilp64.lib', 'lib/mkl_sequential.lib'):
        if not (mkl_root / relative).is_file():
            raise RuntimeError('The MKL static build inputs are incomplete: ' + relative)
    binary_dir = work_dir / 'native-build'
    native_install = work_dir / 'native-install'
    options = {
        'CMAKE_BUILD_TYPE': 'Release', 'BUILD_SHARED_LIBS': 'ON',
        'BUILD_CLI': 'OFF', 'BUILD_TESTS': 'OFF',
        'WITH_CUDA': 'OFF', 'WITH_CUDNN': 'OFF', 'WITH_DNNL': 'OFF',
        'WITH_MKL': 'ON', 'WITH_OPENBLAS': 'OFF', 'WITH_RUY': 'OFF',
        'OPENMP_RUNTIME': 'COMP', 'ENABLE_CPU_DISPATCH': 'ON',
        'CMAKE_POLICY_VERSION_MINIMUM': '3.5',
    }
    # /d1trimfile removes the private checkout prefix from __FILE__ strings.
    # Release mode omits compiler debug symbols; the linker uses a base name
    # if a debug record is emitted by a third-party object.
    trim_prefix = str(ROOT) + '\\'
    compiler_flags = f'/utf-8 /d1trimfile:{trim_prefix}'
    import ninja
    ninja_executable = Path(ninja.BIN_DIR) / 'ninja.exe'
    run([cmake, '-S', source, '-B', binary_dir, '-G', 'Ninja',
         *[f'-D{name}={value}' for name, value in options.items()],
         f'-DCMAKE_MAKE_PROGRAM={ninja_executable}',
         f'-DMKL_ROOT={mkl_root}', f'-DCMAKE_INSTALL_PREFIX={native_install}',
         f'-DCMAKE_CXX_FLAGS={compiler_flags}',
         f'-DCMAKE_C_FLAGS={compiler_flags}',
         '-DCMAKE_SHARED_LINKER_FLAGS=/PDBALTPATH:%_PDB%'], env=env)
    run([cmake, '--build', binary_dir, '--parallel', '8'], env=env)
    run([cmake, '--install', binary_dir], env=env)
    dll = native_install / 'bin/ctranslate2.dll'
    if not dll.is_file():
        raise RuntimeError('The CPU-only shared library was not produced.')
    import pefile
    pe = pefile.PE(str(dll))
    imports = sorted(entry.dll.decode('ascii') for entry in pe.DIRECTORY_ENTRY_IMPORT)
    pe.close()
    if any(re.match(r'(?:cudnn|cublas|cufft|curand|cusolver|cusparse|nvrtc|nvcuda|cudart)', name, re.I) for name in imports):
        raise RuntimeError('The CPU backend unexpectedly imports a GPU library.')
    package = source / 'python/ctranslate2'
    shutil.copy2(dll, package / dll.name)
    redist = Path(env.get('VCTOOLSREDISTDIR', ''))
    openmp = list(redist.glob('x64/Microsoft.VC*.OpenMP/vcomp140.dll')) if redist.is_dir() else []
    if not openmp:
        raise RuntimeError('The redistributable x64 Visual C++ OpenMP runtime was not found.')
    shutil.copy2(sorted(openmp)[-1], package / 'vcomp140.dll')
    licenses = package / 'licenses'
    licenses.mkdir(exist_ok=True)
    shutil.copy2(source / 'LICENSE', licenses / 'CTranslate2-LICENSE.txt')
    for distribution_name in ('mkl-static', 'mkl-include'):
        distribution = metadata.distribution(distribution_name)
        for name in distribution.files or []:
            if any(marker in str(name).lower() for marker in ('license', 'third-party', 'third_party')) and distribution.locate_file(name).is_file():
                shutil.copy2(distribution.locate_file(name), licenses / f'{distribution_name}-{Path(name).name}')
    setup = source / 'python/setup.py'
    setup_text = setup.read_text(encoding='utf-8')
    setup_text = setup_text.replace('package_data["ctranslate2"] = ["*.dll"]',
                                    'package_data["ctranslate2"] = ["*.dll", "licenses/*", "CPU_BUILD.json"]')
    setup.write_text(setup_text, encoding='utf-8')
    version_file = package / 'version.py'
    version_text = version_file.read_text(encoding='utf-8')
    version_text = version_text.replace('__version__ = "4.6.0"', '__version__ = "4.6.0+cpu"')
    version_file.write_text(version_text, encoding='utf-8')
    submodules = subprocess.check_output(['git', 'submodule', 'status', '--recursive'], cwd=source, text=True)
    provenance = {
        'upstream_repository': SOURCE_URL, 'upstream_revision': REVISION,
        'version': '4.6.0+cpu', 'mkl_static_version': MKL_VERSION,
        'build_options': options, 'native_dll_sha256': digest(dll),
        'compiler_options': ['/utf-8', '/d1trimfile:<project-root>\\'],
        'linker_options': ['/PDBALTPATH:%_PDB%'],
        'native_imports': imports,
        'submodules': [{'revision': line.strip().split()[0], 'path': line.strip().split()[1]}
                       for line in submodules.splitlines() if line.strip()],
        'modifications': ['CPU-only native build', '+cpu package version label',
                          'Sequential MKL with compiler OpenMP on Windows to avoid fallback TLS thread-pool shutdown deadlock',
                          'Package includes build provenance and original component licenses'],
    }
    (package / 'CPU_BUILD.json').write_text(json.dumps(provenance, indent=2) + '\n', encoding='utf-8')
    env['CTRANSLATE2_ROOT'] = str(native_install)
    env['CL'] = (env.get('CL', '') + ' ' + compiler_flags).strip()
    env['LINK'] = (env.get('LINK', '') + ' /PDBALTPATH:%_PDB%').strip()
    wheel_dir = work_dir / 'wheels'
    wheel_dir.mkdir(exist_ok=True)
    run([sys.executable, 'setup.py', 'build_ext', '--force'], cwd=source / 'python', env=env)
    run([sys.executable, 'setup.py', 'bdist_wheel', '--dist-dir', wheel_dir], cwd=source / 'python', env=env)
    wheels = list(wheel_dir.glob('ctranslate2-4.6.0+cpu-cp312-cp312-win_amd64.whl'))
    if len(wheels) != 1:
        raise RuntimeError('A unique CPython3.12 x64 CPU wheel was not produced.')
    wheel = wheels[0]
    if install_wheel:
        run([sys.executable, '-m', 'pip', 'install', '--force-reinstall', '--no-deps', wheel])
        run([sys.executable, '-c',
             'import ctranslate2; print(ctranslate2.__version__); '
             'assert "int8" in ctranslate2.get_supported_compute_types("cpu"); '
             'assert ctranslate2.get_cuda_device_count() == 0'])
    report = {**provenance, 'wheel': wheel.name, 'wheel_sha256': digest(wheel),
              'installed_in_build_env': install_wheel}
    (work_dir / 'CPU_BACKEND_BUILD.json').write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--work-dir', type=Path, default=ROOT / '.publish-audit/cpu-backend')
    parser.add_argument('--install', action='store_true', help='Replace the GPU-capable wheel in this dedicated build venv only.')
    arguments = parser.parse_args()
    build(arguments.work_dir, arguments.install)
