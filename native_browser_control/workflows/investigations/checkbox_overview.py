"""
CheckBoxの詳細情報を調査するワークフロー。
"""

import argparse
import logging
import time

from native_browser_control.core.driver import NativeEdgeDriver
from native_browser_control.utils.output import (
    OutputTarget,
    WorkflowResult,
    add_logging_argument,
    add_output_argument,
    resolve_output_targets,
    route_output,
    setup_logger,
)

logger = setup_logger(__name__)


def run_checkbox_overview(
    output: OutputTarget = "stdout",
    stderr_output: OutputTarget | None = None,
) -> WorkflowResult:
    """CheckBoxの詳細情報を表示し、出力先を切り替え可能にする。"""

    result = None

    def _task() -> None:
        nonlocal result
        logger.info("=" * 80)
        logger.info("CheckBox詳細情報調査")
        logger.info("=" * 80)

        # ブラウザに接続
        logger.info("[1] ブラウザに接続中...")
        driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
        logger.info("    接続完了")

        # 「添付表示」ボタンをクリックして画面を切り替え
        logger.info("[2] 「添付表示」ボタンをクリックして画面を切り替え...")
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
                logger.info(f"    「添付表示」ボタンをクリックしました (index={switch_button_idx})")
                time.sleep(1.5)  # 画面更新待機
            else:
                logger.warning("    「添付表示」ボタンが見つかりませんでした（スキップ）")
        except Exception as exc:  # noqa: BLE001
            logger.error(f"    エラー: {exc}")

        # CheckBoxをスキャン
        logger.info("[3] CheckBox要素をスキャン中...")
        driver.scan_page_elements(
            control_type="CheckBox",
            max_elements=50,
            foreground=True,
            settle_ms=100,
        )

        checkbox_count = len(driver.current_elements)
        logger.info(f"    {checkbox_count}個のCheckBoxが見つかりました")

        # 各CheckBoxの詳細情報を表示
        logger.info("[4] CheckBox詳細情報:")
        logger.info("=" * 80)

        for idx in sorted(driver.current_elements.keys()):
            elem_wrapper = driver.current_elements[idx]
            logger.info(f"--- CheckBox #{idx} ---")

            try:
                # 基本情報
                logger.info(f"  window_text():      '{elem_wrapper.window_text()}'")

                # element_info の各属性
                info = elem_wrapper.element_info
                logger.info(f"  name:               '{info.name}'")
                logger.info(f"  automation_id:      '{info.automation_id}'")
                logger.info(f"  class_name:         '{info.class_name}'")
                logger.info(f"  control_type:       '{info.control_type}'")

                # 追加情報
                if hasattr(info, "help_text"):
                    logger.info(f"  help_text:          '{info.help_text}'")
                if hasattr(info, "item_type"):
                    logger.info(f"  item_type:          '{info.item_type}'")
                if hasattr(info, "localized_control_type"):
                    logger.info(f"  localized_control_type: '{info.localized_control_type}'")

                # トグル状態
                toggle_state = elem_wrapper.get_toggle_state()
                logger.info(f"  toggle_state:       {toggle_state} (0=未チェック, 1=チェック済み)")

                # 親要素の情報を取得してみる
                try:
                    # 親要素にアクセスできるか試す
                    if hasattr(elem_wrapper, "parent"):
                        parent = elem_wrapper.parent()
                        logger.info(f"  parent.name:        '{parent.element_info.name}'")
                except Exception as exc:  # noqa: BLE001
                    logger.debug(f"  parent:             (取得失敗: {exc})")

            except Exception as exc:  # noqa: BLE001
                logger.error(f"  [ERROR] 情報取得失敗: {exc}")

        logger.info("=" * 80)
        logger.info("調査完了")
        logger.info("=" * 80)

        result = WorkflowResult(
            exit_code=0,
            summary={"status": "completed", "checkbox_count": checkbox_count}
        )

    log = route_output(_task, output, stderr_target=stderr_output)

    if result:
        result.log = log

    return result or WorkflowResult(exit_code=1, summary={"status": "failed"})


def main() -> None:
    parser = argparse.ArgumentParser(description="CheckBoxの詳細情報を表示するワークフロー")
    add_output_argument(parser)
    add_logging_argument(parser)
    args = parser.parse_args()

    # ログレベルを設定
    log_level = getattr(logging, args.log_level)
    logger.setLevel(log_level)
    for handler in logger.handlers:
        handler.setLevel(log_level)

    stdout_target, stderr_target = resolve_output_targets(
        args.output, stdout_target=args.stdout, stderr_target=args.stderr
    )
    result = run_checkbox_overview(stdout_target, stderr_target)

    # サマリーを表示
    print(f"\n--- Summary ---")
    print(f"Exit Code: {result.exit_code}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
