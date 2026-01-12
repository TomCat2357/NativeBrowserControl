---
description: ページ内検索
argument-hint: <text> [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__find_text
---

ページ内検索を開いてテキストを検索します（Chrome/Edge対応、Ctrl+F）

**引数**
- `text`: 検索するテキスト（必須）
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `text`, `browser` を解析
2. `mcp__native-browser-control__find_text` を呼び出す
   - `text`: 検索するテキスト
   - `browser`: 解析した値（省略時は "chrome"）
3. ページ内検索ダイアログが開き、テキストがハイライトされる
4. 次のアクションとして `/browser:screenshot` で検索結果を確認することを案内
