---
description: ブラウザ概要（URL/タイトル/状態）を取得
argument-hint: [browser=chrome|edge] [max_text_len=50]
allowed-tools: mcp__native-browser-control__get_browser_summary
---

現在のブラウザ概要（URL/タイトル/状態/位置サイズ/descendants統計）をJSONで取得します（Chrome/Edge対応）

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）
- `max_text_len`: URL/タイトル等の最大文字数（省略時: 50）

**手順**
1. 引数から `browser`, `max_text_len` を解析
2. `mcp__native-browser-control__get_browser_summary` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
   - `max_text_len`: 整数値（省略時は 50）
3. ブラウザ概要情報をJSON形式で表示
