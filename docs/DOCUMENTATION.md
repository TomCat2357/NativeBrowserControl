# Native Browser Control - 詳細ドキュメント

## 概要

Native Browser Controlは、Windows UI Automation（pywinauto / pywin32）を使用して、Seleniumを使わずにChrome/Edgeブラウザを直接操作するMCPサーバーです。標準入出力で待ち受け、LLMエージェントなどからツール呼び出しでブラウザを制御できます。

## プロジェクト構造

```
NativeBrowserControl/
├── pyproject.toml                    # パッケージ設定
├── README.md                         # 基本的な使い方
├── browser_table_extraction.md       # テーブル抽出の手順メモ
├── approval_system_file_download_procedure.md  # 承認システムのファイルDL手順
├── docs/
│   └── DOCUMENTATION.md              # 本ドキュメント
├── commands/                         # プラグイン用コマンド定義
├── skills/                           # プラグイン用スキル
├── native_browser_control/           # メインパッケージ
│   ├── __init__.py
│   ├── core/                         # コア機能
│   │   ├── __init__.py
│   │   ├── driver.py                 # ブラウザ自動化ロジック
│   │   └── server.py                 # MCPサーバー本体
│   │
│   ├── utils/                        # ユーティリティ
│   │   ├── __init__.py
│   │   └── output.py                 # 出力/ログ制御
│   │
│   └── workflows/                    # ワークフロー群
│       ├── __init__.py
│       ├── analysis/                 # 分析系
│       │   ├── __init__.py
│       │   └── parse_log.py          # ログ抽出表示
│       │
│       ├── downloads/                # ダウンロード系
│       │   ├── __init__.py
│       │   ├── attachments_basic.py      # 添付ファイルダウンロード（基本）
│       │   └── attachments_conductor.py  # 添付ファイルダウンロード（指揮者）
│       │
│       ├── extraction/               # 抽出系
│       │   ├── __init__.py
│       │   └── kesai_page.py         # 決裁ページ情報抽出
│       │
│       └── investigations/           # 調査系
│           ├── __init__.py
│           ├── checkbox_overview.py      # チェックボックス概要
│           ├── checkbox_properties.py    # チェックボックスプロパティ
│           ├── checkbox_surroundings.py  # チェックボックス周辺調査
│           ├── file_extensions.py        # ファイル拡張子調査
│           ├── file_rows.py              # ファイル行調査
│           ├── keyword_search.py         # キーワード検索
│           ├── table_full.py             # テーブル全体調査
│           ├── table_rows_overview.py    # テーブル行概要
│           └── table_structure.py        # テーブル構造調査
└── tests/                            # テスト/検証ファイル
```

---

## コアモジュール

### `native_browser_control/core/driver.py`

ブラウザ自動化の中心となるモジュール。約2,000行以上のコードで構成。

#### 主要クラス

##### `NativeBrowserDriver`
Chrome/Edgeを操作するメインクラス。

```python
class NativeBrowserDriver:
    """Chrome/Edge共通の基底クラス"""

    def __init__(
        self,
        browser: str = "chrome",      # "chrome" or "edge"
        retries: int = 3,             # 探索リトライ回数
        start_if_not_found: bool = False,  # 見つからない場合に起動するか
        ...
    ):
```

**主要メソッド:**

| メソッド | 説明 |
|---------|------|
| `connect(target_window)` | 指定ウィンドウに接続 |
| `navigate(url)` | 指定URLに移動 |
| `get_address_bar_url()` | アドレスバーからURL取得 |
| `get_page_title()` | ページタイトル取得 |
| `screenshot(file_path, ...)` | スクリーンショット撮影 |
| `capture_full_screen(...)` | 画面全体のスクリーンショット |
| `scan_page_elements(...)` | ページ要素のスキャン |
| `filter_current_elements(...)` | スキャン済み要素のフィルタリング |
| `click_by_index(index)` | インデックスで要素をクリック |
| `set_edit_text(index, text)` | 要素にテキスト設定 |
| `select_all_and_get_text()` | 全選択してテキスト取得 |
| `get_page_source()` | HTMLソース取得 |
| `type_text(text, method)` | テキスト入力 |
| `find_text_on_page(text)` | ページ内検索 |
| `scroll_down/up/to_top/to_bottom()` | スクロール操作 |
| `new_tab/close_tab/next_tab/previous_tab()` | タブ操作 |
| `back/forward/refresh()` | ナビゲーション操作 |
| `zoom_in/out/reset_zoom()` | ズーム操作 |
| `click_at_position(x, y)` | 座標クリック |
| `copy_selected_text()` | 選択テキストコピー |
| `paste_from_clipboard()` | 貼り付け |
| `wait_for_idle(seconds)` | 待機 |
| `get_browser_summary()` | ブラウザ概要取得 |

##### `NativeChromeDriver` / `NativeEdgeDriver`
ブラウザ固有のドライバー（`NativeBrowserDriver`の継承クラス）

#### データクラス

```python
@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int
    # プロパティ: width, height

@dataclass(frozen=True)
class BrowserWindowInfo:
    browser: str
    title: str
    pid: int
    handle: int
    rect: Rect
    is_visible: bool
    is_minimized: bool
    is_foreground: bool

@dataclass(frozen=True)
class ActionResult:
    ok: bool
    code: str
    message: str
    data: Any | None = None
```

#### 例外クラス

```python
class NativeBrowserError(Exception)       # 基底例外
class InvalidInputError(NativeBrowserError)      # 入力エラー
class UnsupportedBrowserError(InvalidInputError) # 非対応ブラウザ
class WindowNotFoundError(NativeBrowserError)    # ウィンドウ未発見
class ElementNotFoundError(NativeBrowserError)   # 要素未発見
class ClipboardError(NativeBrowserError)         # クリップボードエラー
class LaunchError(NativeBrowserError)            # 起動失敗
class ScreenshotError(NativeBrowserError)        # スクリーンショット失敗
class ExternalApiError(NativeBrowserError)       # 外部API エラー
class ActionFailedError(NativeBrowserError)      # アクション失敗
class BrowserTimeoutError(NativeBrowserError, TimeoutError)  # タイムアウト
```

#### ファクトリ関数

```python
def find_browser_windows(browser, ...)  # ブラウザウィンドウを検索
def get_browser_window(browser, ...)    # ブラウザウィンドウを取得
def list_running_browser_drivers(...)   # 起動中ブラウザ一覧
def launch_browser_driver(browser, ...) # ブラウザを起動
def connect_browser_by_index(browser, window_index, ...)  # インデックスで接続
```

---

### `native_browser_control/core/server.py`

MCPサーバー本体。約960行のコード。

#### 提供ツール一覧

| カテゴリ | ツール名 | 説明 |
|---------|---------|------|
| **接続** | `list_browser_windows` | 起動中ブラウザウィンドウ一覧 |
| | `connect_browser` | ブラウザに接続 |
| **ナビゲーション** | `navigate` | URL移動 |
| | `get_url` | URL取得 |
| | `get_title` | タイトル取得 |
| | `get_browser_summary` | ブラウザ概要取得 |
| **スクリーンショット** | `screenshot` | ウィンドウスクリーンショット |
| | `full_screenshot` | 画面全体スクリーンショット |
| **コンテンツ取得** | `get_page_text` | ページテキスト取得 |
| | `get_page_source` | HTMLソース取得 |
| **入力** | `type_text` | テキスト入力 |
| | `find_text` | ページ内検索 |
| **スクロール** | `scroll` | スクロール操作 |
| **タブ操作** | `new_tab` | 新規タブ |
| | `close_tab` | タブを閉じる |
| | `switch_tab` | タブ切り替え |
| **ブラウザ操作** | `back` | 戻る |
| | `forward` | 進む |
| | `refresh` | リロード |
| | `zoom` | ズーム操作 |
| **クリック** | `click` | 座標クリック |
| **要素操作** | `scan_elements` | 要素スキャン |
| | `filter_elements` | 要素フィルタリング |
| | `list_elements` | 要素一覧表示 |
| | `elements_summary` | 要素サマリー表示 |
| | `click_element` | 要素クリック |
| | `set_element_text` | 要素テキスト設定 |
| **その他** | `wait` | 待機 |
| | `copy_selected` | 選択テキストコピー |
| | `paste` | 貼り付け |

#### 提供リソース

| URI | 説明 |
|-----|------|
| `tips://file-dialog-text-input` | ファイルダイアログでの入力方法 |
| `tips://gemini-file-upload` | Geminiでのファイルアップロード手順 |

---

### `native_browser_control/utils/output.py`

ワークフローの出力/ログ制御ユーティリティ。

#### 主要コンポーネント

```python
OutputTarget = Literal["stdout", "stderr", "silent"]

@dataclass
class WorkflowResult:
    exit_code: int
    summary: dict[str, Any]
    log: str = ""

def add_output_argument(parser)     # 出力引数をパーサーに追加
def resolve_output_targets(output, ...)  # 出力先を解決
def route_output(func, target, ...)      # 出力をルーティング
def emit_lines(target, lines)            # 行を出力
def setup_logger(name, level)            # ロガー設定
def add_logging_argument(parser)         # ログ引数をパーサーに追加
```

---

## ワークフロー

### `workflows/downloads/attachments_basic.py`

決裁確認ページから添付ファイルをダウンロードするスクリプト。

**機能:**
1. 決裁情報を抽出
2. 添付ファイル情報を読み込み（kesai_data.json）
3. Edgeブラウザに接続
4. チェックボックス操作で添付ファイルをダウンロード
5. ZIPファイルを展開・削除

**使用方法:**
```bash
python -m native_browser_control.workflows.downloads.attachments_basic --help
```

### `workflows/extraction/kesai_page.py`

決裁確認ページから情報を抽出するスクリプト。

**抽出情報:**
- 基本情報（所属、担当者、役職）
- 文書情報（供覧日、文書年、供覧区分、文書管理番号）
- 内容（件名、供覧文、説明、備考、コメント）
- 添付ファイル情報

**出力:**
- コンソール表示（整形済み）
- JSONファイル（kesai_data.json）

### `workflows/investigations/*`

ブラウザ上のUI要素を調査するためのスクリプト群。

| スクリプト | 目的 |
|-----------|------|
| `checkbox_overview.py` | チェックボックスの概要調査 |
| `checkbox_properties.py` | チェックボックスのプロパティ調査 |
| `checkbox_surroundings.py` | チェックボックス周辺要素の調査 |
| `file_extensions.py` | ファイル拡張子の調査 |
| `file_rows.py` | ファイル行の調査 |
| `keyword_search.py` | キーワード検索 |
| `table_full.py` | テーブル全体の調査 |
| `table_rows_overview.py` | テーブル行の概要 |
| `table_structure.py` | テーブル構造の調査 |

---

## 依存関係

```toml
[project]
requires-python = ">=3.13"
dependencies = [
    "mss>=10.1.0",        # スクリーンショット
    "pillow>=12.0.0",     # 画像処理
    "pywin32>=311",       # Windows API
    "pywinauto>=0.6.9",   # UI Automation
    "mcp>=1.0.0",         # Model Context Protocol
]
```

---

## セットアップ

```powershell
# 仮想環境作成
python -m venv .venv
.\.venv\Scripts\activate

# パッケージインストール
pip install -e .
```

---

## 起動方法

### MCPクライアントから起動（推奨）

Claude Code / Codex CLI では `/browser:add-to-config` を実行して MCP 設定を追加します。  
uvx で GitHub から直接実行する設定が推奨です。

Codex CLI 例（`~/.codex/config.toml`）:
```toml
[mcp_servers.native-browser-control]
command = "uvx"
args = [
  "--python",
  "3.13",
  "--from",
  "git+https://github.com/TomCat2357/NativeBrowserControl",
  "native-browser-control",
]
```

### MCPサーバーとして

```powershell
# エントリーポイントから
native-browser-control

# または直接実行
python -m native_browser_control.core.server
```

### ワークフロースクリプトとして

```powershell
python -m native_browser_control.workflows.<path> --help
```

---

## アーキテクチャ

### ブラウザ接続フロー

```
1. find_browser_windows()
   └─ Desktop.windows() で全ウィンドウ取得
   └─ _match_browser_window() でフィルタリング
      ├─ タイトルキーワード/正規表現
      ├─ 可視性/有効性
      └─ 実行ファイルパス

2. get_browser_window() または connect_browser_by_index()
   └─ NativeBrowserDriver インスタンス作成

3. NativeBrowserDriver.connect()
   └─ Application.connect(process=pid)
   └─ app.window(handle=hwnd)
   └─ window.wait("visible")
```

### UI要素操作フロー

```
1. scan_page_elements()
   └─ window.descendants() で要素取得（control_type/titleで絞り込み）
   └─ max_elements で件数上限
   └─ current_elements / current_elements_info に格納

2. filter_current_elements()
   └─ 各種条件でフィルタリング
      ├─ control_types
      ├─ class_names
      ├─ name_regex / value_regex
      ├─ automation_id / automation_id_regex
      ├─ only_visible / require_enabled / only_focusable
      ├─ min_width / min_height
      ├─ omit_no_name / min_separator_count
      ├─ index_ranges
      └─ overwrite / output

3. click_by_index() / set_edit_text()
   └─ current_elements から要素取得
   └─ elem.invoke() または elem.click_input()
```

#### UI要素フィルタの補足

- `scan_page_elements`: `control_type`, `title`, `max_elements`, `foreground`, `maximize`, `settle_ms`
- `filter_current_elements`: `class_names`, `control_types`, `name_regex`, `value_regex`, `automation_id`, `automation_id_regex`, `only_visible`, `require_enabled`, `only_focusable`, `min_width`, `min_height`, `index_ranges`, `omit_no_name`, `min_separator_count`, `overwrite`, `output`

### スクリーンショットフロー

```
screenshot()
├─ ensure_visible() でウィンドウ準備
├─ prefer="printwindow"
│   └─ _capture_by_printwindow() [PrintWindow API]
│   └─ 失敗時 → _capture_by_screen_rect() にフォールバック
└─ prefer="screen"
    └─ _capture_by_screen_rect() [mss ライブラリ]
    └─ 失敗時 → _capture_by_printwindow() にフォールバック
```

---

## 注意事項

1. **Windows専用**: pywinauto / pywin32 に依存するためWindows環境が必須

2. **ブラウザ前面化**: 実ブラウザを前面化して操作するため、実行中は手動操作に影響

3. **DPI対応**: 高DPI環境での座標ズレに対応（`_enable_dpi_awareness()`）

4. **view-source**: `get_page_source()` は一時的にタブが増加（取得後に閉じる）

5. **スクリーンショット**: GPUレンダリングや仮想デスクトップ構成によってはPrintWindowが失敗する可能性あり

---

## 開発者向け情報

### テストファイル

- `test.py` - 基本テスト
- `test_native_browser_driver.py` - ドライバーテスト
- `test_native_browser_driver_unit.py` - ユニットテスト
- `test_native_browser_control_server_unit.py` - サーバーユニットテスト
- `test_output_mode.py` - 出力モードテスト

### ログ出力

ワークフローは `--log-level` オプションでログレベルを制御可能:

```bash
python -m native_browser_control.workflows.xxx --log-level DEBUG
```

### 出力制御

ワークフローは `--output` / `--stdout` / `--stderr` オプションで出力先を制御可能:

```bash
python -m native_browser_control.workflows.xxx --output silent
python -m native_browser_control.workflows.xxx --stdout stderr --stderr silent
```
