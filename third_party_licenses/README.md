# 第三者ライセンス・通知の原文

44パッケージに対応するライセンス情報と、その環境から複製した通知類59文書を提供します（確認日: 2026-10-19）。モデルと推論の上流許諾文も保持しています。複製先は[原文一覧](../dependency-licenses.json)、依存パッケージは[固定版一覧](../requirements-lock.txt)と[第三者通知](../THIRD_PARTY_NOTICES.md)に記載しています。

`common/` には同じ環境に同梱されていた Apache-2.0、LGPLv3、GPLv3 の原文も置いています。LGPLv3 は GPLv3 の条件を取り込むため、両方を用意しています。これらは本体コードのライセンスを設定するものではありません。

本アプリはPySide6 / shiboken6とQtCore・QtGui・QtWidgetsをLGPLv3の条件で使用します。[PySide6 / shiboken6 6.9.2の上流ソース](https://code.qt.io/cgit/pyside/pyside-setup.git/tree/?h=v6.9.2)と、[QtCore](https://doc.qt.io/archives/qt-6.9/qtcore-index.html#licenses-and-attributions)・[QtGui](https://doc.qt.io/archives/qt-6.9/qtgui-index.html#licenses-and-attributions)・[QtWidgets](https://doc.qt.io/archives/qt-6.9/qtwidgets-index.html#licenses)の許諾案内を参照できます。ライブラリは改変せず、利用者のPython環境にインストールしたものを動的に読み込みます。

このフォルダーにはライセンス文書を含み、ライブラリ本体・DLL、OCRモデル、Tesseract、Python本体は含みません。これらのバイナリを同梱して再配布する場合、含めた部品のライセンスに基づく通知、対応ソースの提供、差し替え・再リンク等の条件を満たす必要があります。[Qtの公式案内](https://www.qt.io/development/open-source-lgpl-obligations)にLGPLv3の条件が説明されています。

本体のMITライセンスと第三者の条件の区別は[権利表示](../RIGHTS_AND_ATTRIBUTION.md)にまとめています。M2M100とCTranslate2のMITライセンスは、翻訳画面への常時クレジット表示を要求していません。
