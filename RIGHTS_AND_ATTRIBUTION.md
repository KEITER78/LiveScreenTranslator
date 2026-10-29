# 権利表示と再配布条件

対象: LiveScreenTranslator v1.0.1（Windows x64）。更新日: 2026-10-29。

## 本体

作者: [KEITER78](https://github.com/KEITER78)

```text
LiveScreenTranslator
Copyright (c) 2026 KEITER78
```

本体の自作Pythonソースと本体文書には [MITライセンス](LICENSE) を適用します。著作権表示と許諾文を保持する条件で、利用・改変・再配布・商用利用を許諾します。第三者ライブラリ、モデル、第三者の許諾文には、それぞれの権利者が定めるライセンスが適用されます。

第三者の著作権表示・許諾文は、[第三者通知](THIRD_PARTY_NOTICES.md)と[原文フォルダー](third_party_licenses/)に掲載しています。本アプリは各提供者の公式製品ではなく、承認・保証を示すものではありません。

## 翻訳モデルと推論

M2M100の[公式モデルカード](https://huggingface.co/facebook/m2m100_418M)はモデルをMITと表示し、元のfairseqプロジェクトの[許諾文](third_party_licenses/m2m100/LICENSE)を保持しています。元の著作権表示は `Copyright (c) Facebook, Inc. and its affiliates.` です。モデルを配布する際はMIT全文を添付し、取得元と版、INT8変換の記録も保持します。モデルは既定のGitHubソース配布には含めません。

[CTranslate2](third_party_licenses/ctranslate2/LICENSE)もMITです。再配布時は元の著作権・許諾・免責文を保持します。モデル準備に使うTransformers等の元文書も保存しています。依存パッケージは[固定版一覧](THIRD_PARTY_NOTICES.md)に記載しています。

## OCRとGUI

Tesseractと[公式tessdata_fast 4.1.0](https://github.com/tesseract-ocr/tessdata_fast/tree/4.1.0)はApache 2.0です。必要な言語データだけ取得し、言語モデルをGitHubソースに含めません。再配布時は原文、該当するNOTICE、改変表示等を保持します。Tesseract実行ファイルは外部のインストールを使用します。

EasyOCR本体はApache 2.0です。学習済み重みは利用者の環境で初回に取得し、このリポジトリのソース配布には含めません。

GUIにはPySide6 / shiboken6と、QtCore・QtGui・QtWidgetsをLGPLv3の条件で使用します。本体はこれらのライブラリを動的に読み込み、ライブラリ自体は改変しません。元の許諾文は[LGPLv3](third_party_licenses/common/LGPL-3.0.txt)と、同ライセンスが参照する[GPLv3](third_party_licenses/common/GPL-3.0.txt)です。選択可能な許諾と上流ソースは[Qtの説明](third_party_licenses/README.md)に記載しています。

## 配布するファイルと再配布時の条件

このリポジトリには本体ソース、本体文書、依存パッケージ一覧、ビルド手順、第三者ライセンス文書を含めます。ReleasesのWindows x64版ZIPにはPythonと使用するライブラリ本体・DLLを同梱します。翻訳・OCRモデル、OSフォント、個人設定、画面画像・翻訳履歴は同梱しません。

ライブラリやモデルを同梱して再配布する場合は、実際に含めた部品の許諾条件に従います。Qt等のLGPL対象バイナリでは、著作権・ライセンスの告知に加え、対応ソースの提供、ライブラリの差し替え・再リンク等の条件があります。[Qt公式の義務](https://www.qt.io/development/open-source-lgpl-obligations)に詳細があります。MPL対象部品では対象ソースの入手方法を示します。NumPy / SciPy / OpenCV / Pillow / PyTorch等が内包する部品にも各原文の条件が適用されます。

配布版では、同梱した部品のライセンスを `licenses/` に保持し、実際のファイル一覧とSHA-256を `BINARY_COMPONENTS.json` に記録します。LGPL / MPL対象部品の対応ソースと再ビルド手順を、同じReleaseの `LiveScreenTranslator-corresponding-sources.zip` で提供します。取得先とそのSHA-256は配布ZIPの `SOURCE_OFFER.md` に記載します。Qt等のDLLはフォルダー形式で保持し、利用者による差し替えを妨げる仕組みを設けません。

OSのフォントは名前で参照するだけで、フォントファイルは同梱しません。画面の文章を翻訳できることは、第三者の画面や翻訳結果を無条件で転載・再配布できるという意味ではありません。
