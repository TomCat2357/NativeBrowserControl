---
description: ページ全体のテキストを取得
argument-hint: [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__get_page_text
---

現在のページの全テキストを取得します（Chrome/Edge対応、Ctrl+A, Ctrl+Cで取得）

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `browser` を解析
2. `mcp__native-browser-control__get_page_text` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
3. ページ全体のテキストを表示
4. 注意: Ctrl+A, Ctrl+Cを使用するため、クリップボードの内容が上書きされます
