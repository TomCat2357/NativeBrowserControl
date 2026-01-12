---
description: 現在のページタイトルを取得
argument-hint: [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__get_title
---

現在のページのタイトルを取得します（Chrome/Edge対応）

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `browser` を解析
2. `mcp__native-browser-control__get_title` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
3. 現在のページタイトルを表示
