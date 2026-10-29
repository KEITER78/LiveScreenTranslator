# Copyright (c) 2026 KEITER78
"""Opt-in release checks with isolated settings and synthetic input only."""
import io
import json
from pathlib import Path
import time
import traceback


def run_self_test(report_filename, prepare=False):
    report_path = Path(report_filename).resolve()
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report = {'passed': False}
    window = None
    try:
        import os
        if not os.environ.get('LST_DATA_DIR'):
            raise RuntimeError('Self-test requires an explicitly isolated LST_DATA_DIR.')
        import ctranslate2
        import easyocr
        import torch
        from PySide6.QtCore import QBuffer, QIODevice, QSettings, Qt
        from PySide6.QtGui import QColor, QFont, QFontDatabase, QImage, QPainter
        from PySide6.QtWidgets import QApplication, QLabel
        from PIL import Image
        import app_window
        from app_paths import DATA_DIR, FROZEN, MODEL_DIR
        from app_version import VERSION
        from local_translation import LocalTranslator
        from prepare_translation import model_ready

        report.update(version=VERSION, frozen=FROZEN, python=__import__('sys').version.split()[0],
                      ctranslate2=ctranslate2.__version__, torch=torch.__version__,
                      data_directory=str(DATA_DIR))
        settings_dir = DATA_DIR / 'diagnostic-settings'
        settings_dir.mkdir(parents=True, exist_ok=True)
        def settings(organization, application):
            return QSettings(str(settings_dir / f'{organization}-{application}.ini'), QSettings.IniFormat)
        app_window.QSettings = settings
        app = QApplication.instance() or QApplication([])
        # The offscreen Qt platform does not enumerate Windows fonts itself.
        # Load the OS font for a synthetic test image; it is never distributed.
        font_directory = Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts'
        for font_name in ('arial.ttf', 'meiryo.ttc'):
            system_font = font_directory / font_name
            if system_font.is_file():
                QFontDatabase.addApplicationFont(str(system_font))
        if FROZEN:
            from terms_dialog import _terms_path, _validate_local_links
            terms_file = _terms_path()
            _validate_local_links(terms_file.read_text(encoding='utf-8'), terms_file)
            report['binary_terms_and_originals_available'] = True
        window = app_window.MainWindow()
        window.setAttribute(Qt.WA_DontShowOnScreen)
        window.show()
        app.processEvents()
        app.processEvents()
        assert window.source_combo.count() == window.target_combo.count() == 100
        labels = [label.text() for label in window.findChildren(QLabel)]
        assert not any('GPU・APIキー' in text or '100言語対応' in text for text in labels)
        report['first_run_dialog'] = window.setup_dialog is not None
        report['ocr_default'] = window.ocr_combo.currentText()
        if prepare:
            dialog = window.setup_dialog
            if dialog is None:
                window.open_setup()
                dialog = window.setup_dialog
            dialog.start_setup()
            started = time.monotonic()
            while dialog.worker is not None:
                app.processEvents()
                if time.monotonic() - started > 900:
                    raise TimeoutError('Setup did not finish within the release-test timeout.')
                time.sleep(0.02)
            app.processEvents()
            assert dialog.succeeded, dialog.last_error
            dialog.accept()
            app.processEvents()
            report['setup_completed'] = True
        elif window.setup_dialog is not None:
            window.setup_dialog.reject()
            app.processEvents()

        report['model_ready'] = model_ready()
        if model_ready():
            translator = LocalTranslator()
            results = []
            for source, target, text in [('en', 'ja', 'Please close the window.'),
                                         ('fr', 'de', 'Bonjour. Comment allez-vous ?')]:
                translated = translator.translate(text, source, target)
                assert translated.strip()
                results.append({'source': source, 'target': target, 'output': translated})
            assert '窓' in results[0]['output']
            report['translations'] = results

        ocr = window.ocr
        if ocr.is_ready('en', 'EasyOCR'):
            image = QImage(1000, 120, QImage.Format_RGB32)
            image.fill(QColor('white'))
            painter = QPainter(image)
            painter.setPen(QColor('black'))
            painter.setFont(QFont('Arial', 26))
            painter.drawText(15, 70, 'Please close the window.')
            painter.end()
            image.save(str(report_path.with_name(report_path.stem + '-ocr.png')))
            buffer = QBuffer()
            buffer.open(QIODevice.WriteOnly)
            assert image.save(buffer, 'PNG')
            pil = Image.open(io.BytesIO(bytes(buffer.data()))).convert('RGB')
            recognized = ocr.read(pil, 'en', 'EasyOCR')
            report['synthetic_ocr'] = recognized
            assert 'window' in recognized.lower(), recognized
        overlay = window.translation_overlay
        overlay.setText('<b>plain text</b>')
        assert overlay.label.textFormat() == Qt.PlainText
        assert overlay.layout().count() == 1
        assert window.grab().save(str(report_path.with_suffix('.png')))
        report['passed'] = True
        return_code = 0
    except BaseException:
        report['error'] = traceback.format_exc()
        return_code = 1
    finally:
        if window is not None:
            window.close()
            while (window.worker is not None or
                   (window.setup_dialog is not None and window.setup_dialog.worker is not None)):
                app.processEvents()
                time.sleep(0.02)
            window.close()
            app.processEvents()
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    return return_code
