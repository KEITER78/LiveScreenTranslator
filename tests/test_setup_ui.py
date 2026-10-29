# Copyright (c) 2026 KEITER78
"""GUI lifecycle tests; no downloads, screenshots or real registry settings."""
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from pathlib import Path
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent, QSettings
from PySide6.QtWidgets import QApplication, QLabel
from shiboken6 import isValid

import app_window
import setup_dialog


class FakeOcr:
    def __init__(self):
        self.ready = False
        self.prepared = []

    def is_ready(self, source, engine):
        return self.ready

    def prepare(self, source, engine, progress):
        progress('認識モデルを準備しています。')
        self.prepared.append((source, engine))
        self.ready = True


class FakeTranslator:
    def translate(self, text, source, target):
        return '翻訳: ' + text


class SetupUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory(
            prefix='lst-ui-tests-', dir=Path(__file__).resolve().parent)
        self.addCleanup(self.directory.cleanup)
        self.widgets = []
        self.model_is_ready = True
        replacements = [
            patch.object(app_window, 'QSettings', self.settings),
            patch.object(app_window, 'model_ready', lambda: self.model_is_ready),
            patch.object(app_window, 'OcrService', FakeOcr),
            patch.object(app_window, 'LocalTranslator', FakeTranslator),
        ]
        for replacement in replacements:
            replacement.start()
            self.addCleanup(replacement.stop)

    def settings(self, organization, application):
        path = Path(self.directory.name) / f'{organization}-{application}.ini'
        return QSettings(str(path), QSettings.IniFormat)

    def wait_for(self, predicate, timeout=3):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            self.app.processEvents()
            if predicate():
                return
            time.sleep(.005)
        self.fail('The expected Qt lifecycle event did not complete.')

    def window(self):
        window = app_window.MainWindow()
        self.widgets.append(window)
        return window

    def dialog(self):
        dialog = setup_dialog.SetupDialog(FakeOcr(), 'en')
        self.widgets.append(dialog)
        dialog.show()
        return dialog

    def tearDown(self):
        for widget in reversed(self.widgets):
            if isValid(widget):
                widget.close()
        self.wait_for(lambda: all(not isValid(widget) or not widget.isVisible()
                                  for widget in self.widgets))
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()

    def test_ready_daily_window_has_no_setup_noise(self):
        window = self.window()
        window.show()
        self.app.processEvents()
        captions = [label.text() for label in window.findChildren(QLabel)]
        self.assertFalse(any('CPUで動作' in caption or '100言語対応' in caption
                             or '翻訳モデルは準備済み' in caption for caption in captions))
        self.assertTrue(window.prepare_button.isHidden())
        self.assertTrue(window.status_label.isHidden())
        self.assertTrue(window.setup_button.isVisible())
        self.assertEqual(window.ocr_combo.currentText(), 'EasyOCR')
        self.assertIsNone(window.setup_dialog)

    def test_first_run_opens_setup_only_after_window_is_shown(self):
        self.model_is_ready = False
        window = self.window()
        self.app.processEvents()
        self.assertIsNone(window.setup_dialog)
        window.show()
        self.wait_for(lambda: window.setup_dialog is not None)
        self.assertTrue(window.setup_dialog.isVisible())
        self.assertIsNone(window.setup_dialog.worker)
        self.assertFalse(window.launch_task(text='Do not start during setup.'))
        window.setup_dialog.reject()
        self.wait_for(lambda: window.setup_dialog is None)
        self.assertTrue(window.prepare_button.isVisible())

    def test_saved_ocr_choice_and_language_are_preserved(self):
        saved = self.settings('KEITER78', 'LiveScreenTranslator')
        saved.setValue('ocr_engine_index', 0)
        saved.setValue('source_language', 'fr')
        saved.sync()
        window = self.window()
        self.assertEqual(window.ocr_combo.currentText(), 'Tesseract')
        self.assertEqual(window.source_combo.currentData(), 'fr')

    def test_success_prepares_translation_and_selected_ocr(self):
        dialog = self.dialog()
        completed = []
        dialog.setup_finished.connect(lambda engine, included: completed.append((engine, included)))
        with patch.object(setup_dialog, 'prepare', lambda report: report('取得中')):
            dialog.start_setup()
            self.wait_for(lambda: dialog.worker is None)
        self.assertTrue(dialog.succeeded)
        self.assertEqual(dialog.ocr.prepared, [('en', 'EasyOCR')])
        self.assertEqual(completed, [('EasyOCR', True)])
        self.assertTrue(dialog.start_button.isHidden())
        self.assertFalse(dialog.include_ocr.isEnabled())
        self.assertFalse(dialog.engine_combo.isEnabled())

    def test_first_setup_updates_main_controls_and_ocr_selection(self):
        self.model_is_ready = False
        window = self.window()
        window.show()
        self.wait_for(lambda: window.setup_dialog is not None)
        dialog = window.setup_dialog
        dialog.engine_combo.setCurrentText('Tesseract')

        def prepare_model(report):
            self.model_is_ready = True

        with patch.object(setup_dialog, 'prepare', prepare_model):
            dialog.start_setup()
            self.wait_for(lambda: dialog.worker is None)
        self.assertTrue(window.prepare_button.isHidden())
        self.assertEqual(window.ocr_combo.currentText(), 'Tesseract')
        dialog.close()
        self.wait_for(lambda: window.setup_dialog is None)
        self.assertTrue(window.setup_button.isEnabled())

    def test_failure_can_be_retried(self):
        dialog = self.dialog()
        with patch.object(setup_dialog, 'prepare', side_effect=RuntimeError('接続できません')):
            dialog.start_setup()
            self.wait_for(lambda: dialog.worker is None)
        self.assertIn('接続できません', dialog.state_label.text())
        self.assertTrue(dialog.start_button.isEnabled())
        self.assertFalse(dialog.succeeded)
        with patch.object(setup_dialog, 'prepare', lambda report: None):
            dialog.start_setup()
            self.wait_for(lambda: dialog.worker is None)
        self.assertTrue(dialog.succeeded)

    def test_invalid_ocr_choice_fails_before_translation_download(self):
        dialog = self.dialog()
        dialog.ocr.validate_setup = lambda source, engine: (_ for _ in ()).throw(
            RuntimeError('この言語は文字認識に対応していません'))
        with patch.object(setup_dialog, 'prepare') as prepare:
            dialog.start_setup()
            self.wait_for(lambda: dialog.worker is None)
        prepare.assert_not_called()
        self.assertIn('対応していません', dialog.state_label.text())

    def test_skipping_ocr_keeps_pasted_translation_available(self):
        dialog = self.dialog()
        dialog.include_ocr.setChecked(False)
        completed = []
        dialog.setup_finished.connect(lambda engine, included: completed.append(included))
        with patch.object(setup_dialog, 'prepare', lambda report: None):
            dialog.start_setup()
            self.wait_for(lambda: dialog.worker is None)
        self.assertEqual(dialog.ocr.prepared, [])
        self.assertEqual(completed, [False])
        dialog.close()
        window = self.window()
        window.ocr_result_text.setPlainText('Text without OCR')
        window.translate_text()
        self.wait_for(lambda: window.worker is None)
        self.assertEqual(window.translation_result_text.toPlainText(), '翻訳: Text without OCR')

    def test_main_close_waits_for_setup_thread_to_stop(self):
        window = self.window()
        window.show()
        window.open_setup()
        dialog = window.setup_dialog
        started = threading.Event()

        def slow_prepare(report):
            started.set()
            while True:
                report('取得中')
                time.sleep(.01)

        with patch.object(setup_dialog, 'prepare', slow_prepare):
            dialog.start_setup()
            self.wait_for(started.is_set)
            window.close()
            self.assertTrue(dialog.close_requested)
            self.wait_for(lambda: window.setup_dialog is None and not window.isVisible())
        self.assertEqual(dialog.ocr.prepared if isValid(dialog) else [], [])


if __name__ == '__main__':
    unittest.main()
