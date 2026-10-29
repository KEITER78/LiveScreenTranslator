# Copyright (c) 2026 KEITER78
"""Binary terms acceptance is explicit, versioned and isolated from real settings."""
import hashlib
import os
os.environ['QT_QPA_PLATFORM'] = 'offscreen'

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PySide6.QtCore import QEvent, QUrl
from PySide6.QtWidgets import QApplication, QDialog, QTextBrowser

import terms_dialog


class FakeSettings:
    def __init__(self):
        self.values = {}
        self.sync_count = 0

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value

    def sync(self):
        self.sync_count += 1


class BinaryTermsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(
            prefix='lst-terms-tests-', dir=Path(__file__).resolve().parent)
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        self.bundle = self.root / 'program'
        self.bundle.mkdir()
        self.resources = self.root / 'resources'
        self.resources.mkdir()
        self.path = self.bundle / 'BINARY_TERMS.md'
        self.text = '# 同梱ランタイムの利用条件\n\n本体はMIT、QtはLGPLです。\nIntelとMicrosoftの部品には各原文の条件が適用されます。\n'
        self.path.write_text(self.text, encoding='utf-8')
        self.settings = FakeSettings()
        for replacement in (
            patch.object(terms_dialog, 'FROZEN', True),
            patch.object(terms_dialog, 'RESOURCE_ROOT', self.resources),
            patch.object(terms_dialog.sys, 'executable', str(self.bundle / 'LiveScreenTranslator.exe')),
            patch.object(terms_dialog, 'application_settings', return_value=self.settings),
        ):
            replacement.start()
            self.addCleanup(replacement.stop)

    def tearDown(self):
        self.app.sendPostedEvents(None, QEvent.DeferredDelete)
        self.app.processEvents()

    @staticmethod
    def agree(dialog):
        dialog.consent_checkbox.setChecked(True)
        dialog.accept()
        return dialog.result()

    def test_source_execution_skips_ui_files_and_settings(self):
        with patch.object(terms_dialog, 'FROZEN', False), \
                patch.object(terms_dialog, '_terms_path') as find_path, \
                patch.object(terms_dialog, 'BinaryTermsDialog') as dialog:
            self.assertTrue(terms_dialog.ensure_binary_terms(self.settings))
        find_path.assert_not_called()
        dialog.assert_not_called()
        self.assertEqual(self.settings.values, {})

    def test_first_acceptance_is_unchecked_and_stored_only_after_explicit_agreement(self):
        observed = []

        def agree(dialog):
            observed.append((dialog.consent_checkbox.isChecked(), dialog.accept_button.isEnabled()))
            dialog.accept()
            self.assertNotEqual(dialog.result(), QDialog.Accepted)
            dialog.consent_checkbox.setChecked(True)
            self.assertTrue(dialog.accept_button.isEnabled())
            dialog.accept()
            return dialog.result()

        with patch.object(terms_dialog.BinaryTermsDialog, 'exec', agree):
            self.assertTrue(terms_dialog.ensure_binary_terms(self.settings))
        self.assertEqual(observed, [(False, False)])
        self.assertEqual(self.settings.values[terms_dialog.ACCEPTED_TERMS_KEY],
                         hashlib.sha256(self.path.read_bytes()).hexdigest())
        self.assertEqual(self.settings.sync_count, 1)

    def test_rejection_does_not_store_agreement(self):
        with patch.object(terms_dialog.BinaryTermsDialog, 'exec', return_value=QDialog.Rejected):
            self.assertFalse(terms_dialog.ensure_binary_terms(self.settings))
        self.assertEqual(self.settings.values, {})
        self.assertEqual(self.settings.sync_count, 0)

    def test_accepted_result_without_checked_box_is_not_consent(self):
        with patch.object(terms_dialog.BinaryTermsDialog, 'exec', return_value=QDialog.Accepted):
            self.assertFalse(terms_dialog.ensure_binary_terms(self.settings))
        self.assertEqual(self.settings.values, {})

    def test_current_digest_skips_repeat_prompt(self):
        self.settings.values[terms_dialog.ACCEPTED_TERMS_KEY] = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with patch.object(terms_dialog, 'BinaryTermsDialog') as dialog:
            self.assertTrue(terms_dialog.ensure_binary_terms(self.settings))
        dialog.assert_not_called()
        self.assertEqual(self.settings.sync_count, 0)

    def test_changed_terms_require_new_consent(self):
        self.settings.values[terms_dialog.ACCEPTED_TERMS_KEY] = 'old-digest'
        with patch.object(terms_dialog.BinaryTermsDialog, 'exec', self.agree):
            self.assertTrue(terms_dialog.ensure_binary_terms(self.settings))
        self.assertNotEqual(self.settings.values[terms_dialog.ACCEPTED_TERMS_KEY], 'old-digest')

    def test_default_settings_use_application_profile_factory(self):
        with patch.object(terms_dialog.BinaryTermsDialog, 'exec', self.agree):
            self.assertTrue(terms_dialog.ensure_binary_terms())
        terms_dialog.application_settings.assert_called_once_with()

    def test_missing_terms_file_is_an_error(self):
        self.path.unlink()
        with self.assertRaisesRegex(RuntimeError, 'BINARY_TERMS.md'):
            terms_dialog.ensure_binary_terms(self.settings)
        self.assertEqual(self.settings.values, {})

    def test_empty_or_invalid_utf8_terms_are_not_accepted(self):
        for content in (b'', b' \n\t', b'\xff\xfeinvalid'):
            self.path.write_bytes(content)
            with self.assertRaisesRegex(RuntimeError, 'BINARY_TERMS.md'):
                terms_dialog.ensure_binary_terms(self.settings)
        self.assertEqual(self.settings.values, {})

    def test_resource_directory_fallback(self):
        self.path.unlink()
        (self.resources / 'BINARY_TERMS.md').write_text(self.text, encoding='utf-8')
        with patch.object(terms_dialog.BinaryTermsDialog, 'exec', self.agree):
            self.assertTrue(terms_dialog.ensure_binary_terms(self.settings))

    def test_missing_linked_license_is_an_error(self):
        self.path.write_text(self.text + '\n[原文](third_party_licenses/missing/LICENSE.txt)', encoding='utf-8')
        with self.assertRaisesRegex(RuntimeError, '原文が見つかりません'):
            terms_dialog.ensure_binary_terms(self.settings)

    def test_original_license_link_opens_complete_text_in_local_viewer(self):
        license_path = self.bundle / 'third_party_licenses/intel/LICENSE.txt'
        license_path.parent.mkdir(parents=True)
        original = 'Original license: first line\nComplete terms: final line\n'
        license_path.write_text(original, encoding='utf-8')
        text = self.text + '\n[原文](third_party_licenses/intel/LICENSE.txt)'
        self.path.write_text(text, encoding='utf-8')
        dialog = terms_dialog.BinaryTermsDialog(self.path, text)
        viewed = []

        def inspect_viewer(viewer):
            viewed.append(viewer.findChild(QTextBrowser).toPlainText())
            return QDialog.Rejected

        with patch.object(QDialog, 'exec', inspect_viewer):
            dialog.open_link(QUrl('third_party_licenses/intel/LICENSE.txt'))
        self.assertEqual(viewed, [original])
        self.assertFalse(dialog.consent_checkbox.isChecked())
        dialog.deleteLater()

    def test_dialog_preserves_mit_and_lgpl_rights_scope(self):
        dialog = terms_dialog.BinaryTermsDialog(self.path, self.text)
        self.assertIn('MIT', dialog.introduction.text())
        self.assertIn('LGPL', dialog.introduction.text())
        self.assertIn('権利を変更しません', dialog.introduction.text())
        self.assertIn('IntelとMicrosoft', dialog.browser.toPlainText())
        dialog.deleteLater()


if __name__ == '__main__':
    unittest.main()
