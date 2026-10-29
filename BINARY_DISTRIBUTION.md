# Windows実行ファイル版の配布とライセンス

本体の自作ソース・本体文書は `Copyright (c) 2026 KEITER78`、MITライセンスです。
実行ファイルに含まれるPython、Qt、OCR・数値計算ライブラリ等には各権利者のライセンスが適用されます。
MITという表示が、同梱ライブラリ全体をMITへ変更することはありません。

## 配布物

Windows x64版は `LiveScreenTranslator-windows-x64.zip` として提供します。
ZIPを展開し、`LiveScreenTranslator.exe` を起動してください。
`_internal/` のDLLやPythonモジュールは実行に必要です。exeだけを取り出して配布しないでください。
翻訳・OCRの学習済みモデルは含めず、初回セットアップで取得します。

`LiveScreenTranslator-corresponding-sources.zip` を同じGitHub Releaseに添付します。
このZIPには対応するLGPL/MPLライブラリの完全なソース、本体ソース、ビルドスクリプト、
ライブラリの変更・差し替え手順、取得元とSHA-256を含めます。
各バイナリに対応する正確なダウンロード先とハッシュは同梱の `SOURCE_OFFER.md` に記載します。

## 権利表示

- `LICENSE`: 本体のMIT許諾文。
- `licenses/`: 実際のビルド環境から収集した第三者の著作権・許諾文。
- `BINARY_COMPONENTS.json`: 同梱した実行ファイル・DLL・pydの一覧とSHA-256、依存の版、対応ソース情報。
- `SOURCE_OFFER.md`: 対応ソースの取得先と、ライブラリを変更・差し替える権利の案内。
- `BINARY_TERMS.md`: Intel / Microsoftのランタイム部分に限って適用される利用条件。

GUIにはPySide6 / Qt / shiboken6をLGPLv3の条件で使用します。
QtのDLL・プラグインは動的に読み込み、利用者が互換ライブラリへ差し替えられる形で配置します。
python-bidiはLGPLv3以降、GEOSとNumPyのOpenBLASに含まれるlibquadmathはLGPLv2.1以降、
certifiはMPL 2.0です。対応ソースと再ビルド手順を提供し、これらの改変や、
改変のデバッグに必要な解析を本体の条件で禁止しません。
CPUバックエンドに含まれるMPL 2.0のEigenも、使用した完全なソースを対応ソースZIPへ含めます。

NumPy・SciPy等のGCCランタイムにはGCC Runtime Library Exceptionが適用される部品もあります。
例外のないlibquadmathは区別して対応ソースを提供します。
PyInstallerブートローダーの原文と、アプリケーション配布のための例外も保持します。

CPU版のCTranslate2はCUDA / cuDNNを無効にしてビルドします。
CPUバックエンドにリンクしたIntel MKLには、原文のIntel Simplified Software Licenseが適用されます。
MKLのバイナリは改変せずに使用し、著作権表示・許諾文を `licenses/` に保持します。
PyTorchに含まれるIntel OpenMP 2025.2.0にはIntel Developer Tools EULAが適用されます。
Intelの当該ランタイムの解析・改変等に関する条件と責任制限は `BINARY_TERMS.md` と
原文に記載します。これは本体のMITやQt等のLGPLに基づく変更・差し替え権を制限しません。
Windows版Pythonに含まれるMicrosoft Distributable Codeの条件も同ファイルで案内します。

OS付属フォントは参照して使用し、フォントファイルを同梱しません。
対応ソースZIPに含まれる各上流ソースにも、それぞれの原文ライセンスが適用されます。

## ソースからの実行・ビルド

ビルドにはWindows x64、Git、Visual StudioのC++ x64ビルドツールとWindows SDKを使用します。
配布版のPythonはAstral python-build-standaloneのCPython 3.12.16（20261026版）です。
ソースを取得したフォルダーで、以下の固定URLとSHA-256を使って専用環境を用意します。

```powershell
New-Item -ItemType Directory -Force .runtime | Out-Null
Invoke-WebRequest 'https://github.com/astral-sh/python-build-standalone/releases/download/20261026/cpython-3.12.16%2B20261026-x86_64-pc-windows-msvc-install_only_stripped.tar.gz' -OutFile .runtime/python.tar.gz
if ((Get-FileHash .runtime/python.tar.gz -Algorithm SHA256).Hash -ne '1F2AB53880FC67EA323398C6388E05AF28ADDC99A8E389209F08A51FDFF4B149') { throw 'Python archive SHA-256 mismatch' }
tar -xzf .runtime/python.tar.gz -C .runtime
.\.runtime\python\python.exe -m venv .build-venv
.\.build-venv\Scripts\python.exe -m pip install -r requirements-lock.txt -r requirements-build.txt
.\.build-venv\Scripts\python.exe build_cpu_backend.py --install
```

ソースからアプリを起動する場合は、次を実行します。

```powershell
.\.build-venv\Scripts\python.exe main.py
```

Windows配布版をビルドする場合は、次を実行します。

```powershell
.\.build-venv\Scripts\python.exe -m unittest discover -s tests -v
.\.build-venv\Scripts\python.exe build_release.py --build-only
.\.build-venv\Scripts\python.exe packaging_licenses.py --bundle dist/LiveScreenTranslator-windows-x64 --python-runtime .runtime/python --release-tag v1.0.0
.\.build-venv\Scripts\python.exe build_release.py --package-only
```

`build_cpu_backend.py` はCTranslate2 v4.6.0の固定リビジョンを取得し、CUDA/cuDNNを無効化します。
Windows上での正常終了のため、逐次実行のoneMKLとコンパイラーのOpenMPを組み合わせるCMake変更を明示して適用します。
Unicode定数を保つUTF-8コンパイルと、ビルドマシンのパスを埋め込まないための処理も行います。
使用するMicrosoft VC++ランタイム一式は、ビルドに使用したVisual Studioの再配布用ファイルから収集します。
`BUILD_INFO.json` とCPUバックエンド内の `CPU_BUILD.json` に、ソース版・ビルド設定・ファイルハッシュを記録します。

`packaging_licenses.py` はビルド済みフォルダーを対象に、対応ソースのSHA-256照合、
必要な通知の収集、Qtの使用モジュール、NVIDIA / FFmpegランタイムの混入、
フォントの混入を検査します。対応ソースZIP・通知文書・部品一覧がそろってから
配布用ZIPを作成します。
