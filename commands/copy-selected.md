---
description: 選択中のテキストをコピー
argument-hint: [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__copy_selected
---

現在選択中のテキストをクリップボードにコピーして、その内容を返します（Chrome/Edge対応、Ctrl+C）。

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `browser` を解析
2. `mcp__native-browser-control__copy_selected` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
3. コピーされたテキスト内容を返却
4. 注意: 事前にテキストを選択しておく必要があります
