---
description: 要素をインデックスでクリック
argument-hint: <index> [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__click_element
---

スキャンした要素をインデックス指定でクリックします。

**引数**
- `index`: クリックする要素のインデックス（必須、scan-elementsで取得したインデックス）
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `index`, `browser` を解析
2. `mcp__native-browser-control__click_element` を呼び出す
   - `index`: 整数値
   - `browser`: 解析した値（省略時は "chrome"）
3. クリック操作の成功を確認
4. 注意: 事前に `/browser:scan-elements` でスキャンしておく必要があります
5. ページ更新後はインデックスが無効になるため、再スキャンが必要です
