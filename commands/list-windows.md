---
description: 起動中のブラウザウィンドウ一覧を取得
argument-hint: [browser=chrome|edge] [require_visible=true|false] [exclude_minimized=true|false]
allowed-tools: mcp__native-browser-control__list_browser_windows
---

起動中のブラウザウィンドウ一覧を取得します（Chrome/Edge対応、ドライバー接続先の選択用）。インデックス番号付きで表示されます。

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）
- `require_visible`: 可視ウィンドウのみを対象にするか（true/false、省略時: false）
- `exclude_minimized`: 最小化されたウィンドウを除外するか（true/false、省略時: false）

**手順**
1. 引数から `browser`, `require_visible`, `exclude_minimized` を解析
2. `mcp__native-browser-control__list_browser_windows` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
   - `require_visible`: ブール値（省略時は false）
   - `exclude_minimized`: ブール値（省略時は false）
3. ウィンドウ一覧をインデックス付きで表示
4. 次のアクションとして `/browser:connect <window_index>` を案内
