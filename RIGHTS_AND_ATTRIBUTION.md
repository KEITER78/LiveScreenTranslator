# 公開時の権利表示

確認日: 2026-10-19。ローカルM2M100版に対応します。

## 本体

作者: [KEITER78](https://github.com/KEITER78)

```text
LiveScreenTranslator
Copyright (c) 2026 KEITER78
```

本体の公開ライセンスは未指定です。第三者ライブラリのライセンスが、本体コードのライセンスを自動で決めるわけではありません。

## README・ヘルプ用の説明例（任意）

次の説明文は任意の案内です。ライセンスがこの文言や画面への常時表示を要求しているわけではありません。配布に必要な著作権表示・許諾文は、別途 `THIRD_PARTY_NOTICES.md` と `third_party_licenses/` に保持します。

```text
LiveScreenTranslator は KEITER78 が開発する独立したアプリです。
翻訳には Meta / Facebook の M2M100 418M を使用します。
本アプリは各提供者の公式アプリではなく、承認・保証を意味しません。
翻訳モデルは CTranslate2 INT8 へ変換して使用します。
M2M100 と CTranslate2 の MIT ライセンス、その他の第三者ソフトウェアの
通知・許諾文を THIRD_PARTY_NOTICES.md と third_party_licenses/ に記載しています。
初回のモデル取得後、翻訳中の文章・画面画像を外部へ送信しません。
```

## 翻訳モデルと推論

M2M100の[公式モデルカード](https://huggingface.co/facebook/m2m100_418M)はモデルをMITと表示し、元のfairseqプロジェクトの[許諾文](third_party_licenses/m2m100/LICENSE)を保持しています。元の著作権表示は `Copyright (c) Facebook, Inc. and its affiliates.` です。モデルを配布する際はMIT全文を添付し、取得元と版、INT8変換の記録も保持します。モデルは既定のGitHubソース配布には含めません。

[CTranslate2](third_party_licenses/ctranslate2/LICENSE)もMITです。再配布時は元の著作権・許諾・免責文を保持します。モデル準備に使うTransformers等の元文書も保存しています。現行依存は[固定版一覧](THIRD_PARTY_NOTICES.md)に記載しています。

### 翻訳画面へのクレジット表示は不要

M2M100のMITライセンスと[CTranslate2 v4.6.0のMITライセンス原文](https://github.com/OpenNMT/CTranslate2/blob/v4.6.0/LICENSE)は、複製物またはソフトウェアの重要な部分に著作権表示と許諾文を含めることを求めています。翻訳結果やオーバーレイにモデル名、クレジット、ロゴを常時表示する条項はありません。元のM2M100の[MITライセンス原文](https://github.com/facebookresearch/fairseq/blob/main/LICENSE)も同じ条件です。

このため、オーバーレイには翻訳結果だけを表示します。配布物には元のライセンス文書を保持します。

## OCRとGUI

Tesseractと[公式tessdata_fast 4.1.0](https://github.com/tesseract-ocr/tessdata_fast/tree/4.1.0)はApache 2.0です。必要な言語データだけ取得し、言語モデルをGitHubソースに含めません。再配布時は原文、該当するNOTICE、改変表示等を保持します。Tesseract実行ファイルは外部のインストールを使用します。

EasyOCR本体はApache 2.0です。学習済み重みの同梱再配布まで全権利を確認した扱いにはせず、現在も重みは公開物から除外しています。

PySide6 / Qt / shiboken6はLGPL等の選択条件に従います。[Qt公式の義務](https://www.qt.io/development/open-source-lgpl-obligations)を確認し、Qtバイナリを配布する場合は、告知だけでなく、適用する対応ソースや差し替え・再リンク等の条件も満たします。MPLの対象部品を配布する場合もソースの入手方法等を示します。

NumPy / SciPy / OpenCV / Pillow / PyTorchなどの同梱部品には別の条件があります。実行ファイルにまとめる場合、Python、DLL、OpenMP、数値計算・画像処理ライブラリ等の実際の構成に対応した通知を用意します。元文書のコピーだけでバイナリ配布の全義務が完了したとは扱いません。

OSのフォントは名前で参照するだけで、フォントファイルは同梱しません。画面の文章を翻訳できることは、第三者の画面や翻訳結果を無条件で転載・再配布できるという意味ではありません。

APIキー、個人設定、`.venv`、モデル、ログ、検証データはGitHubへ含めません。
