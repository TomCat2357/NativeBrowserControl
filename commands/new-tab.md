---
description: 新しいタブを開く
argument-hint: [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__new_tab
---

新しいタブを開きます（Chrome/Edge対応、Ctrl+T）

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `browser` を解析
2. `mcp__native-browser-control__new_tab` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
3. 新しいタブが開いたことを確認
4. 次のアクションとして `/browser:navigate <url>` を案内
