# Copyright (c) 2026 KEITER78
"""First-run preparation of translation and optional OCR data."""
from PySide6.QtCore import QThread, Qt, Signal
from PySide6.QtWidgets import (QCheckBox, QComboBox, QDialog, QHBoxLayout,
    QLabel, QPlainTextEdit, QProgressBar, QPushButton, QVBoxLayout)

from languages import LANGUAGES
from prepare_translation import prepare


class SetupTask(QThread):
    progress = Signal(str)
    completed = Signal()
    failed = Signal(str)

    def __init__(self, ocr, source, engine, include_ocr=True, parent=None):
        super().__init__(parent)
        self.ocr, self.source, self.engine = ocr, source, engine
        self.include_ocr = include_ocr

    def report(self, message):
        if self.isInterruptionRequested():
            raise InterruptedError()
        self.progress.emit(message)

    def run(self):
        try:
            if self.include_ocr and hasattr(self.ocr, 'validate_setup'):
                self.report('文字認識の設定を確認しています…')
                self.ocr.validate_setup(self.source, self.engine)
            self.report('翻訳モデルを準備しています…')
            prepare(self.report)
            self.report('翻訳モデルの準備が完了しました。')
            if self.include_ocr:
                self.report('文字認識を準備しています…')
                self.ocr.prepare(self.source, self.engine, self.report)
                self.report('文字認識の準備が完了しました。')
            self.completed.emit()
        except InterruptedError:
            pass
        except Exception as error:
            self.failed.emit(str(error))


class SetupDialog(QDialog):
    setup_finished = Signal(str, bool)

    def __init__(self, ocr, source, engine='EasyOCR', parent=None):
        super().__init__(parent)
        self.setWindowTitle('初回セットアップ')
        self.setWindowModality(Qt.WindowModal)
        self.resize(560, 420)
        self.ocr, self.source = ocr, source
        self.worker = None
        self.close_requested = False
        self.succeeded = False
        self.last_error = ''

        introduction = QLabel('翻訳モデルと、使用する言語の文字認識を準備します。\n'
            '初回はインターネット接続と数GBの空き容量が必要です。\n'
            '翻訳モデルの取得量は約1.95GBです。')
        introduction.setWordWrap(True)
        self.language_label = QLabel(f'文字認識する言語: {LANGUAGES.get(source, source)}')
        self.include_ocr = QCheckBox('画面の文字認識も準備する')
        self.include_ocr.setChecked(True)
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(['EasyOCR', 'Tesseract'])
        self.engine_combo.setCurrentText(engine)
        self.engine_combo.setToolTip('EasyOCRは文字認識アプリの別途インストールが不要です。')
        self.engine_hint = QLabel()
        self.engine_hint.setWordWrap(True)
        self.state_label = QLabel('「セットアップを開始」を押してください。')
        self.state_label.setTextFormat(Qt.PlainText)
        self.state_label.setWordWrap(True)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(100)
        self.log.hide()
        self.start_button = QPushButton('セットアップを開始')
        self.close_button = QPushButton('閉じる')

        layout = QVBoxLayout(self)
        layout.addWidget(introduction)
        layout.addSpacing(8)
        layout.addWidget(self.language_label)
        options = QHBoxLayout()
        options.addWidget(self.include_ocr)
        options.addWidget(self.engine_combo)
        layout.addLayout(options)
        layout.addWidget(self.engine_hint)
        layout.addSpacing(8)
        layout.addWidget(self.state_label)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.log, 1)
        layout.addStretch()
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.close_button)
        layout.addLayout(buttons)

        self.engine_combo.currentTextChanged.connect(self.update_hint)
        self.include_ocr.toggled.connect(self.update_hint)
        self.start_button.clicked.connect(self.start_setup)
        self.close_button.clicked.connect(self.reject)
        self.update_hint()

    def update_hint(self):
        enabled = self.include_ocr.isChecked()
        self.engine_combo.setEnabled(enabled and self.worker is None)
        if not enabled:
            text = '文字認識を使わず、原文欄に貼り付けて翻訳できます。'
        elif self.engine_combo.currentText() == 'EasyOCR':
            text = 'EasyOCRの認識モデルを取得します。別のOCRアプリは不要です。'
        else:
            text = 'Tesseract本体は別途インストール済みである必要があります。認識データを取得します。'
        self.engine_hint.setText(text)

    def start_setup(self):
        if self.worker is not None:
            return
        self.succeeded = False
        self.last_error = ''
        self.close_requested = False
        self.start_button.setEnabled(False)
        self.include_ocr.setEnabled(False)
        self.engine_combo.setEnabled(False)
        self.close_button.setText('キャンセル')
        self.state_label.setText('セットアップ中です…')
        self.progress_bar.show()
        self.log.clear()
        self.log.show()
        self.worker = SetupTask(self.ocr, self.source,
            self.engine_combo.currentText(), self.include_ocr.isChecked(), self)
        self.worker.progress.connect(self.report)
        self.worker.completed.connect(self.mark_completed)
        self.worker.failed.connect(self.mark_failed)
        self.worker.finished.connect(self.worker_finished)
        self.worker.start()

    def report(self, message):
        self.log.appendPlainText(message)
        if not self.close_requested:
            self.state_label.setText(message)

    def mark_completed(self):
        self.succeeded = True

    def mark_failed(self, message):
        self.last_error = message

    def worker_finished(self):
        worker, self.worker = self.worker, None
        worker.deleteLater()
        self.progress_bar.hide()
        self.close_button.setEnabled(True)
        self.close_button.setText('閉じる')
        self.include_ocr.setEnabled(True)
        self.update_hint()
        if self.close_requested:
            super().reject()
        elif self.succeeded:
            self.state_label.setText('セットアップが完了しました。この画面を閉じて翻訳を開始できます。')
            self.start_button.hide()
            self.include_ocr.setEnabled(False)
            self.engine_combo.setEnabled(False)
            self.setup_finished.emit(self.engine_combo.currentText(), self.include_ocr.isChecked())
        else:
            self.state_label.setText('セットアップできませんでした。\n' + self.last_error)
            self.start_button.setText('もう一度試す')
            self.start_button.setEnabled(True)

    def request_close(self):
        self.close_requested = True
        self.worker.requestInterruption()
        self.state_label.setText('停止処理中です。現在の処理が終了するまでお待ちください。')
        self.close_button.setEnabled(False)

    def reject(self):
        if self.worker is not None:
            self.request_close()
        else:
            super().reject()

    def closeEvent(self, event):
        if self.worker is not None:
            self.request_close()
            event.ignore()
        else:
            super().closeEvent(event)
