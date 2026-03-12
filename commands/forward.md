---
description: 次のページに進む
argument-hint: browser=chrome|edge
allowed-tools: mcp__native-browser-control__forward
---

ブラウザの進むボタンをクリックして、次のページに進みます（Chrome/Edge対応）

**引数**
- `browser`: 対象ブラウザ（chrome または edge、必須）

**手順**
1. 引数から `browser` を解析
2. `mcp__native-browser-control__forward` を呼び出す
   - `browser`: 解析した値（必須。省略は不可）
3. 進む操作の成功を確認
4. 必要に応じて `/browser:wait 2` でページロード待機を案内
