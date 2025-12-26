"""
CheckBoxの周辺要素を調査して「収受添付文書」情報を探すスクリプト
"""
from native_browser_driver import NativeEdgeDriver
import time

def investigate_surrounding_elements():
    """CheckBoxの周辺要素を調査"""
    print("=" * 80)
    print("CheckBox周辺要素調査")
    print("=" * 80)

    # ブラウザに接続
    print("\n[1] ブラウザに接続中...")
    driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
    print("    接続完了")

    # CheckBoxの数を確認し、必要に応じて「添付表示」ボタンをクリック
    print("\n[2] CheckBoxの数を確認...")
    driver.scan_page_elements(
        control_type="CheckBox",
        max_elements=50,
        foreground=True,
        settle_ms=100,
    )

    checkbox_count = len(driver.current_elements)
    print(f"    現在のCheckBox数: {checkbox_count}個")

    # CheckBoxが2個以下なら「添付表示」をクリックして切り替え
    if checkbox_count <= 2:
        print("\n[3] 「添付表示」ボタンをクリックして画面を切り替え...")
        try:
            driver.scan_page_elements(
                control_type="Button",
                max_elements=100,
                foreground=True,
                settle_ms=100,
            )

            driver.filter_current_elements(
                name_regex="添付表示",
                output="simple",
                overwrite=True,
            )

            if driver.current_elements:
                switch_button_idx = min(driver.current_elements.keys())
                driver.click_by_index(switch_button_idx)
                print(f"    「添付表示」ボタンをクリックしました (index={switch_button_idx})")
                time.sleep(1.5)
            else:
                print("    「添付表示」ボタンが見つかりませんでした")
        except Exception as exc:
            print(f"    エラー: {exc}")
    else:
        print("\n[3] CheckBoxが複数あるため、切り替え不要")

    # 全要素をスキャン
    print("\n[4] 全要素をスキャン中...")
    driver.scan_page_elements(
        max_elements=1000,
        foreground=True,
        settle_ms=100,
    )
    print(f"    {len(driver.current_elements)}個の要素が見つかりました")

    # CheckBoxのインデックスを記録
    print("\n[5] CheckBoxを特定...")
    checkbox_indices = []
    for idx, elem_wrapper in driver.current_elements.items():
        try:
            if elem_wrapper.element_info.control_type == "CheckBox":
                checkbox_indices.append(idx)
        except Exception:
            continue

    print(f"    {len(checkbox_indices)}個のCheckBoxが見つかりました: {checkbox_indices[:10]}")

    # CheckBox周辺のText要素を探す
    print("\n[6] CheckBox周辺のText、TableCell、Label要素を調査...")
    print("=" * 80)

    for cb_idx in checkbox_indices[:8]:  # 最初の8個を調査
        print(f"\n--- CheckBox #{cb_idx} の周辺 ---")

        cb_wrapper = driver.current_elements[cb_idx]
        cb_info = cb_wrapper.element_info
        print(f"  automation_id: '{cb_info.automation_id}'")

        # CheckBoxの前後50要素を調べる
        nearby_indices = range(max(0, cb_idx - 20), min(len(driver.current_elements), cb_idx + 20))

        print(f"  周辺要素 (index {cb_idx-20} ~ {cb_idx+20}):")

        found_text = []
        for nearby_idx in nearby_indices:
            if nearby_idx not in driver.current_elements:
                continue

            elem_wrapper = driver.current_elements[nearby_idx]
            try:
                info = elem_wrapper.element_info
                control_type = info.control_type

                # Text、TableCell、Labelなどのテキスト情報を持つ要素
                if control_type in ["Text", "DataItem", "Custom", "Table", "Group", "Pane"]:
                    text = elem_wrapper.window_text()
                    name = info.name

                    if text or name:
                        text_info = f"    [{nearby_idx}] {control_type}: text='{text}', name='{name}'"
                        found_text.append(text_info)

                        # 「収受」「添付」「文書」などのキーワードをチェック
                        if any(keyword in text or keyword in name for keyword in ["収受", "添付", "文書", "PDF", "Excel"]):
                            print(f"    ★ [{nearby_idx}] {control_type}: text='{text}', name='{name}'")

            except Exception:
                continue

        # 見つかったテキスト要素を表示（最大10個）
        if found_text:
            print(f"  テキスト要素: {len(found_text)}個")
            for text_info in found_text[:10]:
                if "★" not in text_info:
                    print(text_info)
        else:
            print(f"  テキスト要素: なし")

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == "__main__":
    investigate_surrounding_elements()
