---
description: 現在のページURLを取得
argument-hint: browser=chrome|edge
allowed-tools: mcp__native-browser-control__get_url
---

現在のページのURLを取得します（Chrome/Edge対応）

**引数**
- `browser`: 対象ブラウザ（chrome または edge、必須）

**手順**
1. 引数から `browser` を解析
2. `mcp__native-browser-control__get_url` を呼び出す
   - `browser`: 解析した値（必須。省略は不可）
3. 現在のURLを表示
