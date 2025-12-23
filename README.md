# Native Browser Control (MCP)

Windows の UI Automation (pywinauto / pywin32) を使って、Selenium なしで Chrome / Edge を直接操作する MCP サーバーです。標準入出力で待ち受け、LLM エージェントなどからツール呼び出しでブラウザを制御できます。ツール引数 `browser` に `edge` を渡すことで Edge を操作できます（省略時は `chrome`）。

## 主な機能W
- ナビゲーション: URL への移動、現在 URL/タイトル取得
- スクリーンショット: Chrome ウィンドウ、全画面の撮影（PNG/JPEG、base64 返却）
- コンテンツ取得: ページ全体のテキスト、HTML ソースのコピー
- 入力/検索: ページ内検索、テキスト貼り付け or タイプ入力WWWW
- スクロール: 上下/ページ単位/最上部・最下部への移動
- タブ操作: 新規タブ、クローズ、次/前タブ切り替え
- ブラウザ操作: 戻る/進む/リロード/ズーム in/out/reset
- 座標/要素操作: ウィンドウ座標クリック、UI 要素スキャンとインデックス指定クリック
- クリップボード: 選択文字列のコピー、貼り付け、待機ユーティリティ

## 前提条件
- Windows 環境（pywinauto/pywin32 依存）。Chrome または Edge がインストールされていること。
- Python 3.13 以上
- 標準ディスプレイ DPI 設定に依存するため、ウィンドウを前面化できる状態で実行してください。

## セットアップ
```powershell
# 仮想環境作成（任意）
python -m venv .venv
.\.venv\Scripts\activate

# 依存関係をインストール
pip install -e .
```

## 起動方法
- MCP サーバー（標準入出力）として起動:W
```powershell
native-browser-control
# または
python native_browser_control_server.py
```
- サーバー名は `native-browser-control`。MCP クライアント側から各ツールを呼び出して操作します。

## 提供ツールの概要
- ナビゲーション: `navigate`, `get_url`, `get_title`
- スクリーンショット: `screenshot`, `full_screenshot`
- コンテンツ取得: `get_page_text`, `get_page_source`
- 入力/検索: `type_text`, `find_text`
- スクロール: `scroll`
- タブ操作: `new_tab`, `close_tab`, `switch_tab`
- ブラウザ操作: `back`, `forward`, `refresh`, `zoom`
- 座標/要素: `click`, `scan_elements`, `list_elements`, `elements_summary`, `click_element`
- 待機・クリップボード: `wait`, `copy_selected`, `paste`

## 注意事項
- 実ブラウザウィンドウを前面化・最大化して操作するため、実行中は手動操作に影響します。
- ウィンドウが非表示/最小化の場合は自動で復帰を試みますが、DPI 設定や仮想デスクトップ構成によっては座標がずれることがあります。
- `scan_elements` 実行後に取得したインデックスを `click_element` で利用してください。
  - `scan_elements` は件数のみ返します。詳細一覧は `list_elements`、タイプ別集計は `elements_summary` を使ってください。

## 主要ファイル
- `native_browser_control_server.py`: MCP サーバー本体。ツール定義とハンドラーを提供。
- `native_browser_driver.py`: Chrome/Edge UI 自動化ロジック。スクリーンショット、入力、タブ/スクロール操作などを実装。
- `pyproject.toml`: パッケージ/スクリプト定義。
