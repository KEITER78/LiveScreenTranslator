# LiveScreenTranslator

[KEITER78](https://github.com/KEITER78) が開発する、画面の文章をローカルで翻訳する Windows アプリです。

Copyright (c) 2026 KEITER78

## 機能

- **翻訳元・翻訳先を100言語から選択**し、入れ替え・設定保存ができます。英語、日本語、中国語、韓国語、フランス語、ドイツ語、スペイン語、ポルトガル語、ロシア語、アラビア語、ヒンディー語などに対応します。
- 翻訳専用の **M2M100 418M / CTranslate2 INT8** をCPUで実行します。GPU・VRAM・APIキー・Ollamaは不要です。
- 画面の指定範囲を定期取得し、認識結果と翻訳を表示します。オーバーレイ表示と原文の貼り付け翻訳もあります。
- TesseractのOCRデータは83の翻訳元言語に対応付けています。翻訳モデルとOCRの対応範囲は異なります。全一覧は [対応言語](SUPPORTED_LANGUAGES.md) を参照してください。
- モデル・OCR言語データの取得時に通信します。翻訳中の画面画像・文章を外部へ送信せず、準備した言語はローカルで処理します。

## 起動

セットアップ後、**`start.bat` をダブルクリック**してください。

「翻訳元」「翻訳先」を選び、「翻訳範囲を選択」→「自動翻訳を開始」の順に操作します。認識に必要な言語データがない場合、初回だけ公式配布元から取得します。原文欄に文章を貼り付けて翻訳する場合はOCRを使いません。

## セットアップ

WindowsでPython 3.10（64ビット）とPythonランチャー `py` をインストールしてください。このリポジトリを取得・展開し、フォルダー内でPowerShellを開いて次を実行します。専用環境 `.venv` に依存パッケージをインストールします。

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -X utf8 prepare_translation.py
```

Python 3.10.6で動作確認しています。`start.bat` は `.venv` のPythonを直接呼びます。元のPython本体を削除した場合は専用環境を作り直してください。

モデル準備には初回約1.95GBの公式チェックポイント取得と、INT8への変換が必要です。画面の「翻訳モデルを準備」でも実行できます。取得元の版と大きいファイルのSHA-256を固定・確認し、`models/m2m100-int8/ready.json` に変換履歴を記録します。変換後の重みは約491MB。初回変換には実行時より多くのメモリとディスクを使うため、RAM 8GB以上・十分な空き容量での準備を勧めます。動作時はGPUを使いません。

Tesseractで画面OCRを行う場合は、[公式のインストール案内](https://tesseract-ocr.github.io/tessdoc/Installation.html)に従ってTesseract 4以降をインストールしてください。PATH、または `C:\Program Files\Tesseract-OCR\tesseract.exe` を探します。EasyOCRを選択する場合はTesseractのインストールは不要です。EasyOCRもCPUで動作し、使用する言語の認識モデルを初回に取得します。

翻訳速度は言語、文章量、CPUにより変わります。ゲーム固有の用語等では誤訳・不自然な訳が生じる場合があります。

## 設定の保存先

言語、表示、フォント、取得範囲などの設定は、プロジェクトの外にあるWindowsレジストリ `HKEY_CURRENT_USER\Software\KEITER78\LiveScreenTranslator` に保存します。画面画像、原文、翻訳結果は保存しません。設定を戻す場合は、画面の「設定を初期化」を使用してください。

翻訳モデルとTesseractの言語データはプロジェクト内の `models/` に、EasyOCRのモデルは通常ユーザーフォルダー内の `.EasyOCR/` に保存されます。これらの取得データはGitHubのソース配布には含みません。

## ライセンスと配布物

本体の自作ソースと本体文書は **MITライセンス** で公開します。著作権表示は `Copyright (c) 2026 KEITER78`、許諾文は [LICENSE](LICENSE) に記載しています。著作権表示と許諾文を保持する条件で、利用・改変・再配布・商用利用ができます。

第三者ソフトウェアとモデルにはそれぞれのライセンスが適用されます。M2M100とCTranslate2はMIT、Tesseract・公式tessdata_fast・EasyOCR本体はApache 2.0です。GUIにはPySide6 / QtのQtCore・QtGui・QtWidgetsをLGPLv3の条件で使用します。本体のMITライセンスは、これら第三者の条件を変更しません。

[必要な権利表示](RIGHTS_AND_ATTRIBUTION.md)、[第三者通知](THIRD_PARTY_NOTICES.md)、[元の許諾文](third_party_licenses/) を参照してください。

このリポジトリの配布形式はPythonソースと文書です。Python環境、ライブラリ本体・DLL、翻訳・OCRモデル、フォント、個人設定、ログ、実行ファイルは同梱しません。依存パッケージはセットアップ時に、モデル・言語データは準備時に取得します。モデルやライブラリを同梱して再配布する場合は、その部品のライセンスに従う必要があります。
