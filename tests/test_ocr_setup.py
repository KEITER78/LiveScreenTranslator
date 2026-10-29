# Copyright (c) 2026 KEITER78
"""OCR setup/cache tests without network requests or real OCR model loading."""
import json
from pathlib import Path
import sys
import tempfile
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import MagicMock, Mock, patch

import ocr_service


class OcrSetupTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(
            prefix='lst-ocr-tests-', dir=Path(__file__).resolve().parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.models = self.root / 'easyocr'
        self.network = self.root / 'network'
        self.tessdata = self.root / 'tessdata'
        self.fake_easyocr = ModuleType('easyocr')
        self.fake_easyocr.__version__ = '1.7.2'
        self.fake_easyocr.config = SimpleNamespace(all_lang_list=['en', 'ja', 'ch_sim', 'fr'])
        self.fake_easyocr.Reader = Mock(side_effect=self.make_reader)
        replacements = [
            patch.object(ocr_service, 'EASYOCR_MODEL_DIR', self.models),
            patch.object(ocr_service, 'EASYOCR_NETWORK_DIR', self.network),
            patch.object(ocr_service, 'TESSDATA_DIR', self.tessdata),
            patch.dict(sys.modules, {'easyocr': self.fake_easyocr}),
            patch.dict('os.environ', {'ProgramFiles': str(self.root / 'programs')}),
        ]
        for replacement in replacements:
            replacement.start()
            self.addCleanup(replacement.stop)
        self.service = ocr_service.OcrService()

    def make_reader(self, languages, **options):
        directory = Path(options['model_storage_directory'])
        directory.mkdir(parents=True, exist_ok=True)
        Path(options['user_network_directory']).mkdir(parents=True, exist_ok=True)
        detection = {'filename': 'craft.pth', 'md5sum': 'a' * 32}
        recognition = {'filename': 'english_g2.pth', 'md5sum': 'b' * 32,
                       'model_script': 'english', 'characters': 'abc'}
        (directory / detection['filename']).write_bytes(b'detection-model')
        (directory / recognition['filename']).write_bytes(b'recognition-model')
        return SimpleNamespace(detection_models={'craft': detection}, detect_network='craft',
            recognition_models={'gen1': {}, 'gen2': {'english_g2': recognition}},
            model_lang='english', character='abc', readtext=Mock(return_value=['hello']))

    def test_easyocr_prepares_inside_explicit_user_cache(self):
        progress = []
        self.service.prepare('en', 'EasyOCR', progress.append)
        options = self.fake_easyocr.Reader.call_args.kwargs
        self.assertEqual(self.fake_easyocr.Reader.call_args.args, (['en'],))
        self.assertEqual(options['model_storage_directory'], str(self.models))
        self.assertEqual(options['user_network_directory'], str(self.network))
        self.assertIs(options['gpu'], False)
        self.assertIs(options['verbose'], False)
        self.assertIs(options['download_enabled'], True)
        self.assertTrue(progress)
        self.assertTrue(self.service.is_ready('en', 'EasyOCR'))
        # A new process can inspect the stamp without importing EasyOCR or Torch.
        with patch.dict(sys.modules, {'easyocr': None}):
            self.assertTrue(ocr_service.OcrService().is_ready('en', 'EasyOCR'))
        self.service.prepare('en', 'EasyOCR')
        self.fake_easyocr.Reader.assert_called_once()

    def test_missing_or_truncated_cached_weight_requires_setup_again(self):
        self.service.prepare('en', 'EasyOCR')
        fresh = ocr_service.OcrService()
        (self.models / 'english_g2.pth').write_bytes(b'')
        self.assertFalse(fresh.is_ready('en', 'EasyOCR'))
        (self.models / 'english_g2.pth').unlink()
        self.assertFalse(fresh.is_ready('en', 'EasyOCR'))

    def test_unsupported_language_does_not_start_reader_or_write_cache(self):
        with self.assertRaisesRegex(RuntimeError, '対応していません'):
            self.service.prepare('am', 'EasyOCR')
        self.fake_easyocr.Reader.assert_not_called()
        self.assertFalse(self.models.exists())
        self.assertFalse(self.service.is_ready('am', 'EasyOCR'))

    def test_failed_reader_does_not_create_ready_stamp(self):
        self.fake_easyocr.Reader.side_effect = RuntimeError('download failed')
        with self.assertRaisesRegex(RuntimeError, 'download failed'):
            self.service.prepare('en', 'EasyOCR')
        self.assertFalse(self.service.is_ready('en', 'EasyOCR'))
        self.assertIsNone(self.service.easy_reader)

    def test_chinese_passes_easyocr_alias_and_english(self):
        self.service.prepare('zh', 'EasyOCR')
        self.assertEqual(self.fake_easyocr.Reader.call_args.args, (['ch_sim', 'en'],))
        self.assertTrue(self.service.is_ready('zh', 'EasyOCR'))

    def test_malformed_and_path_traversal_markers_are_not_ready(self):
        self.models.mkdir()
        marker = self.models / 'en.ready.json'
        for content in ('[]', '{broken', 'null'):
            marker.write_text(content, encoding='utf-8')
            self.assertFalse(self.service.is_ready('en', 'EasyOCR'))
        record = {'schema': 1, 'version': '1.7.2', 'language': 'en',
                  'files': [{'name': '../outside.pth', 'size': 1},
                            {'name': 'craft.pth', 'size': 1}]}
        marker.write_text(json.dumps(record), encoding='utf-8')
        self.assertFalse(self.service.is_ready('en', 'EasyOCR'))
        self.assertFalse(self.service.is_ready('../../outside', 'EasyOCR'))

    def test_unknown_engine_does_not_fall_back_to_tesseract(self):
        self.assertFalse(self.service.is_ready('en', 'unknown'))
        with self.assertRaisesRegex(RuntimeError, 'OCRエンジン'):
            self.service.prepare('en', 'unknown')

    def test_tesseract_requires_existing_engine_and_nonempty_language_files(self):
        self.tessdata.mkdir()
        for code in ('jpn', 'eng'):
            (self.tessdata / f'{code}.traineddata').write_bytes(b'data')
        with patch.object(ocr_service.shutil, 'which', return_value=None):
            self.assertFalse(self.service.is_ready('ja', 'Tesseract'))
            with self.assertRaisesRegex(RuntimeError, 'EasyOCRを選択'):
                self.service.prepare('ja', 'Tesseract')
        with patch.object(ocr_service.shutil, 'which', return_value='C:/Tesseract/tesseract.exe'):
            self.assertTrue(self.service.is_ready('ja', 'Tesseract'))
            (self.tessdata / 'eng.traineddata').write_bytes(b'')
            self.assertFalse(self.service.is_ready('ja', 'Tesseract'))

    def test_tesseract_downloads_selected_language_data_and_reuses_it(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.iter_content.return_value = [b'language-data']
        session = MagicMock()
        session.get.return_value = response
        with patch.object(ocr_service.shutil, 'which', return_value='tesseract'), \
                patch('requests.Session', return_value=session):
            self.service.prepare('zh', 'Tesseract')
            self.assertTrue(self.service.is_ready('zh', 'Tesseract'))
            self.assertEqual(session.get.call_count, 3)
            self.assertFalse(session.trust_env)
            self.assertEqual({path.stem for path in self.tessdata.glob('*.traineddata')},
                             {'chi_sim', 'chi_tra', 'eng'})
            self.service.prepare('zh', 'Tesseract')
            self.assertEqual(session.get.call_count, 3)

    def test_tesseract_empty_download_is_not_marked_ready(self):
        response = MagicMock()
        response.__enter__.return_value = response
        response.iter_content.return_value = []
        session = MagicMock()
        session.get.return_value = response
        with patch.object(ocr_service.shutil, 'which', return_value='tesseract'), \
                patch('requests.Session', return_value=session):
            with self.assertRaisesRegex(RuntimeError, '取得に失敗'):
                self.service.prepare('en', 'Tesseract')
        self.assertFalse((self.tessdata / 'eng.traineddata').exists())


if __name__ == '__main__':
    unittest.main()
