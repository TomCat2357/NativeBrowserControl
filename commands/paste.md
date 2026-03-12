---
description: クリップボードの内容を貼り付け
argument-hint: browser=chrome|edge
allowed-tools: mcp__native-browser-control__paste
---

クリップボードの内容をフォーカス中の要素に貼り付けます（Chrome/Edge対応、Ctrl+V）。

**引数**
- `browser`: 対象ブラウザ（chrome または edge、必須）

**手順**
1. 引数から `browser` を解析
2. `mcp__native-browser-control__paste` を呼び出す
   - `browser`: 解析した値（必須。省略は不可）
3. 貼り付け操作の成功を確認
4. 注意: 事前に入力フィールドなどにフォーカスしておく必要があります
