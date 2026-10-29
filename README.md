# LiveScreenTranslator

画面の指定範囲に表示された文章を認識し、翻訳結果を表示するWindowsアプリです。100言語の翻訳、オーバーレイ表示、文章の貼り付け翻訳に対応しています。

## ダウンロード

[**Windows版をダウンロード**](https://github.com/KEITER78/LiveScreenTranslator/releases/latest/download/LiveScreenTranslator-windows-x64.zip)

## はじめ方

1. ダウンロードしたZIPをすべて展開します。
2. フォルダー内の `LiveScreenTranslator.exe` を開きます。`_internal` フォルダーも同じ場所に置いてください。
3. 初回に表示される利用条件とセットアップを、画面の案内に従って進めます。OCRにはEasyOCRを選択してください。

初回セットアップでは約1.95GBの翻訳モデルと、使用する言語のOCRモデルを取得します。

## 使い方

1. 「翻訳元」と「翻訳先」の言語を選びます。
2. 「翻訳範囲を選択」を押し、読み取りたい範囲をドラッグします。
3. 「自動翻訳を開始」を押すと、範囲内の文章を定期的に認識して翻訳します。「停止」で終了します。

「オーバーレイ表示」を有効にすると、翻訳結果を別ウィンドウで表示できます。表示位置はドラッグで移動し、文字の大きさは「フォント設定」で変更できます。

文章を直接翻訳する場合は、原文欄に貼り付けて「原文欄のテキストを翻訳」を押してください。OCRの追加準備は画面下部の「セットアップ…」から行えます。

## 動作環境

- Windows 10 / 11（64ビット・x64）
- メモリ8GB以上を推奨
- 初回セットアップ時のインターネット接続と数GBの空き容量

## 対応言語・OCR

翻訳元・翻訳先を100言語から選択できます。OCRの対応言語はエンジンによって異なります。[対応言語一覧](SUPPORTED_LANGUAGES.md)を参照してください。

Tesseractを利用する場合は、[公式の導入案内](https://tesseract-ocr.github.io/tessdoc/Installation.html)に従ってインストールしてください。

翻訳速度や精度は、文章・言語・PCの性能によって異なります。固有名詞や専門用語では誤訳が生じる場合があります。

## データの扱い・保存先

画面画像と翻訳する文章はローカルで処理し、外部へ送信しません。画像・原文・翻訳結果の履歴は保存しません。

モデル・言語データは `%LOCALAPPDATA%\LiveScreenTranslator\models\` に、表示や言語などの設定はWindowsレジストリ `HKEY_CURRENT_USER\Software\KEITER78\LiveScreenTranslator` に保存します。

## ライセンス・開発者向け情報

本体のコードと文書は[MITライセンス](LICENSE)です。同梱部品には各権利者のライセンスが適用されます。

- [権利表示と再配布条件](RIGHTS_AND_ATTRIBUTION.md)
- [第三者ソフトウェア通知](THIRD_PARTY_NOTICES.md)
- [ソースからの実行・ビルド手順](BINARY_DISTRIBUTION.md)
- [配布物・対応ソース](https://github.com/KEITER78/LiveScreenTranslator/releases)

Copyright (c) 2026 KEITER78
