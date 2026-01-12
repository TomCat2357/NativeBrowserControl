---
description: 要素のテキストを設定
argument-hint: <index> <text> [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__set_element_text
---

スキャンした要素（Editコントロールなど）にテキストを設定します。

**引数**
- `index`: テキストを設定する要素のインデックス（必須、scan-elementsで取得したインデックス）
- `text`: 設定するテキスト（必須）
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `index`, `text`, `browser` を解析
2. `mcp__native-browser-control__set_element_text` を呼び出す
   - `index`: 整数値
   - `text`: 指定されたテキスト
   - `browser`: 解析した値（省略時は "chrome"）
3. テキスト設定の成功を確認
4. 注意: 事前に `/browser:scan-elements` でスキャンしておく必要があります
5. Editコントロールなど、テキスト設定可能な要素にのみ有効です
