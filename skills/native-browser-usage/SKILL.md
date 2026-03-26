---
name: native-browser-usage
description: Direct NativeBrowserDriver workflows for Chrome and Edge on Windows without using the MCP server. Use when Codex needs to control a real browser from this repository by running the bundled workflow script for navigation, screenshots, page text or source capture, element scanning, clicking, text input, scrolling, tabs, history, zoom, clipboard, or mouse movement.
---

# NativeBrowserDriver Direct Workflow

この skill では MCP server や `/browser:*` を使わず、同梱スクリプトから `native_browser_control.driver` を直接呼び出す。

## 実行ルール

- `browser` は常に明示する。未指定なら確認を取り、`chrome` を既定扱いしない。
- Edge を操作する場合は、workflow JSON のトップレベルに必ず `"browser": "edge"` を入れる。
- 要素 index を使う操作は、同じ workflow invocation の中で `scan` を先に実行してから続ける。
- `connect` は `window_index` または `launch: true` のどちらかを指定する。

## 基本コマンド

PowerShell 例:

```powershell
.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_workflow.py --spec-file .\workflow.json
```

インライン JSON 例:

```powershell
.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_workflow.py --spec-json '{"browser":"chrome","connect":{"window_index":0},"steps":[{"action":"summary"}]}'
```

Agent 向けコマンドラッパー例:

```powershell
.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_command.py scan --browser edge --window-index 0 --control-type Button --only-visible
.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_command.py click --browser edge --name-regex "^(検索|Search)$" --control-type Button --only-visible
```

`run_native_browser_command.py` の主な subcommand は `summary` / `navigate` / `scan` / `click` / `set-text` / `screenshot`。

## 運用手順

1. ユーザーが対象ブラウザを明示していなければ確認する。
2. `connect` と `steps` を持つ workflow JSON を作る。
3. 1 回の workflow に、必要な `scan -> filter/get_index -> click_index/set_text` をまとめる。
4. 返却 JSON の `results` と `artifacts` を読んで次の操作を決める。

## 参照ファイル

- `references/workflow-schema.md`: workflow JSON のスキーマと step 一覧
- `references/workflow-examples.md`: よく使う workflow 例
- `scripts/run_native_browser_command.py`: agent 向けのコア操作ラッパー
- `../../.agents/skills/native-browser-usage/SKILL.md`: Codex CLI から見える repo skill 入口

## 補足

- `summary` はブラウザ概要取得用。index ベースの操作前提 state は `scan` で作る。
- `screenshot` と `full_screenshot` は既定で画像を一時ディレクトリへ保存し、絶対パスを返す。
- legacy の MCP server / plugin / `commands/` は互換のため残っているが、この skill では使わない。
