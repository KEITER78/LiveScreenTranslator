# Copyright (c) 2026 KEITER78
"""Writable-path and model-preparation regression tests with tiny local fixtures."""
from contextlib import ExitStack
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from types import ModuleType
import unittest
from unittest.mock import MagicMock, patch

import prepare_translation


class ApplicationPathTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(
            prefix='lst-path-tests-', dir=Path(__file__).resolve().parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)

    def load_paths(self, environment, frozen=False):
        filename = Path(__file__).resolve().parent.parent / 'app_paths.py'
        spec = importlib.util.spec_from_file_location('_lst_test_paths', filename)
        module = importlib.util.module_from_spec(spec)
        with ExitStack() as stack:
            stack.enter_context(patch.dict(os.environ))
            os.environ.pop('LST_DATA_DIR', None)
            os.environ.pop('LOCALAPPDATA', None)
            os.environ.update(environment)
            stack.enter_context(patch.object(sys, 'frozen', frozen, create=True))
            if frozen:
                stack.enter_context(patch.object(sys, '_MEIPASS', str(self.root / 'program/_internal'), create=True))
            spec.loader.exec_module(module)
        return module

    def test_default_cache_is_per_user_and_import_creates_nothing(self):
        local = self.root / 'local-appdata'
        paths = self.load_paths({'LOCALAPPDATA': str(local)})
        self.assertEqual(paths.DATA_DIR, local / 'LiveScreenTranslator')
        self.assertTrue(paths.MODEL_DIR.is_relative_to(paths.DATA_DIR))
        self.assertTrue(paths.EASYOCR_MODEL_DIR.is_relative_to(paths.DATA_DIR))
        self.assertFalse(local.exists())

    def test_explicit_isolated_cache_does_not_change_bundled_resources(self):
        override = self.root / 'isolated-cache'
        paths = self.load_paths({'LOCALAPPDATA': str(self.root / 'user'), 'LST_DATA_DIR': str(override)}, frozen=True)
        self.assertEqual(paths.DATA_DIR, override)
        self.assertEqual(paths.RESOURCE_ROOT, self.root / 'program/_internal')
        self.assertFalse(paths.MODEL_DIR.is_relative_to(paths.RESOURCE_ROOT))
        self.assertFalse(override.exists())

    def test_empty_override_uses_user_cache_instead_of_program_directory(self):
        local = self.root / 'local-appdata'
        paths = self.load_paths({'LOCALAPPDATA': str(local), 'LST_DATA_DIR': ''})
        self.assertEqual(paths.DATA_DIR, local / 'LiveScreenTranslator')

    def test_empty_localappdata_uses_home_fallback(self):
        paths = self.load_paths({'LOCALAPPDATA': '', 'LST_DATA_DIR': ''})
        self.assertEqual(paths.DATA_DIR, (Path.home() / 'AppData/Local/LiveScreenTranslator').resolve())


class ModelPreparationTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(
            prefix='lst-model-tests-', dir=Path(__file__).resolve().parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.data = self.root / 'user-data'
        self.model = self.data / 'models/m2m100-int8'
        self.downloads = self.data / 'models/downloads/m2m100'
        self.downloads.mkdir(parents=True)
        for name in prepare_translation.FILES:
            (self.downloads / name).write_bytes(b'tiny fixture: ' + name.encode())
        converter_module = ModuleType('ctranslate2.converters')
        converter_module.TransformersConverter = MagicMock(side_effect=self.converter)
        self.converter_factory = converter_module.TransformersConverter
        converter_package = ModuleType('ctranslate2')
        converter_package.__path__ = []
        self.session = MagicMock()
        replacements = [
            patch.object(prepare_translation, 'DATA_DIR', self.data),
            patch.object(prepare_translation, 'MODEL_DIR', self.model),
            patch.object(prepare_translation, 'MODEL_DOWNLOAD_DIR', self.downloads),
            patch.object(prepare_translation, 'CHECKPOINT_SHA256', prepare_translation.digest(self.downloads / 'pytorch_model.bin')),
            patch.object(prepare_translation, 'SPM_SHA256', prepare_translation.digest(self.downloads / 'sentencepiece.bpe.model')),
            patch.dict(sys.modules, {'ctranslate2': converter_package, 'ctranslate2.converters': converter_module}),
            patch('requests.Session', return_value=self.session),
        ]
        for replacement in replacements:
            replacement.start()
            self.addCleanup(replacement.stop)

    def converter(self, source, trust_remote_code):
        self.assertEqual(Path(source), self.downloads)
        self.assertFalse(trust_remote_code)

        def convert(destination, quantization, force):
            self.assertEqual(quantization, 'int8')
            self.assertTrue(force)
            output = Path(destination)
            output.mkdir(parents=True, exist_ok=True)
            (output / 'model.bin').write_bytes(b'tiny-converted-model')
            (output / 'config.json').write_text('{}', encoding='utf-8')
            (output / 'shared_vocabulary.json').write_text('{}', encoding='utf-8')

        return type('TinyConverter', (), {'convert': staticmethod(convert)})()

    def ready_fixture(self, manifest=None):
        self.model.mkdir(parents=True, exist_ok=True)
        for name in ('model.bin', 'sentencepiece.bpe.model', 'config.json', 'shared_vocabulary.json'):
            (self.model / name).write_bytes(b'fixture')
        manifest = {'revision': prepare_translation.REVISION} if manifest is None else manifest
        (self.model / 'ready.json').write_text(json.dumps(manifest), encoding='utf-8')

    def test_ready_model_requires_correct_revision_and_nonempty_files(self):
        self.ready_fixture()
        self.assertTrue(prepare_translation.model_ready(self.model))
        (self.model / 'model.bin').write_bytes(b'')
        self.assertFalse(prepare_translation.model_ready(self.model))
        self.ready_fixture({'revision': 'different'})
        self.assertFalse(prepare_translation.model_ready(self.model))

    def test_recorded_file_sizes_detect_nonempty_truncation(self):
        self.ready_fixture()
        manifest = {'revision': prepare_translation.REVISION,
                    'converted_file_sizes': {path.name: path.stat().st_size
                        for path in self.model.iterdir() if path.name != 'ready.json'}}
        (self.model / 'ready.json').write_text(json.dumps(manifest), encoding='utf-8')
        self.assertTrue(prepare_translation.model_ready(self.model))
        (self.model / 'model.bin').write_bytes(b'x')
        self.assertFalse(prepare_translation.model_ready(self.model))

    def test_legacy_source_model_is_never_used_by_frozen_or_isolated_release(self):
        checkout = self.root / 'source-checkout'
        legacy = checkout / 'models/m2m100-int8'
        legacy.mkdir(parents=True)
        for name in prepare_translation.RUNTIME_FILES:
            (legacy / name).write_bytes(b'legacy fixture')
        (legacy / 'ready.json').write_text(json.dumps({'revision': prepare_translation.REVISION}), encoding='utf-8')
        filename = Path(prepare_translation.__file__)
        for frozen, isolated, expected in [(False, False, legacy), (True, False, self.model), (False, True, self.model)]:
            paths = ModuleType('app_paths')
            paths.DATA_DIR = self.data
            paths.FROZEN = frozen
            paths.MODEL_DIR = self.model
            paths.MODEL_DOWNLOAD_DIR = self.downloads
            paths.RESOURCE_ROOT = self.root / 'program'
            paths.SOURCE_ROOT = checkout
            spec = importlib.util.spec_from_file_location('_lst_test_preparation', filename)
            module = importlib.util.module_from_spec(spec)
            with patch.dict(sys.modules, {'app_paths': paths}), patch.dict(os.environ):
                os.environ.pop('LST_DATA_DIR', None)
                if isolated:
                    os.environ['LST_DATA_DIR'] = str(self.data)
                spec.loader.exec_module(module)
            self.assertEqual(module.MODEL_DIR, expected)

    def test_nonobject_or_invalid_manifest_is_repairable_instead_of_crashing(self):
        self.model.mkdir(parents=True)
        for content in ('[]', 'null', '1', '"text"', '{invalid'):
            (self.model / 'ready.json').write_text(content, encoding='utf-8')
            self.assertFalse(prepare_translation.model_ready(self.model), content)

    def test_retry_archives_incomplete_target_without_overwriting_old_backup(self):
        self.model.mkdir(parents=True)
        (self.model / 'keep.txt').write_text('incomplete data', encoding='utf-8')
        old_backup = self.model.with_name('m2m100-int8.incomplete')
        old_backup.mkdir()
        (old_backup / 'older.txt').write_text('older data', encoding='utf-8')
        result = prepare_translation.prepare(lambda text: None)
        self.assertEqual(result, self.model)
        self.assertTrue(prepare_translation.model_ready(self.model))
        self.assertTrue((self.model / 'LICENSE').is_file())
        self.assertEqual((self.model.with_name('m2m100-int8.incomplete-1') / 'keep.txt').read_text(), 'incomplete data')
        self.assertEqual((old_backup / 'older.txt').read_text(), 'older data')
        self.session.get.assert_not_called()
        self.assertFalse(self.session.trust_env)

    def test_cancel_before_conversion_keeps_incomplete_target_untouched(self):
        self.model.mkdir(parents=True)
        (self.model / 'keep.txt').write_text('keep', encoding='utf-8')

        def progress(message):
            if 'INT8' in message:
                raise InterruptedError()

        with self.assertRaises(InterruptedError):
            prepare_translation.prepare(progress)
        self.converter_factory.assert_not_called()
        self.assertEqual((self.model / 'keep.txt').read_text(), 'keep')
        self.assertFalse((self.model / 'ready.json').exists())

    def test_invalid_download_is_not_promoted_or_converted(self):
        (self.downloads / 'pytorch_model.bin').write_bytes(b'corrupt cached checkpoint')
        response = MagicMock()
        response.__enter__.return_value = response
        response.iter_content.return_value = [b'corrupt downloaded checkpoint']
        self.session.get.return_value = response
        with self.assertRaisesRegex(RuntimeError, '検証に失敗'):
            prepare_translation.prepare(lambda text: None)
        self.converter_factory.assert_not_called()
        self.assertFalse(self.model.exists())
        self.assertEqual((self.downloads / 'pytorch_model.bin').read_bytes(), b'corrupt cached checkpoint')


if __name__ == '__main__':
    unittest.main()
