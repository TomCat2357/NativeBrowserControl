"""
決裁ページの表構造を完全調査
収受文書情報から「表示」ボタンまでを精査
"""
from native_browser_driver import NativeEdgeDriver
import time

def investigate_table_full():
    """表構造の完全調査"""
    print("=" * 100)
    print("決裁ページ表構造完全調査")
    print("=" * 100)

    # ブラウザに接続
    print("\n[1] ブラウザに接続中...")
    driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
    print("    接続完了")

    # CheckBoxの数を確認
    driver.scan_page_elements(control_type="CheckBox", max_elements=50, foreground=True, settle_ms=100)
    checkbox_count = len(driver.current_elements)

    if checkbox_count <= 2:
        driver.scan_page_elements(control_type="Button", max_elements=100, foreground=True, settle_ms=100)
        driver.filter_current_elements(name_regex="添付表示", output="simple", overwrite=True)
        if driver.current_elements:
            driver.click_by_index(min(driver.current_elements.keys()))
            time.sleep(1.5)

    # 全要素をスキャン
    print("\n[2] 全要素をスキャン中...")
    driver.scan_page_elements(max_elements=1500, foreground=True, settle_ms=200)
    print(f"    {len(driver.current_elements)}個の要素が見つかりました")

    # 「収受」を含む要素を検索
    print("\n[3] 「収受」を含む要素を検索...")
    shuushu_indices = []
    for idx, elem_wrapper in driver.current_elements.items():
        try:
            text = elem_wrapper.window_text()
            name = elem_wrapper.element_info.name
            if "収受" in text or "収受" in name:
                shuushu_indices.append(idx)
        except Exception:
            continue

    print(f"    {len(shuushu_indices)}個見つかりました: {shuushu_indices[:10]}")

    # 「表示」ボタンを検索
    print("\n[4] 「表示」ボタンを検索...")
    hyouji_indices = []
    for idx, elem_wrapper in driver.current_elements.items():
        try:
            text = elem_wrapper.window_text()
            name = elem_wrapper.element_info.name
            control_type = elem_wrapper.element_info.control_type
            if control_type == "Button" and text == "表示":
                hyouji_indices.append(idx)
        except Exception:
            continue

    print(f"    {len(hyouji_indices)}個見つかりました: {hyouji_indices}")

    # 「収受」から「表示」ボタンまでの全要素を表示
    if shuushu_indices and hyouji_indices:
        start_idx = min(shuushu_indices)
        end_idx = max(hyouji_indices)

        print(f"\n[5] 「収受」(index={start_idx}) から 「表示」ボタン(index={end_idx}) までの全要素:")
        print("=" * 100)

        for elem_idx in range(start_idx, end_idx + 20):
            if elem_idx not in driver.current_elements:
                continue

            elem_wrapper = driver.current_elements[elem_idx]
            try:
                info = elem_wrapper.element_info
                text = elem_wrapper.window_text()
                name = info.name
                control_type = info.control_type
                automation_id = info.automation_id

                # テキストがある要素、またはCheckBox/Buttonを表示
                if text or name or control_type in ["CheckBox", "Button"]:
                    text_display = (text[:70] + "...") if len(text) > 70 else text
                    name_display = (name[:70] + "...") if len(name) > 70 else name

                    # 重要な要素をマーク
                    is_important = control_type in ["CheckBox", "Button"] or \
                                 any(kw in text or kw in name for kw in ["収受", "文書", "種類", "番号", "ファイル名", "01_", "02_", "03_"])

                    marker = "★ " if is_important else "  "

                    print(f"{marker}[{elem_idx:3d}] {control_type:15s} text='{text_display}'")
                    if name and name != text:
                        print(f"                                  name='{name_display}'")
                    if automation_id:
                        print(f"                                  automation_id='{automation_id}'")

            except Exception as e:
                pass

    # CheckBoxの詳細情報
    print(f"\n[6] CheckBoxの詳細情報:")
    print("=" * 100)

    checkbox_list = []
    for idx, elem_wrapper in driver.current_elements.items():
        try:
            if elem_wrapper.element_info.control_type == "CheckBox":
                info = elem_wrapper.element_info
                toggle_state = elem_wrapper.get_toggle_state()
                checkbox_list.append({
                    'index': idx,
                    'automation_id': info.automation_id,
                    'toggle_state': toggle_state
                })
        except Exception:
            continue

    for i, cb in enumerate(checkbox_list):
        marker = "✅" if cb['toggle_state'] == 1 else "  "
        print(f"{marker} CheckBox #{i}: index={cb['index']:3d}, automation_id='{cb['automation_id']}', state={cb['toggle_state']}")

    print("\n" + "=" * 100)
    print("調査完了")
    print("=" * 100)

if __name__ == "__main__":
    investigate_table_full()
