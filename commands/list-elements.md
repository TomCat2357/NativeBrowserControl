---
description: スキャン済み要素の一覧を表示
argument-hint: [browser=chrome|edge] [index_ranges=...]
allowed-tools: mcp__native-browser-control__list_elements
---

既にスキャンした要素の一覧を表示します。

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）
- `index_ranges`: 表示する要素のインデックス範囲（例: '1:4,10:-1'、省略時: 全要素）

**手順**
1. 引数から `browser`, `index_ranges` を解析
2. `mcp__native-browser-control__list_elements` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
   - `index_ranges`: 解析した値（省略時は全要素）
3. 要素一覧をインデックス付きで表示
