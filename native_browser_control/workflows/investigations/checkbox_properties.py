"""
CheckBoxの詳細プロパティを確認する調査ワークフロー。
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


def run_checkbox_properties(
    output: OutputTarget = "stdout",
    stderr_output: OutputTarget | None = None,
) -> WorkflowResult:
    """CheckBoxの詳細プロパティを確認し、結果を指定先に出力する。"""

    result = None

    def _task() -> None:
        nonlocal result
        logger.info("=" * 80)
        logger.info("CheckBoxプロパティ確認")
        logger.info("=" * 80)

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

        logger.info("CheckBox詳細プロパティ:")
        logger.info("=" * 80)

        for i, idx in enumerate(checkbox_indices):
            elem_wrapper = driver.current_elements[idx]
            info = elem_wrapper.element_info

            logger.info(f"CheckBox #{i} (index={idx}):")
            logger.info(f"  automation_id:      '{info.automation_id}'")
            logger.info(f"  control_type:       '{info.control_type}'")
            logger.info(f"  class_name:         '{info.class_name}'")
            logger.info(f"  name:               '{info.name}'")

            # トグル状態
            try:
                toggle_state = elem_wrapper.get_toggle_state()
                logger.info(f"  toggle_state:       {toggle_state}")
            except Exception as exc:  # noqa: BLE001
                logger.error(f"  toggle_state:       ERROR: {exc}")

            # 有効/無効状態
            try:
                is_enabled = elem_wrapper.is_enabled()
                logger.info(f"  is_enabled:         {is_enabled}")
            except Exception as exc:  # noqa: BLE001
                logger.error(f"  is_enabled:         ERROR: {exc}")

            # 表示状態
            try:
                # element_infoにis_offscreenやis_visibleがあるかチェック
                if hasattr(info, "is_offscreen"):
                    logger.info(f"  is_offscreen:       {info.is_offscreen}")
                if hasattr(info, "is_visible"):
                    logger.info(f"  is_visible:         {info.is_visible}")
            except Exception as exc:  # noqa: BLE001
                logger.error(f"  visibility:         ERROR: {exc}")

            # BoundingRectangle
            try:
                if hasattr(info, "rectangle"):
                    logger.info(f"  rectangle:          {info.rectangle}")
            except Exception as exc:  # noqa: BLE001
                logger.error(f"  rectangle:          ERROR: {exc}")

        logger.info("=" * 80)
        logger.info("確認完了")
        logger.info("=" * 80)

        result = WorkflowResult(
            exit_code=0,
            summary={"status": "completed", "checkbox_count": len(checkbox_indices)}
        )

    log = route_output(_task, output, stderr_target=stderr_output)

    if result:
        result.log = log

    return result or WorkflowResult(exit_code=1, summary={"status": "failed"})


def main() -> None:
    parser = argparse.ArgumentParser(description="CheckBoxの詳細プロパティを確認する調査ワークフロー")
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
    result = run_checkbox_properties(stdout_target, stderr_target)

    # サマリーを表示
    print(f"\n--- Summary ---")
    print(f"Exit Code: {result.exit_code}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
