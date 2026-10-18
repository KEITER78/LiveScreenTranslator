# -*- coding: utf-8 -*-
# Copyright (c) 2026 KEITER78
import sys
from PySide6.QtWidgets import QApplication
from app_window import MainWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
