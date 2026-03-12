# Native Browser Control

Windows の UI Automation (`pywinauto` / `pywin32`) を使って、Selenium なしで Chrome / Edge を直接操作するプロジェクトです。

現在の推奨導線は、MCP server ではなく repo 同梱 skill `skills/native-browser-usage/` と補助スクリプト `skills/native-browser-usage/scripts/run_native_browser_workflow.py` を使う方法です。`server.py`、`commands/`、`.claude-plugin/` は互換のため残していますが legacy 扱いです。

## 主な機能

- 起動中ブラウザへの接続、または新規起動
- URL 遷移、URL/タイトル/概要取得
- ウィンドウスクリーンショット、全画面スクリーンショット
- ページ全文テキスト取得、HTML ソース取得
- 要素スキャン、フィルタ、index 取得、クリック、テキスト設定
- テキスト入力、ページ内検索、スクロール
- タブ、履歴、ズーム、クリップボード、マウス移動

## 前提条件

- Windows 環境
- Chrome または Edge がインストール済み
- Python 3.13 以上
- UI Automation の性質上、ブラウザを前面化して操作するため手動操作と競合する

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

## 推奨: skill + direct driver workflow

### browser 選択ルール

- `browser` は必須です。`chrome` 既定値には頼りません。
- Edge を操作する場合は、workflow JSON のトップレベルに必ず `"browser": "edge"` を入れます。
- browser が曖昧なまま実行しません。

### 実行方法

`skills/native-browser-usage/scripts/run_native_browser_workflow.py` は `--spec-json` または `--spec-file` で workflow JSON を受け取ります。

```powershell
.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_workflow.py --spec-file .\workflow.json
```

### workflow JSON の最小例

```json
{
  "browser": "chrome",
  "connect": {
    "window_index": 0
  },
  "steps": [
    {
      "action": "summary"
    },
    {
      "action": "navigate",
      "url": "https://example.com"
    },
    {
      "action": "wait",
      "seconds": 2
    },
    {
      "action": "screenshot",
      "fmt": "PNG"
    }
  ]
}
```

### 重要な運用ルール

- `connect` では `window_index` か `launch: true` を指定します。
- `filter`、`get_index`、`click_index`、`set_text`、`move_mouse` の index 指定は、同じ workflow invocation 内の先行 `scan` が必須です。
- `screenshot` と `full_screenshot` は既定で一時ディレクトリへ保存し、返却 JSON に絶対パスを入れます。

### 参照

- `skills/native-browser-usage/SKILL.md`
- `skills/native-browser-usage/references/workflow-schema.md`
- `skills/native-browser-usage/references/workflow-examples.md`

## Legacy: MCP server / plugin

互換用として次は残しています。

- `native_browser_control/server.py`
- `commands/`
- `.claude-plugin/`

ただし、legacy 経路でも browser は明示指定前提です。`driver_read` / `driver_call` / `driver_tool_info` では browser を省略して暗黙に `chrome` へ落とさないようにしています。既存の slash command も browser を明示して使ってください。

### 直接起動

```powershell
native-browser-control
# または
python -m native_browser_control.server
```

### add-to-config

MCP 設定追加の legacy command は `commands/add-to-config.md` に残しています。

## 主なファイル

- `native_browser_control/driver.py`: 実ブラウザ制御の本体
- `skills/native-browser-usage/`: 推奨 skill
- `skills/native-browser-usage/scripts/run_native_browser_workflow.py`: direct driver 実行入口
- `native_browser_control/server.py`: legacy MCP server

## 注意事項

- DPI 設定や複数モニタ環境では座標操作がずれることがあります。
- 要素 index は永続ではありません。ページ更新や再描画で変わるため、毎回 workflow 内で `scan` からやり直します。
- `get_page_source` は一時的に view-source タブを開きます。

## ライセンス

MIT
