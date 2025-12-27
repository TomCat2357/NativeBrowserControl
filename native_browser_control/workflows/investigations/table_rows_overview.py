"""
全行の全要素を詳細調査
"""
import argparse
import time

from native_browser_control.core.driver import NativeEdgeDriver
from native_browser_control.utils.output import add_output_argument, route_output

def investigate_all_rows():
    """全行の全要素を詳細調査"""
    print("=" * 80)
    print("全行詳細調査")
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

    # 全行を調査
    print("\n[5] 全行の全要素を表示...")
    print("=" * 100)

    for i, cb_idx in enumerate(checkbox_indices):
        # 行の範囲を決定（現在のCheckBoxから次のCheckBoxまで）
        next_cb_idx = checkbox_indices[i + 1] if i + 1 < len(checkbox_indices) else cb_idx + 100
        row_range = range(cb_idx, next_cb_idx)

        # CheckBox情報
        cb_wrapper = driver.current_elements[cb_idx]
        cb_info = cb_wrapper.element_info
        toggle_state = cb_wrapper.get_toggle_state()

        # 行のタイトル
        row_title = "全選択CheckBox" if i == 0 else f"ファイル #{i}"

        print(f"\n{'='*100}")
        print(f"行 {i}: {row_title} (CheckBox index={cb_idx})")
        print(f"{'='*100}")
        print(f"CheckBox:")
        print(f"  automation_id:  '{cb_info.automation_id}'")
        print(f"  toggle_state:   {toggle_state} {'(チェック済み)' if toggle_state == 1 else '(未チェック)'}")
        print(f"\n行内の全要素:")

        # 行内の全要素を表示
        element_list = []
        for elem_idx in row_range:
            if elem_idx not in driver.current_elements:
                continue

            elem_wrapper = driver.current_elements[elem_idx]
            try:
                info = elem_wrapper.element_info
                text = elem_wrapper.window_text()
                name = info.name
                control_type = info.control_type

                # 全ての要素を記録（空でも）
                element_list.append({
                    'index': elem_idx,
                    'control_type': control_type,
                    'text': text,
                    'name': name
                })

            except Exception:
                pass

        # 要素を表示（空のテキストも含めて最初の20個）
        for elem in element_list[:20]:
            text_display = (elem['text'][:50] + "...") if len(elem['text']) > 50 else elem['text']
            name_display = (elem['name'][:50] + "...") if len(elem['name']) > 50 else elem['name']

            # 重要なキーワードをチェック
            is_important = any(kw in elem['text'] or kw in elem['name']
                             for kw in ["収受", "文書", "種類", "種", "別紙", "01_", "02_", "03_", "04_", "05_", "06_", "07_", "pdf", "xlsx"])

            marker = "★ " if is_important else "  "

            # テキストまたは名前があるか、CheckBoxの場合は表示
            if elem['text'] or elem['name'] or elem['control_type'] == 'CheckBox':
                print(f"{marker}[{elem['index']:3d}] {elem['control_type']:15s} text='{text_display}' name='{name_display}'")

        if len(element_list) > 20:
            print(f"  ... (残り{len(element_list) - 20}個の要素)")

    print("\n" + "=" * 100)
    print("調査完了")
    print("=" * 100)


def run_table_rows_overview(output: str = "stdout") -> str:
    """全行詳細調査を指定出力先で実行する。"""

    return route_output(investigate_all_rows, output)


def main() -> None:
    parser = argparse.ArgumentParser(description="全行の全要素を詳細に調査するワークフロー")
    add_output_argument(parser)
    args = parser.parse_args()
    run_table_rows_overview(args.output)


if __name__ == "__main__":
    main()
