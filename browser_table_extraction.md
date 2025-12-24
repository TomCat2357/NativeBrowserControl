# ブラウザ要素テーブル抽出スキル

## 概要
Edgeブラウザから特定の要素をスキャンし、表形式のデータを抽出してJSON化する一連の操作をまとめたスキルです。

## 処理フロー

### 2. Static/Button要素のスキャン
ページ内の`Static`および`Button`クラスの要素をスキャンします。

```python
# 複数のクラス名を指定してスキャン
scan_elements(browser="edge", class_names=["Static", "Button"])
```

### 3. 要素リストの展開とインデックス取得
スキャンした要素を展開し、特定の要素のインデックス番号を取得します。

```python
# 要素リストを展開
list_elements(browser="edge")

# 出力例:
# [56] <Static> 添付文書名称
# [57] <Static> 種類
# [79] <Button> 表示 [ID:IP123352IC~tplTenpu2_04]
```

**キー要素のインデックス特定**:
- `添付文書名称` (Static): インデックス 56
- `表示` (Button): インデックス 79

### 4. 範囲指定による要素抽出
特定インデックスから1を引いた範囲の要素を抽出します。

**抽出範囲**: `[56-1]` ～ `[79-1]` = `[55]` ～ `[78]`

```
[55] <Button> ﾋﾞｭｰｱ
[56] <Static> 添付文書名称
[57] <Static> 種類
[58-64] <Static> 1～7 (番号列)
[65] <Static> 01_保有個人情報の取扱いに係る監査に
[66] <Static> pdf
[67] <Static> 02_【別紙１】令和７年度安全管理要綱
[68] <Static> xlsx
...
[78] <Static> pdf
```

### 5. テーブル構造への整形
抽出した要素を表形式に整形します。

| No | 添付文書名称 | 種類 |
|----|-------------|------|
| 1  | 01_保有個人情報の取扱いに係る監査に | pdf |
| 2  | 02_【別紙１】令和７年度安全管理要綱 | xlsx |
| 3  | 03_【別紙２】札幌市保有個人情報及び | pdf |
| 4  | 04_【別紙３】法令に基づく照会に対す | pdf |
| 5  | 05_【別紙４】個人情報取扱事務委託等 | pdf |
| 6  | 06_【別紙５】個人情報保護法 | pdf |
| 7  | 07_【別紙６】Q＆A | pdf |

### 6. JSON構造化
表データをJSON形式に変換します。

```json
{
  "table": {
    "title": "収受添付文書情報",
    "headers": ["No", "添付文書名称", "種類"],
    "rows": [
      {
        "no": 1,
        "document_name": "01_保有個人情報の取扱いに係る監査に",
        "type": "pdf"
      },
      {
        "no": 2,
        "document_name": "02_【別紙１】令和７年度安全管理要綱",
        "type": "xlsx"
      },
      {
        "no": 3,
        "document_name": "03_【別紙２】札幌市保有個人情報及び",
        "type": "pdf"
      },
      {
        "no": 4,
        "document_name": "04_【別紙３】法令に基づく照会に対す",
        "type": "pdf"
      },
      {
        "no": 5,
        "document_name": "05_【別紙４】個人情報取扱事務委託等",
        "type": "pdf"
      },
      {
        "no": 6,
        "document_name": "06_【別紙５】個人情報保護法",
        "type": "pdf"
      },
      {
        "no": 7,
        "document_name": "07_【別紙６】Q＆A",
        "type": "pdf"
      }
    ]
  },
  "metadata": {
    "start_index": 55,
    "end_index": 78,
    "header_index": 56,
    "button_index": 79,
    "total_rows": 7
  }
}
```

## データ抽出ロジック

### パターン認識
1. **ヘッダー行**: インデックス56, 57が列名を示す
2. **番号列**: インデックス58～64が行番号（1～7）
3. **データ列**: 奇数インデックス（65,67,69...）が文書名、偶数インデックス（66,68,70...）がファイル種類

### 抽出アルゴリム
```python
def extract_table_data(elements, start_idx=55, end_idx=78):
    """
    要素リストから表データを抽出

    Args:
        elements: スキャンされた要素リスト
        start_idx: 開始インデックス（デフォルト: 55）
        end_idx: 終了インデックス（デフォルト: 78）

    Returns:
        dict: JSON形式の表データ
    """
    # ヘッダー取得
    headers = ["No", elements[56], elements[57]]

    # データ行を抽出（65から2つずつペアで処理）
    rows = []
    row_num = 1
    for i in range(65, end_idx, 2):
        rows.append({
            "no": row_num,
            "document_name": elements[i],
            "type": elements[i+1]
        })
        row_num += 1

    return {
        "table": {
            "title": "収受添付文書情報",
            "headers": headers,
            "rows": rows
        },
        "metadata": {
            "start_index": start_idx,
            "end_index": end_idx,
            "total_rows": len(rows)
        }
    }
```

## 応用例

### 他のテーブル構造への適用
このスキルは、以下のような構造を持つ任意のテーブルに適用可能です：

1. ヘッダー行が明確に識別できる（特定のStatic要素）
2. データが規則的なパターンで配置されている
3. 開始点と終了点が特定可能なボタンやラベルで示されている

### カスタマイズポイント
- **検索キーワード**: ブラウザタイトルの検索文字列を変更
- **クラス名**: `Static`, `Button` 以外のクラスも指定可能
- **範囲調整**: 開始・終了インデックスを動的に調整
- **データ構造**: JSON出力形式をニーズに応じてカスタマイズ

## 注意事項
- ブラウザウィンドウが可視状態である必要があります
- 要素のインデックスはページ構造により変動する可能性があります
- 複数の該当ウィンドウがある場合は、適切な`window_index`を指定してください
