---
description: 現在のタブを閉じる
argument-hint: browser=chrome|edge
allowed-tools: mcp__native-browser-control__close_tab
---

現在のタブを閉じます（Chrome/Edge対応、Ctrl+W）

**引数**
- `browser`: 対象ブラウザ（chrome または edge、必須）

**手順**
1. 引数から `browser` を解析
2. `mcp__native-browser-control__close_tab` を呼び出す
   - `browser`: 解析した値（必須。省略は不可）
3. タブが閉じられたことを確認
4. 注意: 最後のタブを閉じるとブラウザが終了する場合があります
