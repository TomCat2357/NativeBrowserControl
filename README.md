# Native Browser Control (MCP)

Windows の UI Automation (pywinauto / pywin32) を使って、Selenium なしで Chrome / Edge を直接操作する MCP サーバーです。標準入出力で待ち受け、LLM エージェントなどからツール呼び出しでブラウザを制御できます。ツール引数 `browser` に `edge` を渡すと Edge を操作できます（省略時は `chrome`）。

**Claude Code プラグイン対応**: このリポジトリは Claude Code プラグインとしても使用できます。プラグインをインストールすると、`/browser:*` コマンドでブラウザを簡単に操作できます。

## 主な機能
- ブラウザウィンドウの列挙と接続（起動中ウィンドウ一覧/接続）
- ナビゲーション、URL/タイトル取得、ブラウザ概要取得
- スクリーンショット（ウィンドウ / 画面全体、base64 返却）
- ページテキスト/HTMLソース取得
- テキスト入力、ページ内検索
- スクロール、タブ操作、履歴/ズーム操作
- 座標クリック、UIA 要素スキャン/フィルタ/クリック/テキスト設定
- クリップボード操作、待機

## 前提条件
- Windows 環境（pywinauto / pywin32 依存）。Chrome または Edge がインストールされていること。
- Python 3.13 以上
- 実ブラウザを前面化して操作するため、実行中は手動操作に影響します。

## セットアップ

### 方法1: Claude Code プラグインとして使用（推奨）

Claude Code でマーケットプレイスを追加し、プラグインをインストールします：

```bash
# マーケットプレイスを追加
/plugin marketplace add TomCat2357/NativeBrowserControl

# プラグインをインストール
/plugin install native-browser-control
```

プラグインをインストールしたら、MCP サーバーを設定します：

```bash
/add-to-config
```

このコマンドを実行すると、インストール方法（uvx / pip-editable / script）を選択し、必要な情報を入力することで、自動的に設定ファイル（`~/.claude.json` または `~/.codex/config.toml`）に MCP サーバーの設定が追加されます。

**推奨設定**: uvx を使用した GitHub からの直接実行（インストール不要で常に最新版を使用できます）

### 方法2: 開発者向けセットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

## 起動方法

### プラグイン使用時

Claude Code で `/browser:*` コマンドを使用するだけで自動的に起動します。例：
```
/browser:connect
/browser:navigate https://example.com
/browser:screenshot
```

### 直接起動（開発者向け）

```powershell
native-browser-control
# または
python -m native_browser_control.core.server
```
- サーバー名は `native-browser-control`。MCP クライアント側から各ツールを呼び出して操作します。

## ツール一覧（概要）
- ウィンドウ接続: `list_browser_windows`, `connect_browser`
- ナビゲーション: `navigate`, `get_url`, `get_title`, `get_browser_summary`
- スクリーンショット: `screenshot`, `full_screenshot`
- コンテンツ取得: `get_page_text`, `get_page_source`
- 入力/検索: `type_text`, `find_text`
- スクロール: `scroll`
- タブ操作: `new_tab`, `close_tab`, `switch_tab`
- ブラウザ操作: `back`, `forward`, `refresh`, `zoom`
- 座標クリック: `click`
- UI要素操作: `scan_elements`, `filter_elements`, `list_elements`, `elements_summary`, `click_element`, `set_element_text`
- 待機・クリップボード: `wait`, `copy_selected`, `paste`

## UI要素スキャンの使い方
- `scan_elements` で要素をスキャンし、`current_elements` を更新します（`control_type` / `title` / `max_elements` で簡易絞り込み）。
- `filter_elements` で条件絞り込みできます（`control_types` / `class_names` / `name_regex` / `value_regex` / `automation_id` / `automation_id_regex` / `only_visible` / `require_enabled` / `only_focusable` / `min_width` / `min_height` / `omit_no_name` / `min_separator_count` など）。
- `output` は `simple` / `summary` / `full` を指定可能。`overwrite=false` で `current_elements` を保持できます。
- `list_elements` / `elements_summary` で一覧・集計表示、`click_element` / `set_element_text` で操作します。
- `index_ranges` は `"1:4,10:-1"` のような Python スライス形式です。

## ワークフロー/ユーティリティ
調査・抽出・ダウンロード向けのスクリプトが `native_browser_control/workflows/` にあります。
例:
- `analysis/parse_log.py`: チャットログの抽出表示
- `extraction/kesai_page.py`: 決裁ページ情報の抽出
- `downloads/attachments_basic.py`, `downloads/attachments_conductor.py`: 添付ファイルのダウンロード補助
- `investigations/*`: チェックボックスやテーブル構造の調査系スクリプト

基本的に `python -m native_browser_control.workflows.<path> --help` で利用方法を確認できます。

## ドキュメント
- `docs/DOCUMENTATION.md`: 詳細ドキュメント
- `browser_table_extraction.md`: ブラウザテーブル抽出の手順メモ
- `approval_system_file_download_procedure.md`: 承認システムのファイルDL手順

## 主要ファイル
- `native_browser_control/core/server.py`: MCP サーバー本体。ツール定義とハンドラーを提供。
- `native_browser_control/core/driver.py`: Chrome/Edge UI 自動化ロジック。
- `native_browser_control/utils/output.py`: ワークフローの出力/ログ制御ユーティリティ。
- `native_browser_control/workflows/`: 調査・ダウンロード・抽出などのワークフロー群。
- `pyproject.toml`: パッケージ/スクリプト定義。

## リソース
- `tips://file-dialog-text-input`: ファイルダイアログでの入力方法
- `tips://gemini-file-upload`: Gemini のファイルアップロード手順

## Claude Code プラグイン機能

このリポジトリには Claude Code プラグインが含まれており、以下の機能を提供します：

### スラッシュコマンド（全31個）

#### ブラウザ接続・管理
- `/browser:list-windows` - 起動中のブラウザウィンドウ一覧を取得
- `/browser:connect` - 指定ブラウザに接続（未起動なら起動）
- `/browser:wait` - 指定秒数待機

#### ナビゲーション
- `/browser:navigate` - 指定URLに移動
- `/browser:get-url` - 現在のページURLを取得
- `/browser:get-title` - 現在のページタイトルを取得
- `/browser:get-browser-summary` - ブラウザ概要を取得
- `/browser:back` - 前のページに戻る
- `/browser:forward` - 次のページに進む
- `/browser:refresh` - ページをリロード

#### スクリーンショット
- `/browser:screenshot` - ブラウザウィンドウを撮影
- `/browser:full-screenshot` - 画面全体を撮影

#### コンテンツ取得
- `/browser:get-page-text` - ページ全体のテキストを取得
- `/browser:get-page-source` - HTMLソースを取得

#### テキスト入力・検索
- `/browser:type-text` - テキストを入力
- `/browser:find-text` - ページ内検索

#### スクロール
- `/browser:scroll` - ページをスクロール

#### タブ操作
- `/browser:new-tab` - 新しいタブを開く
- `/browser:close-tab` - 現在のタブを閉じる
- `/browser:switch-tab` - タブを切り替え

#### ズーム
- `/browser:zoom` - ズーム操作

#### クリック操作
- `/browser:click` - 座標でクリック

#### 要素操作（重要）
- `/browser:scan-elements` - ページ上の要素をスキャン
- `/browser:filter-elements` - スキャン済み要素をフィルタリング
- `/browser:list-elements` - スキャン済み要素の一覧を表示
- `/browser:elements-summary` - スキャン済み要素の統計情報を表示
- `/browser:click-element` - 要素をインデックスでクリック
- `/browser:set-element-text` - 要素のテキストを設定

#### クリップボード
- `/browser:copy-selected` - 選択中のテキストをコピー
- `/browser:paste` - クリップボードの内容を貼り付け

#### 設定
- `/browser:add-to-config` - MCP サーバー設定を追加

### Skill

- **native-browser-usage**: NativeBrowserControl の使い方、Tips、ベストプラクティスを提供

### 使い方の例

#### 基本的な流れ

1. ブラウザに接続
```
/browser:connect
```

2. URLに移動
```
/browser:navigate https://example.com
```

3. スクリーンショットで確認
```
/browser:screenshot
```

4. 要素をスキャンしてボタンをクリック
```
/browser:scan-elements
/browser:click-element 42
```

## 注意事項
- ウィンドウが非表示/最小化の場合は復帰を試みますが、DPI 設定や仮想デスクトップ構成によっては座標がずれることがあります。
- `get_page_source` は view-source を開いて取得するため、一時的にタブが増えます（取得後に閉じます）。
- 実ブラウザウィンドウを前面化・最大化して操作するため、実行中は手動操作に影響します。
- `scan_elements` 実行後に取得したインデックスを `click_element` で利用してください。

## ライセンス

MIT
