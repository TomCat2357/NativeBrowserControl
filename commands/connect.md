---
description: 指定ブラウザに接続（未起動なら起動）
argument-hint: [browser=chrome|edge] [window_index=0]
allowed-tools: mcp__native-browser-control__connect_browser
---

指定ブラウザに接続します。window_indexで接続先を選択（省略時は0番目、-1で最後）。ブラウザが未起動の場合は起動します。

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）
- `window_index`: 接続するウィンドウのインデックス（0=最初、-1=最後、省略時は0）

**手順**
1. 引数から `browser`, `window_index` を解析
2. `mcp__native-browser-control__connect_browser` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
   - `window_index`: 整数値（省略時は 0）
3. 接続成功を確認し、PIDとHWNDを表示
4. 次のアクションとして `/browser:navigate <url>` を案内
