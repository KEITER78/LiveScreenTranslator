# LiveScreenTranslator

[KEITER78](https://github.com/KEITER78) が開発する、画面の文章をローカルで翻訳するWindowsアプリです。

Copyright (c) 2026 KEITER78 — MIT License

## ダウンロード・起動

通常の利用には、[ReleasesのWindows x64版](https://github.com/KEITER78/LiveScreenTranslator/releases/latest)から `LiveScreenTranslator-windows-x64.zip` をダウンロードしてください。GitHubの「Code → Download ZIP」は開発用ソースです。

1. ZIPをすべて展開します。
2. 展開したフォルダー内の **`LiveScreenTranslator.exe`** を開きます。`_internal` フォルダーも一緒に置いてください。
3. 初回のみ、[同梱部品の利用条件](BINARY_TERMS.md)を確認して使用を開始します。本体のMIT許諾と、第三者部品に固有の条件を区別して表示します。
4. 初回セットアップで、使用するOCRを選び「セットアップを開始」を押します。標準のEasyOCRには別のOCRアプリのインストールは不要です。
5. 準備が終わったらセットアップ画面を閉じ、翻訳元・翻訳先を選択します。
6. 「翻訳範囲を選択」→「自動翻訳を開始」の順に操作します。原文欄への貼り付け翻訳もできます。

配布版にはPythonと必要なライブラリを同梱しています。**Pythonのインストール、コマンド操作、GPU、APIキーは不要**です。対応OSはWindows 10 / 11の64ビット版（x64）です。

初回の翻訳モデル取得量は約1.95GBで、CPU用形式への変換も行います。OCRモデルは言語に応じて追加取得します。初回にはインターネット接続と数GBの空き容量が必要です。モデル変換は通常の翻訳よりメモリを使うため、RAM 8GB以上を目安にしてください。

準備したモデルは次回以降も利用します。通常の起動では初回案内を表示せず、追加の言語準備や再設定は画面下部の「セットアップ…」から行えます。

## 機能と対応範囲

- 翻訳元・翻訳先をM2M100の100言語から選択し、入れ替え・設定保存ができます。
- 指定した画面範囲を定期的に認識し、翻訳結果を表示します。オーバーレイ表示とフォント変更にも対応します。
- 翻訳はM2M100 418M / CTranslate2 INT8で、OCRはEasyOCRまたはTesseractでローカル処理します。配布版のCTranslate2はCUDA/cuDNNを使わないCPU専用ビルドです。
- Tesseractの言語データは83の翻訳元言語に対応付けています。翻訳モデルと各OCRの対応範囲は異なります。[対応言語](SUPPORTED_LANGUAGES.md)を参照してください。
- モデル・OCR言語データの取得時に通信します。翻訳する画面画像・文章を外部へ送信しません。

Tesseractを選ぶ場合のみ、[公式の導入案内](https://tesseract-ocr.github.io/tessdoc/Installation.html)に従ってTesseract 4以降を別途インストールしてください。PATH上、または `C:\Program Files\Tesseract-OCR\tesseract.exe` を探します。初めて使う場合はEasyOCRを選択できます。

翻訳速度は文章量・言語・CPUにより変わります。ゲーム用語などで誤訳や不自然な訳が生じる場合があります。100言語すべての翻訳方向について品質を保証するものではありません。

## 設定・モデルの保存先

言語、表示、フォント、取得範囲などの設定は、Windowsレジストリ `HKEY_CURRENT_USER\Software\KEITER78\LiveScreenTranslator` に保存します。画面画像・原文・翻訳結果の履歴は保存しません。

モデルと言語データは **`%LOCALAPPDATA%\LiveScreenTranslator\models\`** に保存します。実行ファイルのフォルダーには書き込まず、取得データを配布用ZIPに含めません。ZIPを展開し直しても、このユーザー用キャッシュは再利用します。動画用に初回状態を確認する場合は、別のWindowsユーザーか、検証専用の保存先を使ってください。

検証用の環境変数 `LST_DATA_DIR` を指定すると、そのフォルダー内にモデルとINI形式の設定を保存し、通常のレジストリ設定から分離します。通常の起動では上記のユーザー用保存先を使います。

ソース版ですでに準備した `models/m2m100-int8/` がある場合、そのソース版では従来のモデルを引き続き利用できます。配布用exeにはコピーされません。

## ソースからの実行・ビルド

自作ソースとビルド手順もこのリポジトリで公開しています。ソースから実行する場合は64ビットのPython環境と依存パッケージが必要です。配布版のビルド環境はCPython 3.12.16、依存の固定版は `requirements-lock.txt`、ビルド用は `requirements-build.txt` です。

開発用の専用環境に依存を導入し、`main.py` を実行します。既存の `.venv` がある場合は `start.bat` でも起動できます。

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe main.py
```

Windows配布版は、Visual Studio C++ x64ビルドツールを備えた別の専用環境でCPU専用CTranslate2を作成し、PyInstallerのフォルダー形式でビルドします。バイナリ同梱部品の通知と対応ソースも同時に生成します。詳しい手順は[バイナリ配布と再ビルド](BINARY_DISTRIBUTION.md)に記載しています。

## ライセンス

自作ソースと本体文書は **MITライセンス** です。[LICENSE](LICENSE)の著作権表示と許諾文を保持する条件で、利用・改変・再配布・商用利用ができます。

第三者ソフトウェアやモデルには各権利者の条件が適用されます。M2M100とCTranslate2はMIT、EasyOCR本体・Tesseract・公式tessdata_fastはApache 2.0です。GUIのPySide6 / QtにはLGPLv3を適用し、必要な通知・ライセンス文書と対応ソースの入手先を配布ZIP内に記載します。

[権利表示](RIGHTS_AND_ATTRIBUTION.md)、[第三者通知](THIRD_PARTY_NOTICES.md)、[バイナリ配布の説明](BINARY_DISTRIBUTION.md)、[原文](third_party_licenses/)を参照してください。ReleasesにはアプリZIPと同じ版の対応ソースZIP・チェックサムも掲載します。
