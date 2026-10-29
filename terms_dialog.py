# Copyright (c) 2026 KEITER78
"""One-time review of the binary bundle's runtime-specific terms."""
import hashlib
from pathlib import Path
import re
import sys

from PySide6.QtCore import QSettings, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (QApplication, QCheckBox, QDialog, QHBoxLayout,
    QLabel, QMessageBox, QPushButton, QTextBrowser, QVBoxLayout)

from app_paths import FROZEN, RESOURCE_ROOT, application_settings

ACCEPTED_TERMS_KEY = 'binary_terms_sha256'


def _terms_path():
    for directory in (Path(sys.executable).resolve().parent, RESOURCE_ROOT):
        path = directory / 'BINARY_TERMS.md'
        if path.is_file():
            return path
    raise RuntimeError('BINARY_TERMS.mdが見つかりません。配布ZIPをすべて展開してから起動してください。')


def _local_document(url, terms_path):
    """Resolve bundle-relative links, without allowing arbitrary local files."""
    if url.scheme() and not url.isLocalFile():
        return None
    roots = [terms_path.parent.resolve(), Path(sys.executable).resolve().parent,
             RESOURCE_ROOT.resolve()]
    candidates = ([Path(url.toLocalFile())] if url.isLocalFile() else
                  [directory / url.path() for directory in roots])
    for candidate in candidates:
        candidate = candidate.resolve()
        if not any(candidate.is_relative_to(directory) for directory in roots):
            continue
        if candidate.is_file() and candidate.stat().st_size > 0:
            return candidate
    return None


def _validate_local_links(text, terms_path):
    for target in re.findall(r'\]\(([^\s)]+)\)', text):
        url = QUrl(target)
        if url.scheme() in ('http', 'https') or not url.path():
            continue
        if _local_document(url, terms_path) is None:
            raise RuntimeError('利用条件の原文が見つかりません。配布ZIPをすべて展開してください。\n' + target)


class BinaryTermsDialog(QDialog):
    def __init__(self, terms_path, text, parent=None):
        super().__init__(parent)
        self.terms_path = Path(terms_path)
        self.setWindowTitle('利用条件の確認')
        self.setFont(QFont('Meiryo', 10))
        self.resize(760, 620)
        self.introduction = QLabel('本体はMITライセンスです。同梱ランタイムには提供元の利用条件が適用されます。\n'
            'これらの条件は、本体のMITやQt等のLGPLに基づく権利を変更しません。')
        self.introduction.setWordWrap(True)
        self.browser = QTextBrowser()
        self.browser.setOpenLinks(False)
        self.browser.setOpenExternalLinks(False)
        self.browser.document().setBaseUrl(QUrl.fromLocalFile(str(self.terms_path.parent) + '/'))
        self.browser.setMarkdown(text)
        self.browser.anchorClicked.connect(self.open_link)
        self.consent_checkbox = QCheckBox('同梱ランタイムの利用条件を確認し、同意します。')
        self.consent_checkbox.setChecked(False)
        self.accept_button = QPushButton('同意して続ける')
        self.accept_button.setEnabled(False)
        self.accept_button.setDefault(True)
        self.reject_button = QPushButton('終了')
        self.reject_button.setAutoDefault(False)
        self.consent_checkbox.toggled.connect(self.accept_button.setEnabled)
        self.accept_button.clicked.connect(self.accept)
        self.reject_button.clicked.connect(self.reject)
        layout = QVBoxLayout(self)
        layout.addWidget(self.introduction)
        layout.addWidget(self.browser, 1)
        layout.addWidget(self.consent_checkbox)
        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.reject_button)
        buttons.addWidget(self.accept_button)
        layout.addLayout(buttons)

    def accept(self):
        if self.consent_checkbox.isChecked():
            super().accept()

    def open_link(self, url):
        if url.isRelative() and not url.path() and url.hasFragment():
            self.browser.scrollToAnchor(url.fragment())
            return
        if url.scheme() in ('http', 'https'):
            QDesktopServices.openUrl(url)
            return
        path = _local_document(url, self.terms_path)
        if path is None:
            QMessageBox.warning(self, '文書を開けません', '同梱のライセンス文書が見つかりません。')
            return
        try:
            text = path.read_text(encoding='utf-8-sig', errors='replace')
        except OSError:
            QMessageBox.warning(self, '文書を開けません', 'ライセンス文書を読み込めませんでした。')
            return
        viewer = QDialog(self)
        viewer.setWindowTitle(path.name)
        viewer.resize(760, 620)
        browser = QTextBrowser()
        browser.setOpenLinks(False)
        browser.setOpenExternalLinks(False)
        browser.anchorClicked.connect(self.open_link)
        if path.suffix.lower() == '.md':
            browser.document().setBaseUrl(QUrl.fromLocalFile(str(path.parent) + '/'))
            browser.setMarkdown(text)
        elif path.suffix.lower() in ('.html', '.htm'):
            browser.document().setBaseUrl(QUrl.fromLocalFile(str(path.parent) + '/'))
            browser.setHtml(text)
        else:
            browser.setPlainText(text)
        button = QPushButton('閉じる')
        button.clicked.connect(viewer.accept)
        layout = QVBoxLayout(viewer)
        layout.addWidget(browser, 1)
        layout.addWidget(button)
        viewer.exec()
        viewer.deleteLater()


def ensure_binary_terms(settings=None):
    """Return False on rejection; source execution never prompts or writes."""
    if not FROZEN:
        return True
    path = _terms_path()
    try:
        content = path.read_bytes()
        text = content.decode('utf-8-sig')
    except (OSError, UnicodeError) as error:
        raise RuntimeError('BINARY_TERMS.mdを読み込めません。配布ZIPを展開し直してください。') from error
    if not text.strip():
        raise RuntimeError('BINARY_TERMS.mdが空です。配布ZIPを展開し直してください。')
    _validate_local_links(text, path)
    digest = hashlib.sha256(content).hexdigest()
    if settings is None:
        settings = application_settings()
    if settings.value(ACCEPTED_TERMS_KEY, '') == digest:
        return True
    if QApplication.instance() is None:
        raise RuntimeError('利用条件の確認画面を開くにはアプリから起動してください。')
    dialog = BinaryTermsDialog(path, text)
    try:
        accepted = (dialog.exec() == QDialog.Accepted
                    and dialog.consent_checkbox.isChecked())
        if not accepted:
            return False
        settings.setValue(ACCEPTED_TERMS_KEY, digest)
        settings.sync()
        if hasattr(settings, 'status') and settings.status() != QSettings.NoError:
            raise RuntimeError('利用条件への同意を保存できませんでした。保存先のアクセス権を確認してください。')
        return True
    finally:
        dialog.deleteLater()
