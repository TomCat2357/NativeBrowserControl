---
description: スキャン済み要素の統計情報を表示
argument-hint: browser=chrome|edge
allowed-tools: mcp__native-browser-control__elements_summary
---

既にスキャンした要素の統計情報（コントロールタイプ別カウントなど）を表示します。

**引数**
- `browser`: 対象ブラウザ（chrome または edge、必須）

**手順**
1. 引数から `browser` を解析
2. `mcp__native-browser-control__elements_summary` を呼び出す
   - `browser`: 解析した値（必須。省略は不可）
3. 要素の統計情報（コントロールタイプ別カウント、可視/有効要素数など）を表示
4. この情報を元に適切なフィルター条件を決定できます
