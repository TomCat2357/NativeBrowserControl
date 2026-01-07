---
description: NativeBrowserControl を Claude Code（~/.claude.json）/ Codex CLI（.toml）に追加する
argument-hint: [config-file-path]
allowed-tools: Read, Write, Edit, AskUserQuestion
---

指定ファイルに `native-browser-control` MCPサーバーの設定を追記/更新します。

**対象ファイル**: `$ARGUMENTS`（省略時はプラグインスコープから自動選択）

**手順**
1. 設定対象ファイルのパスを決める（ユーザーには質問しない）
   - `$ARGUMENTS` があればそれを使う
   - 無ければ、プラグインスコープに合わせて自動選択する
     - `~/.claude.json` が存在する → Claude Code（ユーザースコープ）として `~/.claude.json`
     - それ以外で `~/.codex/config.toml` が存在する → Codex CLI（ユーザースコープ）として `~/.codex/config.toml`
     - どちらも無い → 対象ファイルが特定できないため終了（`$ARGUMENTS` で明示してもらう）
2. 形式を判定（ユーザーに "どの環境か" は聞かない）
   - 拡張子が `.toml` → Codex CLI 形式（TOML）
   - 拡張子が `.json` → Claude Code 形式（JSON、既定は `~/.claude.json`）
   - それ以外は、ユーザーに「`~/.claude.json` か `.toml` を指定してほしい」旨を伝えて終了
3. 実行環境（Windows / WSL）の扱いを "質問せず" に判断する
   - 以降でユーザーから受け取るパス表記が `C:\\...` / `D:\\...` のような Windows 形式なら Windows として扱う
   - `/...` や `/mnt/...` のような POSIX 形式なら WSL/Linux として扱う
   - 以降の設定パスは、その判断結果に合わせた「実行環境から見える絶対パス」を採用する
4. インストール方法を質問する（必須）
   - `AskUserQuestion`:
     - 「NativeBrowserControl のインストール方法を選択してください」
     - オプション:
       - `uvx`: uvx で GitHub から直接実行（推奨）
       - `pip-editable`: pip install -e で開発インストール済み
       - `script`: Pythonスクリプト直接実行
5. インストール方法に応じて必要な情報を質問する
   - `uvx` の場合:
     - リポジトリURL（デフォルト: `git+https://github.com/TomCat2357/NativeBrowserControl`）
     - Python バージョン（デフォルト: `3.13`）
   - `pip-editable` の場合:
     - コマンド名（デフォルト: `native-browser-control`）
   - `script` の場合:
     - Pythonコマンドパス（デフォルト: `python`）
     - `native_browser_control_server.py` の絶対パス
6. 追加/更新する設定を提示し、y/n で確認してから書き込み
   - 既に `native-browser-control` の設定が入っている場合は値を置換（重複させない）

**追加/更新する設定（Claude Code / `~/.claude.json`）**

uvx の場合:
```json
{
  "native-browser-control": {
    "command": "uvx",
    "args": [
      "--python",
      "3.13",
      "--from",
      "git+https://github.com/TomCat2357/NativeBrowserControl",
      "native-browser-control"
    ]
  }
}
```

pip-editable の場合:
```json
{
  "native-browser-control": {
    "command": "native-browser-control",
    "args": []
  }
}
```

script の場合:
```json
{
  "native-browser-control": {
    "command": "python",
    "args": [
      "C:/absolute/path/to/NativeBrowserControl/native_browser_control/core/server.py"
    ]
  }
}
```

**追加/更新する設定（Codex CLI / `.toml`）**

uvx の場合:
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

pip-editable の場合:
```toml
[mcp_servers.native-browser-control]
command = "native-browser-control"
args = []
```

script の場合:
```toml
[mcp_servers.native-browser-control]
command = "python"
args = [
  "C:/absolute/path/to/NativeBrowserControl/native_browser_control/core/server.py",
]
```

**注意**
- Claude Code と Codex CLI の設定ファイルは別物（Claude Code は `~/.claude.json`、Codex CLI は `~/.codex/config.toml`）
- スクリプトパスは「NativeBrowserControl を起動する環境（WSL/Windows）から見える絶対パス」
- WSL で動かすなら `/mnt/c/...` も "WSLから見えるパス" として有効（Windows の `C:\\...` とは別物なので混ぜない）
- Windows 環境で使用することを前提としています（UI Automation が必要なため）
