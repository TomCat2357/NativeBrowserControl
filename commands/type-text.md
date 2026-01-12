---
description: テキストを入力
argument-hint: <text> [browser=chrome|edge] [method=paste|type]
allowed-tools: mcp__native-browser-control__type_text
---

フォーカス中の要素にテキストを入力します（Chrome/Edge対応）

**引数**
- `text`: 入力するテキスト（必須）
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）
- `method`: 入力方法（paste=クリップボード経由、type=一文字ずつ、省略時: paste）

**手順**
1. 引数から `text`, `browser`, `method` を解析
2. `mcp__native-browser-control__type_text` を呼び出す
   - `text`: 指定されたテキスト
   - `browser`: 解析した値（省略時は "chrome"）
   - `method`: 解析した値（省略時は "paste"）
3. テキスト入力の成功を確認
4. 注意: method=pasteの場合、クリップボードの内容が上書きされます
