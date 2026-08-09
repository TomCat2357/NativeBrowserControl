# Native Browser Control

Windows の UI Automation (`pywinauto` / `pywin32`) を使って、Selenium なしで Chrome / Edge を直接操作するプロジェクトです。

利用導線は、MCPが利用できない環境でも成立する直接runnerを中心に構成しています。

- **直接runner (Codex / ChatGPT 向け、推奨)**: `skills/native-browser-usage/scripts/` から MCPサーバーなしで操作します。
- **MCP サーバー (対応クライアント向け、任意)**: `.claude-plugin/` と `.mcp.json` は互換経路として残しています。利用環境にMCPツールが表示されない場合は使用しません。
- **スキル (Codex CLI / Claude Code project skill)**: `.agents/skills/native-browser-*/` (Codex) と `.claude/skills/native-browser-*/` (Claude Code project skill) を同梱しています。
- **直接スクリプト実行 (CI / バッチ)**: `skills/native-browser-usage/scripts/run_native_browser_workflow.py` または `run_native_browser_command.py` を直接呼び出します。

`server.py` の旧 3 ツール (`driver_call` / `driver_read` / `driver_tool_info`) は互換のため残していますが、新規利用は個別 MCP ツール (`driver_<method>`) を推奨します。

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
- Python 3.11 以上
- UI Automation の性質上、ブラウザを前面化して操作するため手動操作と競合する

## セットアップ

```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -e .
```

## プラグインとしての導入 (Codex / ChatGPT)

このリポジトリは、MCPサーバーを利用できないCodex / ChatGPT環境でも動くskill中心のプラグイン構成です。

- `.codex-plugin/plugin.json`: プラグインマニフェスト
- `skills/`: `native-browser-usage` と、summary / navigate / scan / click / set-text / screenshot の操作別skill
- `.mcp.json`: MCP対応クライアント向けの任意の接続定義（Codexプラグインは読み込みません）

ローカルで試す場合は、Codexのローカルマーケットプレイスへこのリポジトリを登録して `native-browser-control` をインストールし、反映後に新しい会話で `$native-browser-usage` または操作別skillを呼び出してください。skillは同梱runnerを実行するため、MCPサーバーの認証やtool公開状態に依存しません。実行時はskillの配置場所からrunnerの絶対パスを解決し、cwdから `skills/...` を推測しません。Windows環境では `uv`、Python 3.11以上、ChromeまたはEdgeが必要です。

MCPを利用する場合のみ、`.mcp.json`の取得元とプラグインバージョンを同時に更新してください。

このリポジトリは既存のユーザー設定や個人マーケットプレイスを自動変更しません。マーケットプレイス登録は利用環境のポリシーに合わせて行ってください。

## プラグインとしての導入 (Claude Code)

Claude Code から MCP ツールを使うには `/plugin install` で本リポジトリのプラグインを取り込みます。3 通りのインストール経路があります。

### 1. マーケットプレイス経由 (推奨)

```text
/plugin marketplace add TomCat2357/NativeBrowserControl
/plugin install native-browser-control@native-browser-control-tools
```

Claude Code がリポジトリを取得し、`.claude-plugin/.mcp.json` の定義に従って `uvx` で MCP サーバーを起動します。

### 2. ローカル marketplace.json から

ローカルにクローンしたリポジトリをそのまま使う場合:

```text
/plugin marketplace add file:///<repo absolute path>/.claude-plugin/marketplace.json
/plugin install native-browser-control
```

### 3. `.claude.json` に直接登録 (プラグインを使わない場合)

`commands/add-to-config.md` の例に従い、ユーザーの `.claude.json` の `mcpServers` に以下を追記します。

```json
{
  "native-browser-control": {
    "command": "uvx",
    "args": [
      "--python", "3.11",
      "--from", "git+https://github.com/TomCat2357/NativeBrowserControl",
      "native-browser-control"
    ]
  }
}
```

### 前提

- `uv` (および `uvx`) がインストール済み。未導入の場合は `pip install uv` か公式インストーラ
- `uv python install 3.11` で Python 3.11 を確保 (`pyproject.toml` が `>=3.11,<3.12` を要求)
- Windows 環境 (pywin32 / pywinauto 依存)

### インストール後の確認

```bash
claude mcp list   # native-browser-control が表示されること
```

Claude Code 内のツール補完で `mcp__native-browser-control__` を打つと、launch 系・list 系・`driver_*` 50+ が候補に出ます。

## MCP サーバーの使い方

### 公開ツールの全体像

| 種別 | ツール | 役割 |
|---|---|---|
| 起動系 | `launch_chrome` / `launch_edge` | 新規ウィンドウを起動して `session_id` を返す |
| 起動系 | `list_running_browsers` | 起動中の Chrome/Edge ウィンドウ一覧を返す (`pid` / `title` / `handle` / `rect` / `is_visible` / `is_minimized` / `is_foreground`) |
| 起動系 | `connect_browser` | 既存ウィンドウに `window_index` 指定で接続して `session_id` を返す |
| 動的 | `driver_<method_name>` | NativeBrowserDriver の公開メソッド (約 50 個) を 1 メソッド = 1 ツールとして動的公開 |
| レガシー | `driver_call` / `driver_read` / `driver_tool_info` | 互換のため残置されたリフレクション型 API |

### 典型的なフロー

1. ブラウザを立ち上げてセッションを取得
   ```json
   { "tool": "mcp__native-browser-control__launch_chrome", "args": {} }
   ```
   → `{"ok": true, "session_id": "chrome:abcd1234", "browser": "chrome", ...}`

2. URL に遷移
   ```json
   { "tool": "mcp__native-browser-control__driver_navigate",
     "args": { "session_id": "chrome:abcd1234", "url": "https://example.com" } }
   ```

3. ページ要素をスキャン
   ```json
   { "tool": "mcp__native-browser-control__driver_scan_page_elements",
     "args": { "session_id": "chrome:abcd1234",
                "control_type": "Button", "only_visible": true } }
   ```

4. インデックスでクリック
   ```json
   { "tool": "mcp__native-browser-control__driver_click_by_index",
     "args": { "session_id": "chrome:abcd1234", "index": 3 } }
   ```

### `session_id` と `browser` パラメータ

- すべての動的ツール (`driver_*`) は `session_id` (任意) と `browser` (任意) を受け付けます。
- `session_id` を指定するとそのセッション (= 接続済みウィンドウ) を直接利用します。
- `session_id` を省略した場合、`browser` (`chrome` または `edge`) のアクティブセッションを解決します。
- どちらも省略するとエラーになります。

### 既存ウィンドウへの再接続

```json
{ "tool": "mcp__native-browser-control__list_running_browsers",
  "args": { "browser": "edge" } }
```
→ 一覧から目的のウィンドウの `index` を確認し、

```json
{ "tool": "mcp__native-browser-control__connect_browser",
  "args": { "browser": "edge", "window_index": 0 } }
```
→ `session_id` を取得して以降は `driver_*` を呼び出します。

### レガシー API との互換

既存の `driver_call(method=..., args=..., kwargs=...)` 呼び出しは引き続き動作します。`driver_tool_info` を呼べば、ドライバーの全公開メソッドのシグネチャと docstring を 1 度に取得できます (個別 MCP ツールにメソッドが見当たらないときの確認用)。

### 動的ツール登録の無効化

ツール数が多すぎる、あるいは LLM のコンテキスト消費を抑えたい場合は環境変数で動的登録を切れます (起動系 4 ツールとレガシー 3 ツールは残ります)。

```bash
NATIVE_BROWSER_MCP_DYNAMIC=0 uvx ... native-browser-control
```

## スキルと MCP サーバーの使い分け

| ユースケース | 推奨経路 |
|---|---|
| Claude Code から自然言語で対話的に操作 | **MCP サーバー** (`/plugin install` 後、ツール補完が効く) |
| Codex CLI から呼ぶ | **`.agents/skills/native-browser-*/`** (slash command 形式) |
| Claude Code でも slash command を使いたい | **`.claude/skills/native-browser-*/`** (project skill) |
| バッチで決まった workflow を実行 | **`run_native_browser_workflow.py` + JSON 仕様** (CI / 定期ジョブ向け) |
| ドライバー API を直接叩く | **Python から `import native_browser_control`** |

補足:

- MCP サーバーとスキル/直接スクリプトは互いに干渉しません。同じ NativeBrowserDriver を裏で使う 3 系統の入口です。
- セッション分離: MCP サーバー経由のセッションとスクリプト直接実行のセッションは別プロセスのため共有されません。

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
- `.codex-plugin/plugin.json`: Codex / ChatGPT プラグインマニフェスト
- `.mcp.json`: Codex / ChatGPT 用 MCP サーバー定義
- `skills/native-browser-usage/`: 推奨 skill
- `skills/native-browser-{summary,navigate,scan,click,set-text,screenshot}/`: 操作別 skill
- `skills/native-browser-usage/scripts/run_native_browser_workflow.py`: direct driver 実行入口
- `skills/native-browser-usage/scripts/run_native_browser_command.py`: agent 向けコア操作ラッパー
- `.agents/skills/`: Codex CLI の repo skill 入口
- `.claude/skills/`: Claude Code の project skill / slash command 入口
- `codex-prompts/`: Codex CLI の `/prompts:` 用テンプレート
- `native_browser_control/server.py`: legacy MCP server

## 注意事項

- DPI 設定や複数モニタ環境では座標操作がずれることがあります。
- 要素 index は永続ではありません。ページ更新や再描画で変わるため、毎回 workflow 内で `scan` からやり直します。
## ライセンス

MIT
