---
description: ページをスクロール
argument-hint: <direction> browser=chrome|edge [amount=500]
allowed-tools: mcp__native-browser-control__scroll
---

ページをスクロールします（Chrome/Edge対応）

**引数**
- `direction`: スクロール方向（up, down, page_up, page_down, top, bottom、必須）
- `browser`: 対象ブラウザ（chrome または edge、必須）
- `amount`: スクロール量（ピクセル、upまたはdownの場合のみ有効、省略時: 500）

**手順**
1. 引数から `direction`, `browser`, `amount` を解析
2. `mcp__native-browser-control__scroll` を呼び出す
   - `direction`: 指定された方向
   - `browser`: 解析した値（必須。省略は不可）
   - `amount`: 整数値（省略時は 500、upまたはdownの場合のみ）
3. スクロール操作の成功を確認
4. 次のアクションとして `/browser:screenshot` でスクロール結果を確認することを案内
