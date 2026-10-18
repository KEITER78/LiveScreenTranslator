# 第三者ライセンス・通知の原文

2026-10-19時点のローカル版の専用環境から、44パッケージの元の通知類59文書をコピーしました。モデルと推論の上流許諾文も保持しています。複製先は `dependency-licenses.json`、依存パッケージは `requirements-lock.txt` と `THIRD_PARTY_NOTICES.md` に記載しています。

`common/` には同じ環境に同梱されていた Apache-2.0、LGPLv3、GPLv3 の原文も置いています。LGPLv3 は GPLv3 の条件を取り込むため、両方を用意しています。これらは本体コードのライセンスを設定するものではありません。

PySide6 / shiboken6 の当該 wheel のメタデータでは LGPL / GPL / 商用等の選択肢が示され、型定義の元ファイルにも SPDX 表記があります。一方、dist-info のライセンス用ファイルは商用契約への参照でした。商用契約ファイルをオープンソースの許諾と誤認しないよう、ここには複製していません。適用する LGPL 条件と [Qt の公式案内](https://www.qt.io/development/open-source-lgpl-obligations)、[固定版の上流ソース](https://code.qt.io/cgit/pyside/pyside-setup.git/tree/?h=v6.9.2) を確認してください。

このフォルダーは、ライブラリ本体や DLL、OCR モデル、Tesseract、Python 本体を含みません。将来それらを実行ファイルへ同梱する場合、配布物の正確な構成に対応した通知・ソース提供・差し替え等の義務を、この原文コピーだけですべて満たしたとは判断していません。パッケージ内の dist-info 以外の全ファイルや、外部インストール物までを網羅した抽出ではありません。

本体と第三者の条件の区別、および README / ヘルプ用の任意の説明例は [RIGHTS_AND_ATTRIBUTION.md](../RIGHTS_AND_ATTRIBUTION.md) にまとめています。M2M100とCTranslate2のMITライセンスは、翻訳画面への常時クレジット表示を要求していません。
