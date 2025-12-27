"""
CheckBoxの詳細プロパティを確認する調査ワークフロー。
"""

import argparse
import time

from native_browser_control.core.driver import NativeEdgeDriver
from native_browser_control.utils.output import add_output_argument, route_output


def run_checkbox_properties(output: str = "stdout") -> str:
    """CheckBoxの詳細プロパティを確認し、結果を指定先に出力する。"""

    def _task() -> None:
        print("=" * 80)
        print("CheckBoxプロパティ確認")
        print("=" * 80)

        # ブラウザに接続
        driver = NativeEdgeDriver(retries=2, start_if_not_found=False)

        # CheckBoxの数を確認
        driver.scan_page_elements(control_type="CheckBox", max_elements=50, foreground=True, settle_ms=100)
        checkbox_count = len(driver.current_elements)

        if checkbox_count <= 2:
            driver.scan_page_elements(control_type="Button", max_elements=100, foreground=True, settle_ms=100)
            driver.filter_current_elements(name_regex="添付表示", output="simple", overwrite=True)
            if driver.current_elements:
                driver.click_by_index(min(driver.current_elements.keys()))
                time.sleep(1.5)

        # CheckBoxをスキャン
        driver.scan_page_elements(control_type="CheckBox", max_elements=50, foreground=True, settle_ms=100)
        checkbox_indices = sorted(driver.current_elements.keys())

        print("\nCheckBox詳細プロパティ:")
        print("=" * 80)

        for i, idx in enumerate(checkbox_indices):
            elem_wrapper = driver.current_elements[idx]
            info = elem_wrapper.element_info

            print(f"\nCheckBox #{i} (index={idx}):")
            print(f"  automation_id:      '{info.automation_id}'")
            print(f"  control_type:       '{info.control_type}'")
            print(f"  class_name:         '{info.class_name}'")
            print(f"  name:               '{info.name}'")

            # トグル状態
            try:
                toggle_state = elem_wrapper.get_toggle_state()
                print(f"  toggle_state:       {toggle_state}")
            except Exception as exc:  # noqa: BLE001
                print(f"  toggle_state:       ERROR: {exc}")

            # 有効/無効状態
            try:
                is_enabled = elem_wrapper.is_enabled()
                print(f"  is_enabled:         {is_enabled}")
            except Exception as exc:  # noqa: BLE001
                print(f"  is_enabled:         ERROR: {exc}")

            # 表示状態
            try:
                # element_infoにis_offscreenやis_visibleがあるかチェック
                if hasattr(info, "is_offscreen"):
                    print(f"  is_offscreen:       {info.is_offscreen}")
                if hasattr(info, "is_visible"):
                    print(f"  is_visible:         {info.is_visible}")
            except Exception as exc:  # noqa: BLE001
                print(f"  visibility:         ERROR: {exc}")

            # BoundingRectangle
            try:
                if hasattr(info, "rectangle"):
                    print(f"  rectangle:          {info.rectangle}")
            except Exception as exc:  # noqa: BLE001
                print(f"  rectangle:          ERROR: {exc}")

        print("\n" + "=" * 80)
        print("確認完了")
        print("=" * 80)

    return route_output(_task, output)


def main() -> None:
    parser = argparse.ArgumentParser(description="CheckBoxの詳細プロパティを確認する調査ワークフロー")
    add_output_argument(parser)
    args = parser.parse_args()
    run_checkbox_properties(args.output)


if __name__ == "__main__":
    main()
