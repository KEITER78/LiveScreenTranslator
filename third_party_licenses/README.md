# 第三者ライセンス・通知の原文

使用するソフトウェアの著作権表示とライセンス原文を掲載しています。パッケージ別の索引は[原文一覧](../dependency-licenses.json)と[第三者通知](../THIRD_PARTY_NOTICES.md)、依存パッケージの版は[固定版一覧](../requirements-lock.txt)を参照してください。

`common/` にはApache 2.0、LGPLv3、GPLv3の原文があります。LGPLv3はGPLv3の条件を取り込むため、両方を掲載しています。各部品に適用されるライセンスは[第三者通知](../THIRD_PARTY_NOTICES.md)を参照してください。

本アプリはPySide6 / shiboken6とQtCore・QtGui・QtWidgetsをLGPLv3の条件で使用します。[PySide6 / shiboken6 6.9.2の上流ソース](https://code.qt.io/cgit/pyside/pyside-setup.git/tree/?h=v6.9.2)と、[QtCore](https://doc.qt.io/archives/qt-6.9/qtcore-index.html#licenses-and-attributions)・[QtGui](https://doc.qt.io/archives/qt-6.9/qtgui-index.html#licenses-and-attributions)・[QtWidgets](https://doc.qt.io/archives/qt-6.9/qtwidgets-index.html#licenses)の許諾案内を参照できます。Windows配布版では、これらを改変せずに同梱し、動的に読み込みます。対応ソースの入手先と差し替え手順は、配布ZIP内の `SOURCE_OFFER.md` に記載しています。

バイナリを再配布する場合は、各部品のライセンスに基づく通知、対応ソースの提供、差し替え・再リンク等の条件を満たす必要があります。[Qtの公式案内](https://www.qt.io/development/open-source-lgpl-obligations)にLGPLv3の条件が説明されています。

本体と第三者ソフトウェアの利用・再配布条件は[権利表示](../RIGHTS_AND_ATTRIBUTION.md)に記載しています。
