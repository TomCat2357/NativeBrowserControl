---
description: 指定秒数待機
argument-hint: <seconds> [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__wait
---

指定秒数待機します（ページロード待ちなどに使用）。

**引数**
- `seconds`: 待機する秒数（必須）
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `seconds`, `browser` を解析
2. `mcp__native-browser-control__wait` を呼び出す
   - `seconds`: 数値（整数または小数）
   - `browser`: 解析した値（省略時は "chrome"）
3. 指定秒数待機
4. 使用例: ページロード後、ダイアログ表示後、フォーム送信後など
