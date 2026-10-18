# Copyright (c) 2026 KEITER78
from pathlib import Path
import io
import os
import shutil
import subprocess

from languages import TESSERACT_CODES, EASYOCR_CODES

ROOT = Path(__file__).resolve().parent
TESSDATA_DIR = ROOT / 'models' / 'tessdata'


class OcrService:
    def __init__(self):
        self.easy_reader = None
        self.easy_language = None

    def read(self, image, source, engine, progress=lambda text: None):
        if engine == 'EasyOCR':
            return self._easy_read(image, source, progress)
        return self._tesseract_read(image, source, progress)

    def _tesseract_read(self, image, source, progress):
        command = shutil.which('tesseract')
        if not command:
            candidate = Path(os.environ.get('ProgramFiles', r'C:\Program Files')) / 'Tesseract-OCR/tesseract.exe'
            if candidate.is_file():
                command = str(candidate)
        if not command:
            raise RuntimeError('Tesseractが見つかりません。Tesseractをインストールするか、EasyOCRを選択してください。')
        code = TESSERACT_CODES.get(source)
        if not code:
            raise RuntimeError('この言語のTesseract OCRデータは未対応です。原文欄への貼り付け翻訳は利用できます。')
        codes = list(dict.fromkeys([code, 'eng']))
        if source == 'zh':
            codes.insert(1, 'chi_tra')
        self._ensure_data(codes, progress)
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
        for code in codes:
            path = TESSDATA_DIR / f'{code}.traineddata'
            if path.is_file():
                continue
            progress(f'OCR言語データを取得中: {code}（初回のみ）')
            url = f'https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/4.1.0/{code}.traineddata'
            with session.get(url, stream=True, timeout=(20, 90)) as response:
                response.raise_for_status()
                partial = path.with_suffix('.traineddata.part')
                with partial.open('wb') as out:
                    for chunk in response.iter_content(1024*1024):
                        out.write(chunk)
            partial.replace(path)
        license_source = ROOT / 'third_party_licenses' / 'common' / 'Apache-2.0.txt'
        if license_source.is_file() and not (TESSDATA_DIR/'LICENSE').exists():
            shutil.copy2(license_source, TESSDATA_DIR/'LICENSE')

    def _easy_read(self, image, source, progress):
        import easyocr
        import numpy as np
        language = EASYOCR_CODES.get(source, source)
        if language not in easyocr.config.all_lang_list:
            raise RuntimeError('EasyOCRはこの言語に対応していません。Tesseractを選択してください。')
        if self.easy_reader is None or self.easy_language != language:
            progress('EasyOCRを準備中です（初回はモデルを取得します）。')
            codes = list(dict.fromkeys([language, 'en']))
            self.easy_reader = easyocr.Reader(codes, gpu=False)
            self.easy_language = language
        return ' '.join(self.easy_reader.readtext(np.array(image), detail=0))
