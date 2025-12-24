# 決裁システムファイルダウンロード手順

## 概要

札幌市文書管理システムの決裁確認画面から添付ファイルを一括ダウンロードする手順です。

## 前提条件

- Microsoft Edgeで決裁確認ページが開いていること
- Native Browser Control MCPサーバーが起動していること

## 手順

### 2. 全選択チェックボックスをクリック

#### 2-1. CheckBox要素をスキャン

```
scan_elements(browser="edge", control_type="CheckBox")
```

#### 2-2. 要素一覧を確認

```
list_elements(browser="edge")
```

結果例：
```
[0] <CheckBox> [ID:all_checkbox_IP123352IC~tplTenpu2]
[1] <CheckBox> [ID:chk_IP123352IC~tplTenpu2_06@0]
...
```

#### 2-3. all_checkboxをクリック

```
click_element(browser="edge", index=0)
```

### 3. 「表示」ボタンをクリック

#### 3-1. Button要素をスキャン

```
scan_elements(browser="edge", control_type="Button")
```

#### 3-2. 「表示」を含むボタンでフィルタリング

```
filter_elements(browser="edge", name_contains="表示", output="full")
```

結果例：
```
[0] <Button> ダウンロードの表示
[1] <Button> 起案／供覧理由を拡大表示
...
[4] <Button> 表示 [ID:IP123352IC~tplTenpu2_04]
```

#### 3-3. 「表示」ボタンをクリック

```
click_element(browser="edge", index=4)
```

**注意**: インデックス番号はフィルタリング結果によって変わる可能性があります。「表示」というシンプルな名前のボタンを選択してください。

### 4. 「保存」ボタンをクリック

#### 4-1. SplitButton要素をスキャン

```
scan_elements(browser="edge", control_type="SplitButton")
```

#### 4-2. 「保存」を含むボタンでフィルタリング

```
filter_elements(browser="edge", name_contains="保存", output="full")
```

結果例：
```
[0] <SplitButton> 保存
```

#### 4-3. 「保存」ボタンをクリック

```
click_element(browser="edge", index=0)
```

### 5. ダウンロードされたZIPファイルの展開（オプション）

#### 5-1. 最新のZIPファイルを特定して展開

Downloadsフォルダで以下のコマンドを実行：

```bash
cd /c/Users/sa11882/Downloads
# 最新のZIPファイルを取得
latest_zip=$(ls -1 *.zip 2>/dev/null | sort | tail -1)
# そのファイル以外を削除
find . -maxdepth 1 -type f ! -name "$latest_zip" -delete
# PowerShellで文字化けせずに展開
powershell.exe -Command "Expand-Archive -Path '$latest_zip' -DestinationPath '.' -Force"
# ZIPファイルを削除
rm "$latest_zip"
```

**重要**: PowerShellの`Expand-Archive`を使用することで、日本語ファイル名の文字化けを防げます。

## 最小限のステップ（まとめ）

```
1. connect_browser(browser="edge")
2. scan_elements(browser="edge", control_type="CheckBox")
3. list_elements(browser="edge")
4. click_element(browser="edge", index=0)  # all_checkbox
5. scan_elements(browser="edge", control_type="Button")
6. filter_elements(browser="edge", name_contains="表示", output="full")
7. click_element(browser="edge", index=4)  # 「表示」ボタン
8. scan_elements(browser="edge", control_type="SplitButton")
9. filter_elements(browser="edge", name_contains="保存", output="full")
10. click_element(browser="edge", index=0)  # 「保存」ボタン
```

## トラブルシューティング

### インデックス番号が合わない場合

- 必ず`list_elements`または`filter_elements(output="full")`で最新の要素一覧を確認してください
- フィルタリング後のインデックスは元のスキャン結果とは異なります

### 文字化けが発生した場合

- `unzip`コマンドではなく、PowerShellの`Expand-Archive`を使用してください
- Git Bashの`unzip`はShift-JISエンコーディングに対応していないため、日本語ファイル名が文字化けします

## 備考

- この手順は札幌市文書管理システム研修・検証環境AP（V3.1L61）で動作確認済みです
- 画面構成が変更された場合、インデックス番号や要素名が変わる可能性があります
- MCPサーバーのツール名は`native-browser-control`プレフィックスなしで記載していますが、実際の呼び出し時には`mcp__native-browser-control__<tool_name>`の形式で使用されます
