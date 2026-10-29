# -*- coding: utf-8 -*-
# Copyright (c) 2026 KEITER78
import sys
import argparse
import os


def main():
    # A windowed Windows executable has no console streams. Some libraries
    # still expect writable stream objects even with progress output disabled.
    if sys.stdout is None:
        sys.stdout = open(os.devnull, 'w', encoding='utf-8')
    if sys.stderr is None:
        sys.stderr = open(os.devnull, 'w', encoding='utf-8')
    parser = argparse.ArgumentParser(description='LiveScreenTranslator')
    parser.add_argument('--self-test', metavar='REPORT_JSON', help=argparse.SUPPRESS)
    parser.add_argument('--prepare-for-test', action='store_true', help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.self_test:
        from diagnostics import run_self_test
        return run_self_test(args.self_test, args.prepare_for_test)

    from PySide6.QtWidgets import QApplication, QMessageBox
    from app_version import VERSION
    from app_window import MainWindow
    from terms_dialog import ensure_binary_terms
    app = QApplication(sys.argv)
    app.setApplicationName('LiveScreenTranslator')
    app.setApplicationVersion(VERSION)
    try:
        if not ensure_binary_terms():
            return 0
    except RuntimeError as error:
        QMessageBox.critical(None, '配布ファイルの確認', str(error))
        return 1
    window = MainWindow()
    window.show()
    return app.exec()


if __name__ == '__main__':
    sys.exit(main())
