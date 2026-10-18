# Copyright (c) 2026 KEITER78
from PIL import ImageGrab
from PySide6.QtCore import QRect, QSettings, QThread, QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QWidget, QPushButton, QVBoxLayout, QHBoxLayout,
    QLabel, QTextEdit, QComboBox, QMessageBox, QFontDialog, QCheckBox, QSpinBox)

from languages import LANGUAGES
from local_translation import LocalTranslator
from ocr_service import OcrService
from prepare_translation import MODEL_DIR, model_ready, prepare
from overlays import SelectionOverlay, TranslationOverlay


class TranslationTask(QThread):
    progress = Signal(str)
    result = Signal(object)
    failed = Signal(str)

    def __init__(self, translator, ocr, source, target, engine, text=None,
                 bbox=None, previous=None, preparing=False, parent=None):
        super().__init__(parent)
        self.translator, self.ocr = translator, ocr
        self.source, self.target, self.engine = source, target, engine
        self.text, self.bbox, self.previous = text, bbox, previous
        self.preparing = preparing

    def report(self, message):
        if self.isInterruptionRequested():
            raise InterruptedError()
        self.progress.emit(message)

    def run(self):
        try:
            if self.preparing:
                prepare(self.report)
                self.result.emit(None)
                return
            text = self.text
            if self.bbox is not None:
                self.report('画面の文字を読み取り中…')
                image = ImageGrab.grab(bbox=self.bbox, all_screens=True)
                text = self.ocr.read(image, self.source, self.engine, self.report)
            text = (text or '').strip()
            key = (text, self.source, self.target, self.engine)
            if not text or key == self.previous:
                self.result.emit(None)
                return
            self.report('ローカルで翻訳中…')
            translated = self.translator.translate(text, self.source, self.target)
            self.report('翻訳完了')
            self.result.emit((key, text, translated))
        except InterruptedError:
            pass
        except Exception as error:
            self.failed.emit(str(error))


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('LiveScreenTranslator')
        self.setFont(QFont('Meiryo', 10))
        self.resize(670, 780)
        self.translator, self.ocr = LocalTranslator(), OcrService()
        self.worker = None
        self.generation = 0
        self.running = False
        self.closing = False
        self.previous = None
        self.target_rect = None
        self.overlay_font = QFont('Meiryo', 16)
        self.translation_overlay = TranslationOverlay(self.overlay_font)
        self.overlay_selection_window = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.run_auto_capture)

        self.source_combo, self.target_combo = QComboBox(), QComboBox()
        for code, name in LANGUAGES.items():
            self.source_combo.addItem(f'{name} ({code})', code)
            self.target_combo.addItem(f'{name} ({code})', code)
        self.source_combo.setCurrentIndex(self.source_combo.findData('en'))
        self.swap_button = QPushButton('⇄ 入れ替え')
        language_row = QHBoxLayout()
        language_row.addWidget(QLabel('翻訳元'))
        language_row.addWidget(self.source_combo, 1)
        language_row.addWidget(self.swap_button)
        language_row.addWidget(QLabel('翻訳先'))
        language_row.addWidget(self.target_combo, 1)
        self.prepare_button = QPushButton('翻訳モデルを準備（初回 約1.95GB）')
        self.status_label = QLabel('CPUで動作します。GPU・APIキーは不要です。')
        self.status_label.setWordWrap(True)
        self.select_button = QPushButton('翻訳範囲を選択')
        self.coords_label = QLabel('範囲が選択されていません')
        self.ocr_combo = QComboBox()
        self.ocr_combo.addItems(['Tesseract', 'EasyOCR'])
        self.overlay_checkbox = QCheckBox('オーバーレイ表示')
        self.font_button = QPushButton('フォント設定')
        self.interval_spinbox = QSpinBox()
        self.interval_spinbox.setRange(250, 10000)
        self.interval_spinbox.setValue(1000)
        self.interval_spinbox.setSuffix(' ms')
        self.start_button = QPushButton('▶ 自動翻訳を開始')
        self.stop_button = QPushButton('■ 停止')
        self.stop_button.setEnabled(False)
        self.translate_button = QPushButton('原文欄のテキストを翻訳')
        self.reset_button = QPushButton('設定を初期化')
        self.ocr_result_text = QTextEdit()
        self.ocr_result_text.setPlaceholderText('画面認識した文字、または翻訳したい文章を貼り付けてください。')
        self.translation_result_text = QTextEdit()
        self.translation_result_text.setReadOnly(True)
        self.translation_result_label = QLabel('翻訳結果')

        layout = QVBoxLayout(self)
        layout.addWidget(QLabel('ローカル翻訳・100言語対応（M2M100 INT8）'))
        layout.addLayout(language_row)
        layout.addWidget(self.prepare_button)
        layout.addWidget(self.status_label)
        layout.addWidget(self.select_button)
        layout.addWidget(self.coords_label)
        options = QHBoxLayout()
        options.addWidget(QLabel('OCR'))
        options.addWidget(self.ocr_combo)
        options.addWidget(self.overlay_checkbox)
        options.addWidget(self.font_button)
        layout.addLayout(options)
        interval = QHBoxLayout()
        interval.addWidget(QLabel('取得間隔'))
        interval.addWidget(self.interval_spinbox)
        interval.addWidget(self.start_button)
        interval.addWidget(self.stop_button)
        layout.addLayout(interval)
        layout.addWidget(QLabel('原文（編集・貼り付け可）'))
        layout.addWidget(self.ocr_result_text, 1)
        layout.addWidget(self.translate_button)
        layout.addWidget(self.translation_result_label)
        layout.addWidget(self.translation_result_text, 1)
        layout.addWidget(self.reset_button)

        self.load_settings()
        self.source_combo.currentIndexChanged.connect(self.language_changed)
        self.target_combo.currentIndexChanged.connect(self.language_changed)
        self.ocr_combo.currentIndexChanged.connect(self.language_changed)
        self.swap_button.clicked.connect(self.swap_languages)
        self.prepare_button.clicked.connect(self.prepare_model)
        self.select_button.clicked.connect(self.open_selection_overlay)
        self.start_button.clicked.connect(self.start_auto_capture)
        self.stop_button.clicked.connect(self.stop_auto_capture)
        self.translate_button.clicked.connect(self.translate_text)
        self.font_button.clicked.connect(self.open_font_dialog)
        self.overlay_checkbox.toggled.connect(self.toggle_overlay_visibility)
        self.interval_spinbox.valueChanged.connect(self.update_timer_interval)
        self.reset_button.clicked.connect(self.reset_settings)
        self.update_model_status()

    def update_model_status(self):
        ready = model_ready()
        self.prepare_button.setText('翻訳モデルは準備済み' if ready else '翻訳モデルを準備（初回 約1.95GB）')
        self.prepare_button.setEnabled(not ready and self.worker is None)

    def load_settings(self):
        old = QSettings('YourCompany', 'LiveScreenTranslator')
        old.remove('api_key')
        old.remove('trans_engine_index')
        old.sync()
        settings = QSettings('KEITER78', 'LiveScreenTranslator')
        for widget, key, default in [(self.source_combo, 'source_language', 'en'),
                                     (self.target_combo, 'target_language', 'ja')]:
            index = widget.findData(settings.value(key, default))
            widget.setCurrentIndex(max(index, 0))
        geometry = settings.value('geometry')
        if geometry:
            self.restoreGeometry(geometry)
        rect = settings.value('target_rect')
        if rect and len(rect) == 4:
            self.on_region_selected(QRect(*map(int, rect)))
        self.interval_spinbox.setValue(settings.value('update_interval', 1000, type=int))
        self.ocr_combo.setCurrentIndex(settings.value('ocr_engine_index', 0, type=int))
        self.overlay_checkbox.setChecked(settings.value('overlay_enabled', False, type=bool))
        font = settings.value('overlay_font')
        if font:
            self.overlay_font.fromString(font)
        self.translation_overlay.setFont(self.overlay_font)

    def save_settings(self):
        settings = QSettings('KEITER78', 'LiveScreenTranslator')
        settings.remove('api_key')
        settings.setValue('geometry', self.saveGeometry())
        settings.setValue('source_language', self.source_combo.currentData())
        settings.setValue('target_language', self.target_combo.currentData())
        settings.setValue('ocr_engine_index', self.ocr_combo.currentIndex())
        settings.setValue('update_interval', self.interval_spinbox.value())
        settings.setValue('overlay_enabled', self.overlay_checkbox.isChecked())
        settings.setValue('overlay_font', self.overlay_font.toString())
        if self.target_rect:
            r = self.target_rect
            settings.setValue('target_rect', [r.x(), r.y(), r.width(), r.height()])
        settings.sync()

    def language_changed(self):
        self.stop_auto_capture()
        self.previous = None
        self.translation_result_text.clear()
        self.translation_overlay.setText('')
        self.status_label.setText('言語を変更しました。読み取り言語も翻訳元に合わせます。')

    def swap_languages(self):
        source, target = self.source_combo.currentData(), self.target_combo.currentData()
        self.source_combo.setCurrentIndex(self.source_combo.findData(target))
        self.target_combo.setCurrentIndex(self.target_combo.findData(source))

    def launch_task(self, **kwargs):
        if self.worker is not None:
            return False
        generation = self.generation
        worker = TranslationTask(self.translator, self.ocr,
            self.source_combo.currentData(), self.target_combo.currentData(),
            self.ocr_combo.currentText(), parent=self, **kwargs)
        self.worker = worker
        self.translate_button.setEnabled(False)
        self.prepare_button.setEnabled(False)
        worker.progress.connect(lambda text: self.status_label.setText(text) if generation == self.generation else None)
        worker.result.connect(lambda result: self.receive_result(result, generation))
        worker.failed.connect(lambda message: self.receive_error(message, generation))
        worker.finished.connect(self.task_finished)
        worker.start()
        return True

    def receive_result(self, result, generation):
        if generation != self.generation or self.closing:
            return
        if result:
            self.previous, original, translated = result
            self.ocr_result_text.setPlainText(original)
            self.translation_result_text.setPlainText(translated)
            self.translation_overlay.setText(translated)
        self.status_label.setText('自動翻訳中' if self.running else '準備完了')

    def receive_error(self, message, generation):
        if generation == self.generation and not self.closing:
            self.stop_auto_capture()
            self.status_label.setText(message)
            self.translation_result_text.setPlainText(f'処理できませんでした:\n{message}')

    def task_finished(self):
        worker, self.worker = self.worker, None
        worker.deleteLater()
        self.translate_button.setEnabled(True)
        self.update_model_status()
        if self.closing:
            self.close()

    def prepare_model(self):
        self.stop_auto_capture()
        self.launch_task(preparing=True)

    def translate_text(self):
        if self.worker is not None:
            return
        self.stop_auto_capture()
        self.launch_task(text=self.ocr_result_text.toPlainText())

    def start_auto_capture(self):
        if self.worker is not None:
            self.status_label.setText('現在の処理が終わるまでお待ちください。')
            return
        if not model_ready():
            self.status_label.setText('先に「翻訳モデルを準備」を押してください。')
            return
        if not self.target_rect or self.target_rect.isEmpty():
            self.status_label.setText('先に翻訳範囲を選択してください。')
            return
        self.running = True
        self.previous = None
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.timer.start(self.interval_spinbox.value())
        self.toggle_overlay_visibility()
        self.run_auto_capture()

    def stop_auto_capture(self):
        self.running = False
        self.timer.stop()
        self.generation += 1
        if self.worker is not None:
            self.worker.requestInterruption()
        self.translation_overlay.hide()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def run_auto_capture(self):
        if not self.running or self.worker is not None:
            return
        r = self.target_rect
        self.launch_task(bbox=(r.x(), r.y(), r.x()+r.width(), r.y()+r.height()),
                         previous=self.previous)

    def open_selection_overlay(self):
        self.stop_auto_capture()
        self.overlay_selection_window = SelectionOverlay()
        self.overlay_selection_window.region_selected.connect(self.on_region_selected)
        self.overlay_selection_window.show()

    def on_region_selected(self, rect):
        self.target_rect = rect
        self.coords_label.setText(f'選択範囲: X:{rect.x()} Y:{rect.y()} 幅:{rect.width()} 高さ:{rect.height()}')
        self.translation_overlay.updateWidth(max(rect.width(), 200))

    def toggle_overlay_visibility(self):
        self.translation_overlay.setVisible(self.running and self.overlay_checkbox.isChecked())

    def update_timer_interval(self):
        if self.running:
            self.timer.setInterval(self.interval_spinbox.value())

    def open_font_dialog(self):
        ok, font = QFontDialog.getFont(self.overlay_font, self)
        if ok:
            self.overlay_font = font
            self.translation_overlay.setFont(font)

    def reset_settings(self):
        if QMessageBox.question(self, '設定の初期化', '表示・言語・範囲の設定を初期化しますか？') == QMessageBox.Yes:
            self.stop_auto_capture()
            self.source_combo.setCurrentIndex(self.source_combo.findData('en'))
            self.target_combo.setCurrentIndex(self.target_combo.findData('ja'))
            self.ocr_combo.setCurrentIndex(0)
            self.interval_spinbox.setValue(1000)
            self.overlay_checkbox.setChecked(False)
            self.target_rect = None
            self.coords_label.setText('範囲が選択されていません')
            QSettings('KEITER78', 'LiveScreenTranslator').clear()

    def closeEvent(self, event):
        self.stop_auto_capture()
        if self.worker is not None:
            self.closing = True
            self.status_label.setText('処理を終了しています…')
            event.ignore()
            return
        self.save_settings()
        self.translation_overlay.close()
        if self.overlay_selection_window:
            self.overlay_selection_window.close()
        event.accept()
