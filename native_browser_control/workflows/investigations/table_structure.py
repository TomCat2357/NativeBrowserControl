"""
テーブル全体構造を調査
"""
import argparse
import time

from native_browser_control.core.driver import NativeEdgeDriver
from native_browser_control.utils.output import add_output_argument, route_output

def investigate_table_structure():
    """テーブル全体構造を調査"""
    print("=" * 80)
    print("テーブル構造調査")
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

    # 最初のCheckBox（全選択）の前50要素を表示（テーブルヘッダー調査）
    print("\n[5] テーブルヘッダー調査（全選択CheckBoxの前50要素）...")
    print("=" * 80)

    first_checkbox = checkbox_indices[0] if checkbox_indices else 0
    header_range = range(max(0, first_checkbox - 50), first_checkbox)

    for elem_idx in header_range:
        if elem_idx not in driver.current_elements:
            continue

        elem_wrapper = driver.current_elements[elem_idx]
        try:
            info = elem_wrapper.element_info
            text = elem_wrapper.window_text()
            name = info.name
            control_type = info.control_type

            if text or name:
                display_text = (text[:60] + "...") if len(text) > 60 else text
                display_name = (name[:60] + "...") if len(name) > 60 else name

                # キーワードチェック
                has_keyword = any(kw in text or kw in name for kw in ["収受", "文書", "種類", "番号", "ファイル名", "拡張子"])
                marker = "★ " if has_keyword else "  "

                print(f"{marker}[{elem_idx}] {control_type:15s} text='{display_text}', name='{display_name}'")

        except Exception:
            pass

    # 全選択CheckBoxから2個目のCheckBoxまでの全要素を表示（1行目のデータ）
    print(f"\n[6] 1行目のデータ（CheckBox #{checkbox_indices[0]} から #{checkbox_indices[1]} まで）...")
    print("=" * 80)

    if len(checkbox_indices) >= 2:
        row1_range = range(checkbox_indices[0], checkbox_indices[1])

        for elem_idx in row1_range:
            if elem_idx not in driver.current_elements:
                continue

            elem_wrapper = driver.current_elements[elem_idx]
            try:
                info = elem_wrapper.element_info
                text = elem_wrapper.window_text()
                name = info.name
                control_type = info.control_type

                if text or name or control_type == "CheckBox":
                    display_text = (text[:60] + "...") if len(text) > 60 else text
                    display_name = (name[:60] + "...") if len(name) > 60 else name

                    print(f"  [{elem_idx}] {control_type:15s} text='{display_text}', name='{display_name}'")

            except Exception:
                pass

    # 2行目のデータ（2個目から3個目のCheckBoxまで）
    print(f"\n[7] 2行目のデータ（CheckBox #{checkbox_indices[1]} から #{checkbox_indices[2]} まで）...")
    print("=" * 80)

    if len(checkbox_indices) >= 3:
        row2_range = range(checkbox_indices[1], checkbox_indices[2])

        for elem_idx in row2_range:
            if elem_idx not in driver.current_elements:
                continue

            elem_wrapper = driver.current_elements[elem_idx]
            try:
                info = elem_wrapper.element_info
                text = elem_wrapper.window_text()
                name = info.name
                control_type = info.control_type

                if text or name or control_type == "CheckBox":
                    display_text = (text[:60] + "...") if len(text) > 60 else text
                    display_name = (name[:60] + "...") if len(name) > 60 else name

                    print(f"  [{elem_idx}] {control_type:15s} text='{display_text}', name='{display_name}'")

            except Exception:
                pass

    # 7行目のデータ（最後のCheckBoxから後ろ80要素）
    print(f"\n[8] 7行目のデータ（最後のCheckBox #{checkbox_indices[-1]} から後ろ80要素）...")
    print("=" * 80)

    if checkbox_indices:
        last_checkbox = checkbox_indices[-1]
        row7_range = range(last_checkbox, min(len(driver.current_elements), last_checkbox + 80))

        for elem_idx in row7_range:
            if elem_idx not in driver.current_elements:
                continue

            elem_wrapper = driver.current_elements[elem_idx]
            try:
                info = elem_wrapper.element_info
                text = elem_wrapper.window_text()
                name = info.name
                control_type = info.control_type

                if text or name or control_type == "CheckBox":
                    display_text = (text[:60] + "...") if len(text) > 60 else text
                    display_name = (name[:60] + "...") if len(name) > 60 else name

                    # キーワードチェック
                    has_keyword = any(kw in text or kw in name for kw in ["収受", "文書", "01_", "02_", "03_", "04_", "05_", "06_", "07_"])
                    marker = "★ " if has_keyword else "  "

                    print(f"{marker}[{elem_idx}] {control_type:15s} text='{display_text}', name='{display_name}'")

            except Exception:
                pass

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)


def run_table_structure(output: str = "stdout") -> str:
    """テーブル構造調査を指定出力先で実行する。"""

    return route_output(investigate_table_structure, output)


def main() -> None:
    parser = argparse.ArgumentParser(description="テーブル全体構造を調査するワークフロー")
    add_output_argument(parser)
    args = parser.parse_args()
    run_table_structure(args.output)


if __name__ == "__main__":
    main()
