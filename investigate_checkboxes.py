"""
CheckBoxの詳細情報を調査するスクリプト
"""
from native_browser_driver import NativeEdgeDriver
import time

def investigate_checkboxes():
    """CheckBoxの詳細情報を表示"""
    print("=" * 80)
    print("CheckBox詳細情報調査")
    print("=" * 80)

    # ブラウザに接続
    print("\n[1] ブラウザに接続中...")
    driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
    print("    接続完了")

    # 「添付表示」ボタンをクリックして画面を切り替え
    print("\n[2] 「添付表示」ボタンをクリックして画面を切り替え...")
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
            time.sleep(1.5)  # 画面更新待機
        else:
            print("    「添付表示」ボタンが見つかりませんでした（スキップ）")
    except Exception as exc:
        print(f"    エラー: {exc}")

    # CheckBoxをスキャン
    print("\n[3] CheckBox要素をスキャン中...")
    driver.scan_page_elements(
        control_type="CheckBox",
        max_elements=50,
        foreground=True,
        settle_ms=100,
    )

    print(f"    {len(driver.current_elements)}個のCheckBoxが見つかりました")

    # 各CheckBoxの詳細情報を表示
    print("\n[4] CheckBox詳細情報:")
    print("=" * 80)

    for idx in sorted(driver.current_elements.keys()):
        elem_wrapper = driver.current_elements[idx]
        print(f"\n--- CheckBox #{idx} ---")

        try:
            # 基本情報
            print(f"  window_text():      '{elem_wrapper.window_text()}'")

            # element_info の各属性
            info = elem_wrapper.element_info
            print(f"  name:               '{info.name}'")
            print(f"  automation_id:      '{info.automation_id}'")
            print(f"  class_name:         '{info.class_name}'")
            print(f"  control_type:       '{info.control_type}'")

            # 追加情報
            if hasattr(info, 'help_text'):
                print(f"  help_text:          '{info.help_text}'")
            if hasattr(info, 'item_type'):
                print(f"  item_type:          '{info.item_type}'")
            if hasattr(info, 'localized_control_type'):
                print(f"  localized_control_type: '{info.localized_control_type}'")

            # トグル状態
            toggle_state = elem_wrapper.get_toggle_state()
            print(f"  toggle_state:       {toggle_state} (0=未チェック, 1=チェック済み)")

            # 親要素の情報を取得してみる
            try:
                # 親要素にアクセスできるか試す
                if hasattr(elem_wrapper, 'parent'):
                    parent = elem_wrapper.parent()
                    print(f"  parent.name:        '{parent.element_info.name}'")
            except Exception as e:
                print(f"  parent:             (取得失敗: {e})")

        except Exception as exc:
            print(f"  [ERROR] 情報取得失敗: {exc}")

    print("\n" + "=" * 80)
    print("調査完了")
    print("=" * 80)

if __name__ == "__main__":
    investigate_checkboxes()
