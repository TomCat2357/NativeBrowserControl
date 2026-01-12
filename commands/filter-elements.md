---
description: スキャン済み要素をフィルタリング
argument-hint: [browser=chrome|edge] [filters...] [output=simple|summary|full]
allowed-tools: mcp__native-browser-control__filter_elements
---

既にスキャンした要素をフィルタリングして表示します。

**引数**
- `browser`: 対象ブラウザ（chrome または edge、省略時: chrome）
- `control_types`: フィルターするコントロールタイプ（複数指定可・OR条件、例: Button, Edit, Link）
- `class_names`: friendly_class_name()で一致させるクラス名（複数指定可・OR条件）
- `name_regex`: 要素名にマッチする正規表現
- `value_regex`: 要素の値（get_value()）にマッチする正規表現
- `only_visible`: 可視要素のみ（true/false、省略時: false）
- `require_enabled`: 有効な要素のみ（true/false、省略時: false）
- `min_width`: 最小幅（ピクセル）
- `min_height`: 最小高さ（ピクセル）
- `only_focusable`: キーボードフォーカス可能な要素のみ（true/false、省略時: false）
- `index_ranges`: 対象インデックス範囲（Pythonスライス形式、例: '1:4,10:-1'）
- `automation_id`: automation_idで一致させる値（単体または配列）
- `automation_id_regex`: automation_idにマッチする正規表現
- `omit_no_name`: 名前なし要素を除外（true/false、省略時: true）
- `min_separator_count`: 先頭のSeparatorをスキップする閾値（デフォルト: 0で無効）
- `update_mode`: 要素更新モード（overwrite=上書き/add=追加/preserve=変更なし、省略時: overwrite）
- `output`: 出力モード（simple=件数, summary=集計, full=一覧、省略時: simple）

**手順**
1. 引数から各フィルターパラメータと出力モードを解析
2. `mcp__native-browser-control__filter_elements` を呼び出す
   - `browser`: 解析した値（省略時は "chrome"）
   - フィルターパラメータ: 指定された値
   - `output`: 解析した値（省略時は "simple"）
3. フィルタリング結果を指定された出力モードで表示
