"""
ファイル拡張子要素の周辺を調査
"""
import argparse
import time

from native_browser_control.core.driver import NativeEdgeDriver
from native_browser_control.utils.output import add_output_argument, route_output

def investigate_file_extensions():
    """ファイル拡張子要素の周辺を調査"""
    print("=" * 80)
    print("ファイル拡張子要素の周辺調査")
    print("=" * 80)

    # ブラウザに接続
    print("\n[1] ブラウザに接続中...")
    driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
    print("    接続完了")

    # CheckBoxの数を確認
    print("\n[2] CheckBoxの数を確認...")
    driver.scan_page_elements(
        control_type="CheckBox",
        max_elements=50,
        foreground=True,
        settle_ms=100,
    )

    checkbox_count = len(driver.current_elements)
    print(f"    現在のCheckBox数: {checkbox_count}個")

    if checkbox_count <= 2:
        print("\n[3] 「添付表示」ボタンをクリック...")
        driver.scan_page_elements(control_type="Button", max_elements=100, foreground=True, settle_ms=100)
        driver.filter_current_elements(name_regex="添付表示", output="simple", overwrite=True)
        if driver.current_elements:
            driver.click_by_index(min(driver.current_elements.keys()))
            time.sleep(1.5)

    # 全要素をスキャン
    print("\n[4] 全要素をスキャン中...")
    driver.scan_page_elements(max_elements=1000, foreground=True, settle_ms=100)
    print(f"    {len(driver.current_elements)}個の要素が見つかりました")

    # ファイル拡張子（pdf, xlsx）を含む要素を検索
    print("\n[5] ファイル拡張子を含む要素を検索...")
    extension_indices = []

    for idx, elem_wrapper in driver.current_elements.items():
        try:
            text = elem_wrapper.window_text()
            if text and text.lower() in ['pdf', 'xlsx', 'xls', 'doc', 'docx']:
                extension_indices.append(idx)
        except Exception:
            continue

    print(f"    {len(extension_indices)}個の拡張子要素が見つかりました")
    print(f"    インデックス: {extension_indices}")

    # 各拡張子要素の周辺を調査
    print("\n[6] 各拡張子要素の周辺を調査...")
    print("=" * 80)

    for ext_idx in extension_indices:
        ext_wrapper = driver.current_elements[ext_idx]
        ext_text = ext_wrapper.window_text()

        print(f"\n--- [{ext_idx}] 拡張子: {ext_text} ---")

        # 前後30要素を調べる
        nearby_range = range(max(0, ext_idx - 30), min(len(driver.current_elements), ext_idx + 10))

        for nearby_idx in nearby_range:
            if nearby_idx not in driver.current_elements:
                continue

            elem_wrapper = driver.current_elements[nearby_idx]
            try:
                info = elem_wrapper.element_info
                text = elem_wrapper.window_text()
                name = info.name
                control_type = info.control_type

                # テキストがある要素だけ表示
                if text or name:
                    # 「収受」を含むかチェック
                    has_keyword = "収受" in text or "収受" in name or "文書" in text or "文書" in name

                    marker = "★ " if has_keyword else "  "
                    print(f"{marker}[{nearby_idx}] {control_type}: '{text[:50] if text else name[:50]}'")

            except Exception:
                continue

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)


def run_file_extension_investigation(output: str = "stdout") -> str:
    """ファイル拡張子調査を指定の出力先で実行する。"""

    return route_output(investigate_file_extensions, output)


def main() -> None:
    parser = argparse.ArgumentParser(description="ファイル拡張子要素の周辺を調査するワークフロー")
    add_output_argument(parser)
    args = parser.parse_args()
    run_file_extension_investigation(args.output)


if __name__ == "__main__":
    main()
