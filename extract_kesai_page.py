"""
決裁確認ページから情報を抽出して再現するスクリプト
"""
import sys
import json
from typing import Dict, List, Any, Optional
from native_browser_driver import NativeEdgeDriver


def extract_static_fields(driver) -> Dict[str, str]:
    """Static要素から基本フィールドを抽出"""
    result = {}

    if not driver.current_elements:
        return result

    # Static要素のリストを作成
    static_texts = []
    for idx in sorted(driver.current_elements.keys()):
        elem_wrapper = driver.current_elements[idx]
        try:
            name = elem_wrapper.window_text()
            static_texts.append(name)
        except Exception:
            static_texts.append("")

    # ラベル-値ペアを抽出
    field_labels = [
        "所属", "担当者", "役職", "供覧日", "文書年",
        "供覧区分", "文書管理番号", "件名", "供覧文"
    ]

    for i, text in enumerate(static_texts):
        if text in field_labels and i + 1 < len(static_texts):
            value = static_texts[i + 1]
            # 次の値がラベルでない場合のみ採用
            # また、ボタンのような不要なテキストを除外
            if value not in field_labels and not value.startswith("・") and value != "関連文書":
                result[text] = value

    return result


def extract_attachment_category(driver) -> str:
    """現在表示されている添付文書の分類名を取得"""
    try:
        # Text要素をスキャン
        driver.scan_page_elements(
            control_type="Text",
            max_elements=200,
            foreground=True,
            settle_ms=100,
        )

        # 「添付文書情報」を含む要素を探す
        driver.filter_current_elements(
            name_regex="添付文書情報",
            output="simple",
            overwrite=True,
        )

        if driver.current_elements:
            # 最初の要素のテキストを取得
            idx = min(driver.current_elements.keys())
            elem_wrapper = driver.current_elements[idx]
            return elem_wrapper.window_text()
    except Exception:
        pass

    return "添付文書情報"


def find_attachment_switch_button(driver) -> Optional[int]:
    """添付表示切り替えボタンのインデックスを見つける"""
    try:
        # Button要素をスキャン
        driver.scan_page_elements(
            control_type="Button",
            max_elements=100,
            foreground=True,
            settle_ms=100,
        )

        # 「添付表示」を含むボタンを探す
        driver.filter_current_elements(
            name_regex="添付表示",
            output="simple",
            overwrite=True,
        )

        if driver.current_elements:
            # 最初のボタンのインデックスを返す
            return min(driver.current_elements.keys())
    except Exception:
        pass

    return None


def extract_attachments_from_table(driver) -> List[Dict[str, str]]:
    """
    テーブル形式の添付ファイル情報を抽出
    browser_table_extraction.mdの手法を使用
    """
    attachments = []

    if not driver.current_elements:
        return attachments

    # インデックス付き要素リストを作成
    elements_dict = {}
    for idx in sorted(driver.current_elements.keys()):
        elem_wrapper = driver.current_elements[idx]
        try:
            name = elem_wrapper.window_text()
            elements_dict[idx] = name
        except Exception:
            elements_dict[idx] = ""

    # 「添付文書名称」と「表示」ボタンのインデックスを探す
    header_idx = None
    button_idx = None

    for idx, text in elements_dict.items():
        if text == "添付文書名称":
            header_idx = idx
        elif text == "表示" and header_idx is not None:
            button_idx = idx
            break

    if header_idx is None or button_idx is None:
        # 見つからない場合は空リストを返す
        return attachments

    # 抽出範囲: header_idx から button_idx-1 まで
    start_idx = header_idx
    end_idx = button_idx - 1

    # header_idx と header_idx+1 はヘッダー行（添付文書名称、種類）
    # その後、データ行が続く
    # パターン: 番号（複数）→ ファイル名 → 種類 → ファイル名 → 種類 ...

    # データ開始位置を探す（ヘッダーの次から）
    data_start = header_idx + 2

    # データ部分の要素を取得
    data_elements = []
    for idx in range(data_start, end_idx + 1):
        if idx in elements_dict:
            data_elements.append((idx, elements_dict[idx]))

    # データ解析: 番号列をスキップして、ファイル名と種類のペアを抽出
    i = 0
    row_num = 1

    # まず番号列をスキップ（連続する数字）
    while i < len(data_elements) and data_elements[i][1].strip().isdigit():
        i += 1

    # ファイル名と種類のペアを抽出
    while i < len(data_elements):
        idx, text = data_elements[i]

        # ファイル名（長いテキスト）
        if len(text) > 3 and not text in ["pdf", "xlsx", "docx", "txt", "xls"]:
            file_name = text
            file_type = ""

            # 次の要素が種類かチェック
            if i + 1 < len(data_elements):
                next_text = data_elements[i + 1][1]
                if next_text in ["pdf", "xlsx", "docx", "txt", "xls"]:
                    file_type = next_text
                    i += 1  # 種類分進める

            attachments.append({
                "番号": row_num,
                "ファイル名": file_name,
                "種類": file_type
            })
            row_num += 1

        i += 1

    return attachments


def extract_edit_fields(driver) -> Dict[str, str]:
    """Edit要素から長文フィールドを抽出"""
    result = {}

    if not driver.current_elements:
        return result

    # Edit要素のマッピング
    edit_field_mapping = {
        "txbKianriyu": "説明",
        "txbBiko": "備考",
        "txbKomento": "コメント",
        "tfsKenMei": "件名",
        "tfcUkagaibun": "供覧文",
        "tfnBunsyoKanriBango": "文書管理番号",
        "choKessaiKubunMei": "供覧区分",
        "tfdKianBi": "供覧日"
    }

    for idx in sorted(driver.current_elements.keys()):
        elem_wrapper = driver.current_elements[idx]
        try:
            elem = elem_wrapper.element_info.element
            automation_id = getattr(elem, 'CurrentAutomationId', '')

            # マッピングに一致するフィールドを探す
            for pattern, field_name in edit_field_mapping.items():
                if pattern in automation_id:
                    try:
                        # Value属性を取得（PropertyId 30045 = ValueValueProperty）
                        value = elem.GetCurrentPropertyValue(30045)
                        if value and str(value).strip():
                            result[field_name] = str(value)
                    except Exception:
                        pass
        except Exception:
            continue

    return result


def print_kesai_info(static_fields: Dict[str, str],
                     edit_fields: Dict[str, str],
                     all_attachments: Dict[str, List[Dict[str, str]]]) -> None:
    """抽出した情報を整形して表示"""
    print("\n" + "=" * 80)
    print("決裁確認ページ情報")
    print("=" * 80)

    # 基本情報
    print("\n【基本情報】")
    basic_fields = ["所属", "担当者", "役職"]
    for field in basic_fields:
        value = static_fields.get(field) or edit_fields.get(field) or ""
        print(f"  {field}: {value}")

    # 文書情報
    print("\n【文書情報】")
    doc_fields = ["供覧日", "文書年", "供覧区分", "文書管理番号"]
    for field in doc_fields:
        value = static_fields.get(field) or edit_fields.get(field) or ""
        print(f"  {field}: {value}")

    # 件名・供覧文
    print("\n【件名・供覧文】")
    content_fields = ["件名", "供覧文"]
    for field in content_fields:
        value = static_fields.get(field) or edit_fields.get(field) or ""
        if value:
            print(f"  {field}: {value}")

    # 説明
    if "説明" in edit_fields:
        print("\n【説明】")
        print(f"  {edit_fields['説明']}")

    # 備考
    if "備考" in edit_fields:
        print("\n【備考】")
        print(f"  {edit_fields['備考']}")

    # コメント
    if "コメント" in edit_fields:
        print("\n【コメント】")
        print(f"  {edit_fields['コメント']}")

    # 添付ファイル（分類ごとに表示）
    if all_attachments:
        for category, attachments in all_attachments.items():
            if attachments:
                print(f"\n【{category}】")
                for att in attachments:
                    num = att.get("番号", "")
                    name = att.get("ファイル名", "")
                    ftype = att.get("種類", "")
                    print(f"  {num}. {name} ({ftype})")

    print("\n" + "=" * 80)


def save_to_json(data: Dict[str, Any], filename: str = "kesai_data.json") -> None:
    """抽出した情報をJSONファイルに保存"""
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"\nデータを {filename} に保存しました。")


def main() -> int:
    print("決裁確認ページ情報抽出スクリプト")
    print("-" * 80)

    # Edgeに接続
    try:
        driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
        print("Edgeに接続しました。")
    except Exception as exc:
        print(f"ERROR: Edgeに接続できません: {exc}")
        return 1

    # 1. Static要素をスキャン
    print("\n1. Static要素をスキャン中...")
    try:
        result = driver.scan_page_elements(
            control_type="Text",
            max_elements=200,
            foreground=True,
            settle_ms=100,
        )
        print(f"   {result}")

        # Static要素から情報抽出
        static_fields = extract_static_fields(driver)

    except Exception as exc:
        print(f"ERROR: Staticスキャン失敗: {exc}")
        static_fields = {}

    # 1.5. 添付ファイル情報を抽出（複数分類対応）
    print("\n1.5. 添付ファイル情報を抽出中...")
    all_attachments = {}

    for attempt in range(2):
        try:
            # 現在の添付文書分類を取得
            category = extract_attachment_category(driver)
            print(f"   分類: {category}")

            # 全要素をスキャン
            result = driver.scan_page_elements(
                max_elements=500,
                foreground=True,
                settle_ms=100,
            )
            print(f"   スキャン: {result}")

            # class_namesでStatic/Buttonに絞り込む
            result = driver.filter_current_elements(
                class_names=["Button", "Static"],
                output="summary",
                overwrite=True,
            )
            print(f"   フィルタ後: {result}")

            # 添付ファイル情報を抽出
            attachments = extract_attachments_from_table(driver)
            all_attachments[category] = attachments
            print(f"   抽出: {len(attachments)}件")

            # 2回目のループ前に切り替えボタンをクリック
            if attempt == 0:
                button_idx = find_attachment_switch_button(driver)
                if button_idx is not None:
                    print(f"\n   切り替えボタンをクリック...")
                    driver.click_by_index(button_idx)
                    import time
                    time.sleep(1)  # 画面更新待ち
                else:
                    print("   切り替えボタンが見つかりません。")
                    break

        except Exception as exc:
            print(f"ERROR: 添付ファイルスキャン失敗 (attempt {attempt+1}): {exc}")
            if attempt == 0:
                all_attachments = {}

    # 2. Edit要素をスキャン
    print("\n2. Edit要素をスキャン中...")
    try:
        result = driver.scan_page_elements(
            control_type="Edit",
            max_elements=50,
            foreground=True,
            settle_ms=100,
        )
        print(f"   {result}")

        # Edit要素から情報抽出
        edit_fields = extract_edit_fields(driver)

    except Exception as exc:
        print(f"ERROR: Editスキャン失敗: {exc}")
        edit_fields = {}

    # 3. 情報を表示
    print_kesai_info(static_fields, edit_fields, all_attachments)

    # 4. JSONに保存
    all_data = {
        "基本情報": {
            "所属": static_fields.get("所属") or edit_fields.get("所属") or "",
            "担当者": static_fields.get("担当者") or edit_fields.get("担当者") or "",
            "役職": static_fields.get("役職") or edit_fields.get("役職") or "",
        },
        "文書情報": {
            "供覧日": static_fields.get("供覧日") or edit_fields.get("供覧日") or "",
            "文書年": static_fields.get("文書年") or edit_fields.get("文書年") or "",
            "供覧区分": static_fields.get("供覧区分") or edit_fields.get("供覧区分") or "",
            "文書管理番号": static_fields.get("文書管理番号") or edit_fields.get("文書管理番号") or "",
        },
        "内容": {
            "件名": static_fields.get("件名") or edit_fields.get("件名") or "",
            "供覧文": static_fields.get("供覧文") or edit_fields.get("供覧文") or "",
            "説明": edit_fields.get("説明", ""),
            "備考": edit_fields.get("備考", ""),
            "コメント": edit_fields.get("コメント", ""),
        },
        "添付ファイル": all_attachments
    }

    save_to_json(all_data)

    print("\n抽出完了")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
