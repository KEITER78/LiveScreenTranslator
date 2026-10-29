# Copyright (c) 2026 KEITER78
from pathlib import Path
import io
import json
import os
import re
import shutil
import subprocess

from app_paths import (RESOURCE_ROOT, TESSDATA_DIR, EASYOCR_MODEL_DIR,
    EASYOCR_NETWORK_DIR)
from languages import LANGUAGES, TESSERACT_CODES, EASYOCR_CODES

EASYOCR_RELEASE = '1.7.2'
EASYOCR_CACHE_SCHEMA = 1


class OcrService:
    def __init__(self):
        self.easy_reader = None
        self.easy_language = None

    def read(self, image, source, engine, progress=lambda text: None):
        if engine == 'EasyOCR':
            return self._easy_read(image, source, progress)
        if engine != 'Tesseract':
            raise RuntimeError('対応していないOCRエンジンが選択されています。')
        return self._tesseract_read(image, source, progress)

    def _tesseract_command(self):
        command = shutil.which('tesseract')
        if not command:
            candidate = Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'Tesseract-OCR/tesseract.exe'
            if candidate.is_file():
                command = str(candidate)
        return command

    def _tesseract_codes(self, source):
        code = TESSERACT_CODES.get(source)
        if not code:
            raise RuntimeError('この言語のTesseract OCRデータは未対応です。原文欄への貼り付け翻訳は利用できます。')
        codes = list(dict.fromkeys([code, 'eng']))
        if source == 'zh':
            codes.insert(1, 'chi_tra')
        return codes

    def _easy_language(self, source):
        if source not in LANGUAGES:
            raise RuntimeError('対応していない翻訳元言語が選択されています。')
        return EASYOCR_CODES.get(source, source)

    def validate_setup(self, source, engine):
        """Validate a setup choice before downloading the translation model."""
        if engine == 'Tesseract':
            self._tesseract_codes(source)
            if not self._tesseract_command():
                raise RuntimeError('Tesseract本体が見つかりません。別途インストール済みのTesseractを使用するか、EasyOCRを選択してください。')
        elif engine == 'EasyOCR':
            language = self._easy_language(source)
            import easyocr
            if language not in easyocr.config.all_lang_list:
                raise RuntimeError('EasyOCRはこの言語に対応していません。Tesseractを選ぶか、文字認識の準備を外して貼り付け翻訳を使用してください。')
        else:
            raise RuntimeError('対応していないOCRエンジンが選択されています。')

    def prepare(self, source, engine, progress=lambda text: None):
        self.validate_setup(source, engine)
        if engine == 'Tesseract':
            self._ensure_data(self._tesseract_codes(source), progress)
        else:
            self._prepare_easy(source, progress)

    def is_ready(self, source, engine):
        """Inspect local preparation without importing Torch or downloading data."""
        try:
            if engine == 'Tesseract':
                return bool(self._tesseract_command()) and all(
                    (TESSDATA_DIR / f'{code}.traineddata').is_file()
                    and (TESSDATA_DIR / f'{code}.traineddata').stat().st_size > 0
                    for code in self._tesseract_codes(source))
            if engine != 'EasyOCR':
                return False
            language = self._easy_language(source)
            if self.easy_reader is not None and self.easy_language == language:
                return True
            manifest = json.loads(self._easy_marker(language).read_text(encoding='utf-8'))
            if (not isinstance(manifest, dict)
                    or manifest.get('schema') != EASYOCR_CACHE_SCHEMA
                    or manifest.get('version') != EASYOCR_RELEASE
                    or manifest.get('language') != language):
                return False
            files = manifest.get('files')
            if not isinstance(files, list) or len(files) != 2:
                return False
            names = set()
            for entry in files:
                name, size = entry['name'], entry['size']
                if (not isinstance(name, str) or not re.fullmatch(r'[A-Za-z0-9_.-]+\.(?:pth|pt)', name)
                        or not isinstance(size, int) or size <= 0):
                    return False
                if name in names:
                    return False
                names.add(name)
                path = EASYOCR_MODEL_DIR / name
                if not path.is_file() or path.stat().st_size != size:
                    return False
            return True
        except (OSError, ValueError, KeyError, TypeError, RuntimeError):
            return False

    def _tesseract_read(self, image, source, progress):
        self.prepare(source, 'Tesseract', progress)
        command = self._tesseract_command()
        codes = self._tesseract_codes(source)
        # Pass a real argv list so paths containing spaces work on Windows too.
        buffer = io.BytesIO()
        image.save(buffer, format='PNG')
        result = subprocess.run([command, 'stdin', 'stdout', '--tessdata-dir',
            str(TESSDATA_DIR), '-l', '+'.join(codes), '--psm', '6'],
            input=buffer.getvalue(), capture_output=True, timeout=30,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0)
        if result.returncode:
            raise RuntimeError(result.stderr.decode('utf-8', errors='replace').strip())
        return result.stdout.decode('utf-8').strip()

    def _ensure_data(self, codes, progress):
        import requests
        TESSDATA_DIR.mkdir(parents=True, exist_ok=True)
        session = requests.Session()
        session.trust_env = False
        try:
            for code in codes:
                path = TESSDATA_DIR / f'{code}.traineddata'
                if path.is_file() and path.stat().st_size > 0:
                    continue
                progress(f'OCR言語データを取得中: {code}')
                url = f'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/{code}.traineddata'
                with session.get(url, stream=True, timeout=(20, 90)) as response:
                    response.raise_for_status()
                    partial = path.with_suffix('.traineddata.part')
                    with partial.open('wb') as out:
                        for chunk in response.iter_content(1024*1024):
                            out.write(chunk)
                            progress(f'OCR言語データを取得中: {code}')
                if partial.stat().st_size == 0:
                    raise RuntimeError(f'OCR言語データ {code} の取得に失敗しました。再実行してください。')
                partial.replace(path)
        finally:
            session.close()
        license_source = RESOURCE_ROOT / 'third_party_licenses' / 'common' / 'Apache-2.0.txt'
        if license_source.is_file() and not (TESSDATA_DIR/'LICENSE').exists():
            shutil.copy2(license_source, TESSDATA_DIR/'LICENSE')

    def _easy_marker(self, language):
        return EASYOCR_MODEL_DIR / f'{language}.ready.json'

    def _easy_model_records(self, reader):
        detection = reader.detection_models[reader.detect_network]
        recognition = None
        # The standard Reader selects generation 2 where a matching model exists,
        # otherwise generation 1. Match the reader's actual script and alphabet.
        for generation in ('gen2', 'gen1'):
            for model in reader.recognition_models[generation].values():
                if (model['model_script'] == reader.model_lang
                        and model['characters'] == reader.character):
                    recognition = model
                    break
            if recognition is not None:
                break
        if recognition is None:
            raise RuntimeError('文字認識モデルの準備状態を確認できませんでした。')
        records = []
        for model in (detection, recognition):
            name = model['filename']
            path = EASYOCR_MODEL_DIR / name
            if not path.is_file() or path.stat().st_size == 0:
                raise RuntimeError('文字認識モデルの保存を確認できませんでした。再実行してください。')
            records.append({'name': name, 'size': path.stat().st_size,
                            'md5': model['md5sum']})
        return records

    def _prepare_easy(self, source, progress):
        import easyocr
        language = self._easy_language(source)
        if self.easy_reader is not None and self.easy_language == language:
            return
        progress('EasyOCRの認識モデルを準備中です。初回はモデルを取得します。')
        codes = list(dict.fromkeys([language, 'en']))
        reader = easyocr.Reader(codes, gpu=False, verbose=False,
            model_storage_directory=str(EASYOCR_MODEL_DIR),
            user_network_directory=str(EASYOCR_NETWORK_DIR), download_enabled=True)
        progress('EasyOCRの認識モデルを読み込みました。')
        manifest = {'schema': EASYOCR_CACHE_SCHEMA,
            'version': getattr(easyocr, '__version__', EASYOCR_RELEASE),
            'language': language, 'files': self._easy_model_records(reader)}
        marker = self._easy_marker(language)
        temporary = marker.with_suffix('.json.part')
        temporary.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
        temporary.replace(marker)
        self.easy_reader, self.easy_language = reader, language

    def _easy_read(self, image, source, progress):
        import numpy as np
        self.prepare(source, 'EasyOCR', progress)
        return ' '.join(self.easy_reader.readtext(np.array(image), detail=0))
