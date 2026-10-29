# 第三者ソフトウェア通知

確認日: 2026-10-29。対象はローカルM2M100版とWindows x64配布版です。本体の作者はKEITER78で、第三者の権利は各権利者に帰属します。

## 翻訳モデル・OCR

| 対象 | 許諾と表示 |
| --- | --- |
| M2M100 418M | Facebook, Inc. and its affiliates / MIT。[公式モデルカード](https://huggingface.co/facebook/m2m100_418M) と [元の許諾文](third_party_licenses/m2m100/LICENSE)。INT8 へ変換したモデルには取得元・版・改変内容を ready.json に記録。重みは GitHub のソースには含めない |
| CTranslate2 4.6.0 | OpenNMT / MIT。[元の許諾文](third_party_licenses/ctranslate2/LICENSE)。Windows配布版は `4.6.0+cpu` としてCUDA/cuDNNを無効化し、Intel oneMKLの逐次実行版を静的リンク。上流ソースと変更・ビルド手順を公開し、Intel部品の許諾文も配布ZIPに保持する |
| Tesseract / tessdata_fast | Apache-2.0。[本体](https://github.com/tesseract-ocr/tesseract/blob/main/LICENSE) / [公式言語データ](https://github.com/tesseract-ocr/tessdata_fast/blob/4.1.0/LICENSE)。必要な言語データだけ公式 4.1.0 から取得。本体の実行ファイルは外部インストールを利用 |
| EasyOCR 1.7.2 | Apache-2.0。[元の許諾文](third_party_licenses/easyocr/LICENSE)。選択時だけ初期化。認識モデルは利用者の環境で初回取得し、ソース配布には同梱しない |
| PySide6 / Qt / shiboken6 | 本アプリではQtCore・QtGui・QtWidgetsをLGPLv3の条件で利用。[LGPLv3原文](third_party_licenses/common/LGPL-3.0.txt) / [参照するGPLv3原文](third_party_licenses/common/GPL-3.0.txt) / [Qtの案内](https://www.qt.io/development/open-source-lgpl-obligations) / [上流ソースと補足](third_party_licenses/README.md) |

## 固定版パッケージ

モデル準備に使用するTransformersを含む、依存パッケージの固定版と許諾文を以下に示します。

44 パッケージ（pip / setuptools を除く）。原文ファイルの一覧は [dependency-licenses.json](dependency-licenses.json) にあります。

| パッケージ | バージョン | ライセンス概要 | 原文 |
| --- | --- | --- | --- |
| [certifi](https://pypi.org/project/certifi/2026.10.18/) | 2026.10.18 | MPL-2.0 | [原文](third_party_licenses/certifi/licenses/) |
| [charset-normalizer](https://pypi.org/project/charset-normalizer/3.5.2/) | 3.5.2 | MIT | [原文](third_party_licenses/charset-normalizer/licenses/) |
| [colorama](https://pypi.org/project/colorama/0.4.6/) | 0.4.6 | BSD-3-Clause | [原文](third_party_licenses/colorama/licenses/) |
| [ctranslate2](https://pypi.org/project/ctranslate2/4.6.0/) | 4.6.0 | MIT; bundled native dependencies have additional terms | [原文](third_party_licenses/ctranslate2/) |
| [easyocr](https://pypi.org/project/easyocr/1.7.2/) | 1.7.2 | Apache-2.0 | [原文](third_party_licenses/easyocr/) |
| [filelock](https://pypi.org/project/filelock/4.1.0/) | 4.1.0 | MIT | [原文](third_party_licenses/filelock/licenses/) |
| [fsspec](https://pypi.org/project/fsspec/2026.9.0/) | 2026.9.0 | BSD-3-Clause | [原文](third_party_licenses/fsspec/licenses/) |
| [huggingface_hub](https://pypi.org/project/huggingface_hub/0.36.2/) | 0.36.2 | Apache-2.0 | [原文](third_party_licenses/huggingface-hub/licenses/) |
| [idna](https://pypi.org/project/idna/2.10/) | 2.10 | BSD-3-Clause | [原文](third_party_licenses/idna/) |
| [ImageIO](https://pypi.org/project/ImageIO/2.38.0/) | 2.38.0 | BSD-2-Clause | [原文](third_party_licenses/imageio/licenses/) |
| [Jinja2](https://pypi.org/project/Jinja2/3.1.6/) | 3.1.6 | BSD-3-Clause | [原文](third_party_licenses/jinja2/licenses/) |
| [lazy-loader](https://pypi.org/project/lazy-loader/0.6/) | 0.6 | BSD-3-Clause | [原文](third_party_licenses/lazy-loader/licenses/) |
| [MarkupSafe](https://pypi.org/project/MarkupSafe/3.0.4/) | 3.0.4 | BSD-3-Clause | [原文](third_party_licenses/markupsafe/licenses/) |
| [mpmath](https://pypi.org/project/mpmath/1.3.0/) | 1.3.0 | BSD-3-Clause | [原文](third_party_licenses/mpmath/) |
| [networkx](https://pypi.org/project/networkx/3.4.2/) | 3.4.2 | BSD-3-Clause | [原文](third_party_licenses/networkx/) |
| [ninja](https://pypi.org/project/ninja/1.13.2/) | 1.13.2 | Apache-2.0 | [原文](third_party_licenses/ninja/licenses/) |
| [numpy](https://pypi.org/project/numpy/1.26.4/) | 1.26.4 | BSD-3-Clause; bundled libraries have additional terms | [原文](third_party_licenses/numpy/) |
| [opencv-python-headless](https://pypi.org/project/opencv-python-headless/4.11.0.86/) | 4.11.0.86 | MIT wrapper; Apache-2.0 OpenCV; bundled libraries have additional terms | [原文](third_party_licenses/opencv-python-headless/) |
| [packaging](https://pypi.org/project/packaging/26.3/) | 26.3 | Apache-2.0 OR BSD-2-Clause | [原文](third_party_licenses/packaging/licenses/) |
| [pillow](https://pypi.org/project/pillow/10.4.0/) | 10.4.0 | HPND; bundled libraries have additional terms | [原文](third_party_licenses/pillow/) |
| [pyclipper](https://pypi.org/project/pyclipper/1.4.0/) | 1.4.0 | MIT | [原文](third_party_licenses/pyclipper/licenses/) |
| [PySide6](https://pypi.org/project/PySide6/6.9.2/) | 6.9.2 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | [Qtの条件](third_party_licenses/README.md) |
| [PySide6_Addons](https://pypi.org/project/PySide6_Addons/6.9.2/) | 6.9.2 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | [Qtの条件](third_party_licenses/README.md) |
| [PySide6_Essentials](https://pypi.org/project/PySide6_Essentials/6.9.2/) | 6.9.2 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | [Qtの条件](third_party_licenses/README.md) |
| [pytesseract](https://pypi.org/project/pytesseract/0.3.13/) | 0.3.13 | Apache-2.0 | [原文](third_party_licenses/pytesseract/) |
| [python-bidi](https://pypi.org/project/python-bidi/0.6.11/) | 0.6.11 | LGPL-3.0-or-later; third-party terms | [原文](third_party_licenses/python-bidi/licenses/) |
| [PyYAML](https://pypi.org/project/PyYAML/6.0.3/) | 6.0.3 | MIT | [原文](third_party_licenses/pyyaml/licenses/) |
| [regex](https://pypi.org/project/regex/2026.9.29/) | 2026.9.29 | Apache-2.0 AND CNRI-Python | [原文](third_party_licenses/regex/licenses/) |
| [requests](https://pypi.org/project/requests/2.34.2/) | 2.34.2 | Apache-2.0 | [原文](third_party_licenses/requests/licenses/) |
| [safetensors](https://pypi.org/project/safetensors/0.8.0/) | 0.8.0 | Apache-2.0 | [原文](third_party_licenses/safetensors/licenses/) |
| [scikit-image](https://pypi.org/project/scikit-image/0.25.2/) | 0.25.2 | BSD-3-Clause; per-file terms in LICENSE.txt | [原文](third_party_licenses/scikit-image/) |
| [scipy](https://pypi.org/project/scipy/1.15.3/) | 1.15.3 | BSD-3-Clause; bundled libraries have additional terms | [原文](third_party_licenses/scipy/) |
| [sentencepiece](https://pypi.org/project/sentencepiece/0.2.0/) | 0.2.0 | Apache-2.0 | [原文](third_party_licenses/sentencepiece/) |
| [shapely](https://pypi.org/project/shapely/2.1.2/) | 2.1.2 | BSD-3-Clause; bundled GEOS LGPL-2.1 | [原文](third_party_licenses/shapely/licenses/) |
| [shiboken6](https://pypi.org/project/shiboken6/6.9.2/) | 6.9.2 | LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only | [Qtの条件](third_party_licenses/README.md) |
| [sympy](https://pypi.org/project/sympy/1.14.0/) | 1.14.0 | BSD-3-Clause; third-party terms | [原文](third_party_licenses/sympy/licenses/) |
| [tifffile](https://pypi.org/project/tifffile/2025.5.10/) | 2025.5.10 | BSD-3-Clause | [原文](third_party_licenses/tifffile/licenses/) |
| [tokenizers](https://pypi.org/project/tokenizers/0.19.1/) | 0.19.1 | Apache-2.0 | [原文](third_party_licenses/tokenizers/) |
| [torch](https://pypi.org/project/torch/2.8.0/) | 2.8.0+cpu | BSD-3-Clause; LICENSE and NOTICE include third-party terms | [原文](third_party_licenses/torch/) |
| [torchvision](https://pypi.org/project/torchvision/0.23.0/) | 0.23.0+cpu | BSD-3-Clause | [原文](third_party_licenses/torchvision/) |
| [tqdm](https://pypi.org/project/tqdm/4.70.1/) | 4.70.1 | MPL-2.0 AND MIT | [原文](third_party_licenses/tqdm/licenses/) |
| [transformers](https://pypi.org/project/transformers/4.44.2/) | 4.44.2 | Apache-2.0 | [原文](third_party_licenses/transformers/) |
| [typing_extensions](https://pypi.org/project/typing_extensions/4.16.0/) | 4.16.0 | PSF-2.0 | [原文](third_party_licenses/typing-extensions/licenses/) |
| [urllib3](https://pypi.org/project/urllib3/2.8.0/) | 2.8.0 | MIT | [原文](third_party_licenses/urllib3/licenses/) |

概要は各原文の代替ではありません。配布版にはCPython 3.12.16、PyInstallerブートローダー、Qt、GEOS、数値計算・画像処理ライブラリ、Microsoft VC++ランタイム等も含みます。各部品の原文とファイル一覧は配布ZIPの `licenses/` と `BINARY_COMPONENTS.json` に、対応ソースの入手先と差し替え方法は `SOURCE_OFFER.md` と[バイナリ配布の説明](BINARY_DISTRIBUTION.md)に記載します。字体はOSのフォントを参照し、フォントファイルは同梱しません。
