---
description: 画面全体を撮影
argument-hint: [browser=chrome|edge] [monitor=0] [format=PNG|JPEG]
allowed-tools: mcp__native-browser-control__full_screenshot
---

画面全体のスクリーンショットを撮影します（Chrome/Edge対応、ブラウザ以外も含む）

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）
- `monitor`: モニター番号（0=全モニター、1=プライマリ、2=セカンダリ...、省略時: 1）
- `format`: 画像フォーマット（PNG または JPEG、省略時: PNG）

**手順**
1. 引数から `browser`, `monitor`, `format` を解析
2. `mcp__native-browser-control__full_screenshot` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
   - `monitor`: 整数値（省略時は 1）
   - `format`: 解析した値（省略時は "PNG"）
3. スクリーンショット画像をbase64形式で返却
4. Claude Codeは自動的に画像として表示
