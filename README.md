# LiveScreenTranslator

[KEITER78](https://github.com/KEITER78) が開発する、画面の文章をローカルで翻訳する Windows アプリです。

Copyright (c) 2026 KEITER78

## 機能

- **翻訳元・翻訳先を100言語から選択**し、入れ替え・設定保存ができます。英語、日本語、中国語、韓国語、フランス語、ドイツ語、スペイン語、ポルトガル語、ロシア語、アラビア語、ヒンディー語などに対応します。
- 翻訳専用の **M2M100 418M / CTranslate2 INT8** をCPUで実行します。GPU・VRAM・APIキー・Ollamaは不要です。
- 画面の指定範囲を定期取得し、認識結果と翻訳を表示します。オーバーレイ表示と原文の貼り付け翻訳もあります。
- TesseractのOCRデータは83の翻訳元言語に対応付けています。翻訳モデルとOCRの対応範囲は異なります。全一覧は [対応言語](SUPPORTED_LANGUAGES.md) を参照してください。
- 初回のモデル取得後、翻訳中の画面画像・文章を外部へ送信しません。

## 起動

セットアップ後、**`start.bat` をダブルクリック**してください。

「翻訳元」「翻訳先」を選び、「翻訳範囲を選択」→「自動翻訳を開始」の順に操作します。認識に必要な言語データがない場合、初回だけ公式配布元から取得します。原文欄に文章を貼り付けて翻訳する場合はOCRを使いません。

## セットアップ

WindowsでPython 3.10（64ビット）をインストールし、このプロジェクトのフォルダーで次を実行してください。専用環境 `.venv` に依存パッケージをインストールします。

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
.\.venv\Scripts\python.exe -X utf8 prepare_translation.py
```

Python 3.10.6で動作確認しています。`start.bat` は `.venv` のPythonを直接呼びます。元のPython本体を削除した場合は専用環境を作り直してください。

モデル準備には初回約1.95GBの公式チェックポイント取得と、INT8への変換が必要です。画面の「翻訳モデルを準備」でも実行できます。取得元の版と大きいファイルのSHA-256を固定・確認し、`models/m2m100-int8/ready.json` に変換履歴を記録します。変換後の重みは約491MB。初回変換には実行時より多くのメモリとディスクを使うため、RAM 8GB以上・十分な空き容量での準備を勧めます。動作時はGPUを使いません。

Tesseractで画面OCRを行う場合は、Tesseract 4以降のインストールが必要です。PATH、または `C:\Program Files\Tesseract-OCR\tesseract.exe` を探します。別途EasyOCRも選択可能で、選択した翻訳元言語に合わせてCPUで初期化します。言語の対応状況は各OCRに依存します。

翻訳速度は言語、文章量、CPUにより変わります。ゲーム固有の用語等では誤訳・不自然な訳が生じる場合があります。

## 設定の保存先

言語、表示、フォント、取得範囲などの設定は、プロジェクトの外にあるWindowsレジストリ `HKEY_CURRENT_USER\Software\KEITER78\LiveScreenTranslator` に保存します。画面画像、原文、翻訳結果は保存しません。設定を戻す場合は、画面の「設定を初期化」を使用してください。

## 公開と権利表示

M2M100はMIT、CTranslate2はMIT、Tesseractと公式tessdata_fastはApache 2.0です。**本体コードの公開ライセンスは未指定です。** 第三者ソフトウェアの条件は、それぞれの権利者が定めています。実行ファイルにQt等をまとめる場合は、ソース公開とは別に配布物の条件を確認してください。

[必要な権利表示](RIGHTS_AND_ATTRIBUTION.md)、[第三者通知](THIRD_PARTY_NOTICES.md)、[元の許諾文](third_party_licenses/) を参照してください。

GitHubへはソースと文書を含め、`.venv`、`models`、`.publish-audit`、`backup`、ログ、個人設定、フォント、実行ファイルを含めない構成です。`.gitignore`は手動アップロードには適用されません。モデルを別途配布する場合は取得元・ライセンス・変換表示も保持してください。
