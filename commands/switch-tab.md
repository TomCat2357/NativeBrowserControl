---
description: タブを切り替え
argument-hint: <direction> [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__switch_tab
---

タブを切り替えます（Chrome/Edge対応、Ctrl+Tab / Ctrl+Shift+Tab）

**引数**
- `direction`: 切り替え方向（next=次のタブ、previous=前のタブ、必須）
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `direction`, `browser` を解析
2. `mcp__native-browser-control__switch_tab` を呼び出す
   - `direction`: 指定された方向（next または previous）
   - `browser`: 解析した値（省略時は "chrome"）
3. タブ切り替えの成功を確認
4. 次のアクションとして `/browser:screenshot` で切り替え結果を確認することを案内
