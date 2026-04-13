# Native Browser Control

Windows の UI Automation (`pywinauto` / `pywin32`) を使って、Selenium なしで Chrome / Edge を直接操作するプロジェクトです。

推奨導線は repo 同梱 skill `skills/native-browser-usage/` と補助スクリプト `skills/native-browser-usage/scripts/run_native_browser_workflow.py` / `skills/native-browser-usage/scripts/run_native_browser_command.py` を使う方法です。Codex CLI 向け repo skill は `.agents/skills/`、Claude Code 向け project skill / slash command は `.claude/skills/` に同梱しています。

## 主な機能

- 起動中ブラウザへの接続、または新規起動
- URL 遷移、URL/タイトル/概要取得
- ウィンドウスクリーンショット、全画面スクリーンショット
- ページ全文テキスト取得
- 要素スキャン、フィルタ、index 取得、クリック、テキスト設定
- テキスト入力、ページ内検索、スクロール
- タブ、履歴、ズーム、クリップボード、マウス移動

## 前提条件

- Windows 環境
- Chrome または Edge がインストール済み
- Python 3.11.9
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

### Agent 向けコマンド入口

workflow JSON を毎回手書きせずに使うため、コア操作向けのラッパー `skills/native-browser-usage/scripts/run_native_browser_command.py` を追加しています。

直接実行例:

```powershell
.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_command.py scan --browser edge --window-index 0 --control-type Button --only-visible
.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_command.py click --browser edge --name-regex "^(検索|Search)$" --control-type Button --only-visible
```

対応 subcommand:

- `summary`
- `navigate`
- `scan`
- `click`
- `set-text`
- `screenshot`

`click` と `set-text` は単一 invocation 内で `scan -> filter -> click/set_text` を組み立てます。前回の `scan` の index を別 invocation に持ち回す前提にはしません。

### Claude Code / Codex CLI

Claude Code:

- `.claude/skills/native-browser-*/SKILL.md` を project skill として同梱
- `/native-browser-scan browser=edge window_index=0 control_type=Button only_visible=true` のように実行

Codex CLI:

- `.agents/skills/native-browser-*/SKILL.md` を repo skill として同梱
- `$native-browser-scan browser=edge window_index=0 control_type=Button only_visible=true` のように実行

Codex CLI の slash wrapper（任意）:

- `codex-prompts/*.md` に `/prompts:native-browser-*` 用テンプレートを同梱
- `.\scripts\install_codex_prompts.ps1` を実行すると `~/.codex/prompts/` へコピー
- 例: `/prompts:native-browser-scan browser=edge window_index=0 control_type=Button`

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
- `.agents/skills/`
- `.claude/skills/`
- `codex-prompts/`

## 主なファイル

- `native_browser_control/driver.py`: 実ブラウザ制御の本体
- `skills/native-browser-usage/`: 推奨 skill
- `skills/native-browser-usage/scripts/run_native_browser_workflow.py`: direct driver 実行入口
- `skills/native-browser-usage/scripts/run_native_browser_command.py`: agent 向けコア操作ラッパー
- `.agents/skills/`: Codex CLI の repo skill 入口
- `.claude/skills/`: Claude Code の project skill / slash command 入口
- `codex-prompts/`: Codex CLI の `/prompts:` 用テンプレート

## 注意事項

- DPI 設定や複数モニタ環境では座標操作がずれることがあります。
- 要素 index は永続ではありません。ページ更新や再描画で変わるため、毎回 workflow 内で `scan` からやり直します。
## ライセンス

MIT
