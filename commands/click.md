---
description: 座標でクリック
argument-hint: <x> <y> [browser=chrome|edge]
allowed-tools: mcp__native-browser-control__click
---

指定座標をクリックします（Chrome/Edge対応）

**引数**
- `x`: X座標（ブラウザウィンドウ内の相対座標、必須）
- `y`: Y座標（ブラウザウィンドウ内の相対座標、必須）
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）

**手順**
1. 引数から `x`, `y`, `browser` を解析
2. `mcp__native-browser-control__click` を呼び出す
   - `x`: 整数値
   - `y`: 整数値
   - `browser`: 解析した値（省略時は "chrome"）
3. クリック操作の成功を確認
4. 注意: DPI設定や画面スケーリングによって座標がずれる可能性があります
5. より確実な操作には `/browser:scan-elements` と `/browser:click-element` の使用を推奨
