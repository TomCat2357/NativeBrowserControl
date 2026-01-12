---
description: ページをリロード
argument-hint: [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__refresh
---

現在のページをリロードします（Chrome/Edge対応、F5キー送信）

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `browser` を解析
2. `mcp__native-browser-control__refresh` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
3. リロード操作の成功を確認
4. 必要に応じて `/browser:wait 3` でページロード待機を案内
