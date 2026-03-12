---
description: 指定URLに移動
argument-hint: <url> browser=chrome|edge
allowed-tools: mcp__native-browser-control__navigate
---

指定したURLに移動します（Chrome/Edge対応）

**引数**
- `url`: 移動先のURL（必須）
- `browser`: 対象ブラウザ（chrome または edge、必須）

**手順**
1. 引数から `url`, `browser` を解析
2. `mcp__native-browser-control__navigate` を呼び出す
   - `url`: 指定されたURL
   - `browser`: 解析した値（必須。省略は不可）
3. ナビゲーション成功を確認
4. 次のアクションとして `/browser:screenshot` または `/browser:get-page-text` を案内
