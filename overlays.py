# Copyright (c) 2026 KEITER78
from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
from PySide6.QtGui import QPainter, QColor, QPen, QMouseEvent
from PySide6.QtCore import Qt, QRect, Signal

class SelectionOverlay(QWidget):
    region_selected = Signal(QRect)
    
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        screen_geometry = QApplication.primaryScreen().geometry()
        self.setGeometry(screen_geometry)
        self.begin = None
        self.end = None

    def paintEvent(self, event):
        """描画イベント。選択範囲の見た目を作る"""
        painter = QPainter(self)
        
        # 1. まず画面全体を暗い半透明色で覆う (選択範囲外の領域)
        bg_color = QColor(0, 0, 0, 100)
        painter.fillRect(self.rect(), bg_color)
        
        # 2. ドラッグ中であれば、選択範囲を描画する
        if self.begin and self.end:
            rect = QRect(self.begin, self.end).normalized()
            
            # 3. 選択範囲の内側を、明るい半透明色で上塗りする
            # これにより、下のコンテンツが透けて見えるハイライト効果が生まれる
            selection_fill_color = QColor(100, 150, 255, 30) # 透明度の高い水色
            painter.fillRect(rect, selection_fill_color)
            
            # 4. 選択範囲の境界線を赤色で描画する
            pen = QPen(QColor("red"), 2, Qt.SolidLine)
            painter.setPen(pen)
            painter.drawRect(rect)

    def mousePressEvent(self, event):
        self.begin = event.pos()
        self.end = event.pos()
        self.update()

    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()

    def mouseReleaseEvent(self, event):
        if self.begin and self.end:
            selected_rect = QRect(self.begin, self.end).normalized()
            self.region_selected.emit(selected_rect)
        self.close()

# --- 翻訳結果表示用オーバーレイ ---
class TranslationOverlay(QWidget):
    def __init__(self, main_window_font):
        super().__init__()
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.label = QLabel("ここに翻訳結果が表示されます", self)
        self.label.setTextFormat(Qt.PlainText)
        self.label.setStyleSheet("color: white; background-color: rgba(0, 0, 0, 150); padding: 5px;")
        self.label.setFont(main_window_font)
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setWordWrap(True)
        self.label.adjustSize()
        
        layout = QVBoxLayout()
        layout.addWidget(self.label)
        self.setLayout(layout)
        self.drag_position = None

    def updateWidth(self, width):
        self.setMaximumWidth(width)

    def setText(self, text):
        self.label.setText(text)
        self.adjustSize()

    def setFont(self, font):
        self.label.setFont(font)
        self.adjustSize()

    def mousePressEvent(self, event: QMouseEvent):
        if event.button() == Qt.LeftButton:
            self.drag_position = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()

    def mouseMoveEvent(self, event: QMouseEvent):
        if event.buttons() == Qt.LeftButton and self.drag_position:
            self.move(event.globalPosition().toPoint() - self.drag_position)
            event.accept()

