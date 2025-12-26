"""
各ファイル行の全要素を詳細調査
"""
from native_browser_driver import NativeEdgeDriver
import time

def investigate_file_rows():
    """各ファイル行の全要素を調査"""
    print("=" * 80)
    print("ファイル行の詳細調査")
    print("=" * 80)

    # ブラウザに接続
    print("\n[1] ブラウザに接続中...")
    driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
    print("    接続完了")

    # CheckBoxの数を確認
    print("\n[2] CheckBoxの数を確認...")
    driver.scan_page_elements(control_type="CheckBox", max_elements=50, foreground=True, settle_ms=100)
    checkbox_count = len(driver.current_elements)
    print(f"    現在のCheckBox数: {checkbox_count}個")

    if checkbox_count <= 2:
        driver.scan_page_elements(control_type="Button", max_elements=100, foreground=True, settle_ms=100)
        driver.filter_current_elements(name_regex="添付表示", output="simple", overwrite=True)
        if driver.current_elements:
            driver.click_by_index(min(driver.current_elements.keys()))
            time.sleep(1.5)

    # 全要素をスキャン
    print("\n[3] 全要素をスキャン中...")
    driver.scan_page_elements(max_elements=1000, foreground=True, settle_ms=100)
    print(f"    {len(driver.current_elements)}個の要素が見つかりました")

    # CheckBoxを特定
    checkbox_indices = []
    for idx, elem_wrapper in driver.current_elements.items():
        try:
            if elem_wrapper.element_info.control_type == "CheckBox":
                checkbox_indices.append(idx)
        except Exception:
            continue

    print(f"\n[4] CheckBox: {len(checkbox_indices)}個")
    print(f"    インデックス: {checkbox_indices}")

    # 各CheckBoxからファイル名までの要素を全て表示
    print("\n[5] 各ファイル行の全要素を表示...")
    print("=" * 80)

    # 個別ファイルのCheckBox（全選択を除く）
    file_checkboxes = checkbox_indices[1:]

    for i, cb_idx in enumerate(file_checkboxes, start=1):
        print(f"\n{'='*80}")
        print(f"ファイル #{i} (CheckBox index={cb_idx})")
        print(f"{'='*80}")

        # CheckBoxの情報
        cb_wrapper = driver.current_elements[cb_idx]
        cb_info = cb_wrapper.element_info
        toggle_state = cb_wrapper.get_toggle_state()

        print(f"CheckBox [{cb_idx}]:")
        print(f"  automation_id:  '{cb_info.automation_id}'")
        print(f"  toggle_state:   {toggle_state} {'(チェック済み)' if toggle_state == 1 else '(未チェック)'}")

        # CheckBoxの後ろ40要素を全て表示
        print(f"\nCheckBox後の要素:")

        next_cb_idx = file_checkboxes[i] if i < len(file_checkboxes) else cb_idx + 100
        search_range = range(cb_idx + 1, min(next_cb_idx, cb_idx + 40))

        for elem_idx in search_range:
            if elem_idx not in driver.current_elements:
                continue

            elem_wrapper = driver.current_elements[elem_idx]
            try:
                info = elem_wrapper.element_info
                text = elem_wrapper.window_text()
                name = info.name
                control_type = info.control_type
                automation_id = info.automation_id

                # 空でない要素のみ表示
                if text or name:
                    # キーワードチェック
                    has_keyword = any(kw in text or kw in name for kw in ["収受", "文書", "別紙", "pdf", "xlsx"])
                    marker = "★ " if has_keyword else "  "

                    # テキストを50文字に制限
                    display_text = (text[:50] + "...") if len(text) > 50 else text
                    display_name = (name[:50] + "...") if len(name) > 50 else name

                    print(f"{marker}[{elem_idx}] {control_type:15s} text='{display_text}', name='{display_name}'")

                    # automation_idも表示（空でない場合）
                    if automation_id:
                        print(f"                                  automation_id='{automation_id}'")

            except Exception as e:
                pass

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == "__main__":
    investigate_file_rows()
