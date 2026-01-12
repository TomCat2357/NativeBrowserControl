---
description: ズーム操作
argument-hint: <action> [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__zoom
---

ブラウザのズーム操作を実行します（Chrome/Edge対応、Ctrl++, Ctrl+-, Ctrl+0）

**引数**
- `action`: ズーム操作（in=拡大、out=縮小、reset=リセット、必須）
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `action`, `browser` を解析
2. `mcp__native-browser-control__zoom` を呼び出す
   - `action`: 指定された操作（in, out, reset）
   - `browser`: 解析した値（省略時は "chrome"）
3. ズーム操作の成功を確認
4. 次のアクションとして `/browser:screenshot` でズーム結果を確認することを案内
