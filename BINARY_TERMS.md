# Windowsバイナリに含まれるランタイムの利用条件

本体の自作ソース・文書はMITです。同梱の第三者ランタイムは各原文の条件で提供します。
このファイルのランタイム固有条件は、本体コードやLGPL対象ライブラリ全体へ適用するものではありません。

## Intel OpenMP Runtime（PyTorchが使用）

同梱のlibiomp5md.dllはIntel OpenMP 2025.2.0配布物と同一のバイナリです。
このIntel Redistributableの使用には、[Intel OpenMP原文](third_party_licenses/intel-openmp-2025.2.0/LICENSE.txt)の
Intel End User License Agreement for Developer Tools（August 2024）が適用されます。
このIntel Redistributableに限り、リバースエンジニアリング、逆コンパイル、逆アセンブルを禁止します。
原文第7条の保証・責任制限も、このIntel Redistributableについて適用されます。
Intelおよびそのサプライヤーが本アプリを認証・保証したという表示は行いません。

## Intel Simplified Software License対象の同梱Intelバイナリ

oneMKL・Intel IPP等、Intel Simplified Software Licenseで提供される同梱Intelバイナリ部分には、
同ライセンス（October 2022）が適用されます。使用する版と配布元は同梱の原文表示に記録します。
[CPU翻訳バックエンドのoneMKL原文](third_party_licenses/intel-mkl-2026.1.0/LICENSE.txt)、
[PyTorch内のoneMKL原文](third_party_licenses/intel-mkl-2025.2.0/LICENSE.txt)、
[OpenCVとIntel IPPの原文](third_party_licenses/opencv-python-headless-4.11.0.86/LICENSE-3RD-PARTY.txt)、
[Intel IPP SDK原文（閲覧用テキスト）](third_party_licenses/intel-ipp-2021.12.0/EULA.txt)を保持しています。
閲覧用テキストは書式のみを除いたもので、[未改変の原本RTF](third_party_licenses/intel-ipp-2021.12.0/EULA.rtf)も同梱します。
Intelの当該バイナリ部分の改変、リバースエンジニアリング、逆コンパイル、逆アセンブルを禁止します。
これらの条件は当該Intelバイナリ部分だけに適用し、本体のMIT、OpenCVのApache 2.0対象部分、
独立したLGPL対象ライブラリを変更・解析・差し替えする権利を制限しません。

## Microsoft Distributable Code

本配布物は、Visual Studio 2026の再配布可能なC++ / OpenMPランタイムを使用します。
利用・再配布には、[Microsoftの原文](third_party_licenses/microsoft-vc-runtime/VISUAL_STUDIO_2026_COMMUNITY_TERMS.txt)の
DISTRIBUTABLE CODEに基づく条件と、[再配布対象一覧](third_party_licenses/microsoft-vc-runtime/VISUAL_STUDIO_2026_REDISTRIBUTION.html)が適用されます。
[Windows版Pythonの原文](third_party_licenses/python-build-standalone/LICENSE.python.txt)にも関連するWindows向け条件を保持しています。

Microsoft Distributable Codeに限り、技術的制限の回避、リバースエンジニアリング、
逆コンパイル、逆アセンブル、ソースコードの導出を禁止します。ただし、適用法や当該部分の
第三者オープンソースライセンスが認める範囲は、この制限に優先します。
Microsoftおよびそのサプライヤーの権利表示を削除・改変・隠蔽せず、Microsoftによる
承認・提供を装わず、再配布対象外のプレビュー・デバッグ用部品を配布しないでください。
Microsoft以外のプラットフォームでの配布や、悪意のある・欺瞞的な・違法なプログラムへの
組み込みも行わないでください。再配布する場合は、原文の再配布可能なコードに関する条件を維持してください。

Microsoftは当該コードを現状のまま提供し、原文のDISCLAIMER OF WARRANTYおよび
LIMITATION ON DAMAGESに定める保証の否認・責任制限が、法令で許容される範囲で適用されます。
これらの条件はMicrosoft Distributable Codeだけに適用され、Python自体、本体コードのMIT、
Qt等のLGPLに基づく変更・差し替え・改変のデバッグの権利を制限しません。

各ランタイムの完全な原文がこの説明に優先します。利用者に対する本体独自の保証は設けません。
