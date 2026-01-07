---
description: ページ上の要素をスキャン
argument-hint: [browser=chrome|edge] [filters...]
allowed-tools: mcp__native-browser-control__scan_elements
---

ページ上の要素をスキャンしてリストアップします。

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）
- `control_type`: フィルターするコントロールタイプ（例: Button, Edit, Link）
- `control_types`: 追加フィルタ用コントロールタイプ（複数指定可・OR、例: ["Button", "Link"]）
- `max_elements`: 取得する最大要素数（省略時: 500）
- `name_contains`: 要素名に含まれるべき文字列（部分一致）
- `name_regex`: 要素名にマッチする正規表現
- `class_name`: friendly_class_name()で一致させるクラス名
- `only_visible`: 可視要素のみ取得（true/false、省略時: false）
- `require_enabled`: 有効な要素のみ取得（true/false、省略時: false）
- `min_width`: 最小幅（ピクセル）
- `min_height`: 最小高さ（ピクセル）
- `only_focusable`: キーボードフォーカス可能な要素のみ（true/false、省略時: false）
- `index_ranges`: 対象インデックス範囲（例: '1:4,10:-1'。start含む/end除外、負数OK）
- `automation_id`: automation_idで一致させる値
- `min_separator_count`: "Separator"が検知されるまで結果出力を遅らせる回数閾値（省略時: 0）

**手順**
1. 引数から各フィルターパラメータを解析
2. `mcp__native-browser-control__scan_elements` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
   - その他のフィルターパラメータ: 指定された値
3. スキャン結果をインデックス付きで表示
4. 次のアクションとして `/browser:click-element <index>` または `/browser:set-element-text <index> <text>` を案内
5. 注意: 要素インデックスはページ更新で無効化されるため、操作前に再スキャンが必要
