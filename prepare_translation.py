# Copyright (c) 2026 KEITER78
"""Download the official M2M100 checkpoint and prepare a local INT8 model."""
import hashlib
import json
import os
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
MODEL_DIR = ROOT / 'models' / 'm2m100-int8'
REPOSITORY = 'facebook/m2m100_418M'
REVISION = '55c2e61bbf05dfb8d7abccdc3fae6fc8512fd636'
CHECKPOINT_SHA256 = 'd907ea45e4e4b9db163382a6674f6218b3c59566fe06d77f4055c208b4e87ed1'
SPM_SHA256 = 'd8f7c76ed2a5e0822be39f0a4f95a55eb19c78f4593ce609e2edbc2aea4d380a'
FILES = ('config.json', 'generation_config.json', 'pytorch_model.bin',
         'sentencepiece.bpe.model', 'special_tokens_map.json',
         'tokenizer_config.json', 'vocab.json')


def model_ready(directory=MODEL_DIR):
    directory = Path(directory)
    try:
        manifest = json.loads((directory/'ready.json').read_text(encoding='utf-8'))
        return (manifest.get('revision') == REVISION and
                all((directory/name).is_file() and (directory/name).stat().st_size > 0
                    for name in ('model.bin', 'sentencepiece.bpe.model', 'config.json')))
    except (OSError, ValueError):
        return False


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(4 * 1024 * 1024), b''):
            h.update(chunk)
    return h.hexdigest()


def prepare(progress=print):
    if model_ready():
        progress('翻訳モデルは準備済みです。')
        return MODEL_DIR
    import requests
    from ctranslate2.converters import TransformersConverter

    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
    source = ROOT / 'models' / 'downloads' / 'm2m100'
    source.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    # All files are public: never attach an API key or ambient .netrc credentials.
    session.trust_env = False
    for name in FILES:
        path = source / name
        expected = {'pytorch_model.bin': CHECKPOINT_SHA256,
                    'sentencepiece.bpe.model': SPM_SHA256}.get(name)
        if path.is_file() and (expected is None or digest(path) == expected):
            continue
        progress(f'取得中: {name}（初回の全取得量は約1.95GB）')
        partial = path.with_suffix(path.suffix + '.part')
        url = f'https://huggingface.co/{REPOSITORY}/resolve/{REVISION}/{name}'
        with session.get(url, stream=True, timeout=(20, 120)) as response:
            response.raise_for_status()
            downloaded = 0
            with partial.open('wb') as out:
                for chunk in response.iter_content(4 * 1024 * 1024):
                    out.write(chunk)
                    downloaded += len(chunk)
                    if name == 'pytorch_model.bin' and downloaded % (64*1024*1024) < len(chunk):
                        progress(f'翻訳モデル取得中: {downloaded // (1024*1024)} MiB / 約1846 MiB')
        if expected and digest(partial) != expected:
            raise RuntimeError(f'{name} の検証に失敗しました。再実行してください。')
        partial.replace(path)

    progress('CPU向けINT8形式に変換中です。数分かかる場合があります。')
    temporary = MODEL_DIR.with_name(MODEL_DIR.name + '.preparing')
    if not temporary.resolve().is_relative_to((ROOT/'models').resolve()):
        raise RuntimeError('モデル変換先が不正です。')
    # force only replaces conversion output under this fixed, dedicated directory.
    TransformersConverter(str(source), trust_remote_code=False).convert(
        str(temporary), quantization='int8', force=True)
    shutil.copy2(source / 'sentencepiece.bpe.model', temporary)
    license_path = ROOT / 'third_party_licenses' / 'm2m100' / 'LICENSE'
    if license_path.is_file():
        shutil.copy2(license_path, temporary / 'LICENSE')
    record = {'repository': REPOSITORY, 'revision': REVISION,
              'license': 'MIT', 'quantization': 'int8',
              'checkpoint_sha256': CHECKPOINT_SHA256,
              'converted_model_sha256': digest(temporary / 'model.bin'),
              'modification': 'Converted from Transformers to CTranslate2 INT8 by LiveScreenTranslator.'}
    (temporary / 'ready.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
    if MODEL_DIR.exists():
        raise RuntimeError('既存モデルが不完全です。models/m2m100-int8 を別の場所に退避して再実行してください。')
    temporary.replace(MODEL_DIR)
    progress('翻訳モデルの準備が完了しました。以後の翻訳はオフラインで動作します。')
    return MODEL_DIR


if __name__ == '__main__':
    prepare(lambda text: print(text, flush=True))
