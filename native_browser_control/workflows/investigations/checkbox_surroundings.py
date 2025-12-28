"""
CheckBoxの周辺要素を調査して「収受添付文書」情報を探すスクリプト
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

def investigate_surrounding_elements():
    """CheckBoxの周辺要素を調査"""
    logger.info("=" * 80)
    logger.info("CheckBox周辺要素調査")
    logger.info("=" * 80)

    # ブラウザに接続
    logger.info("[1] ブラウザに接続中...")
    driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
    logger.info("    接続完了")

    # CheckBoxの数を確認し、必要に応じて「添付表示」ボタンをクリック
    logger.info("[2] CheckBoxの数を確認...")
    driver.scan_page_elements(
        control_type="CheckBox",
        max_elements=50,
        foreground=True,
        settle_ms=100,
    )

    checkbox_count = len(driver.current_elements)
    logger.info(f"    現在のCheckBox数: {checkbox_count}個")

    # CheckBoxが2個以下なら「添付表示」をクリックして切り替え
    if checkbox_count <= 2:
        logger.info("[3] 「添付表示」ボタンをクリックして画面を切り替え...")
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
                time.sleep(1.5)
            else:
                logger.warning("    「添付表示」ボタンが見つかりませんでした")
        except Exception as exc:
            logger.error(f"    エラー: {exc}")
    else:
        logger.info("[3] CheckBoxが複数あるため、切り替え不要")

    # 全要素をスキャン
    logger.info("[4] 全要素をスキャン中...")
    driver.scan_page_elements(
        max_elements=1000,
        foreground=True,
        settle_ms=100,
    )
    logger.info(f"    {len(driver.current_elements)}個の要素が見つかりました")

    # CheckBoxのインデックスを記録
    logger.info("[5] CheckBoxを特定...")
    checkbox_indices = []
    for idx, elem_wrapper in driver.current_elements.items():
        try:
            if elem_wrapper.element_info.control_type == "CheckBox":
                checkbox_indices.append(idx)
        except Exception:
            continue

    logger.info(f"    {len(checkbox_indices)}個のCheckBoxが見つかりました: {checkbox_indices[:10]}")

    # CheckBox周辺のText要素を探す
    logger.info("[6] CheckBox周辺のText、TableCell、Label要素を調査...")
    logger.info("=" * 80)

    keyword_findings = 0
    for cb_idx in checkbox_indices[:8]:  # 最初の8個を調査
        logger.info(f"--- CheckBox #{cb_idx} の周辺 ---")

        cb_wrapper = driver.current_elements[cb_idx]
        cb_info = cb_wrapper.element_info
        logger.info(f"  automation_id: '{cb_info.automation_id}'")

        # CheckBoxの前後50要素を調べる
        nearby_indices = range(max(0, cb_idx - 20), min(len(driver.current_elements), cb_idx + 20))

        logger.debug(f"  周辺要素 (index {cb_idx-20} ~ {cb_idx+20}):")

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
                            logger.info(f"    ★ [{nearby_idx}] {control_type}: text='{text}', name='{name}'")
                            keyword_findings += 1

            except Exception:
                continue

        # 見つかったテキスト要素を表示（最大10個）
        if found_text:
            logger.debug(f"  テキスト要素: {len(found_text)}個")
            for text_info in found_text[:10]:
                if "★" not in text_info:
                    logger.debug(text_info)
        else:
            logger.debug("  テキスト要素: なし")

    logger.info("=" * 80)
    logger.info("調査完了")
    logger.info("=" * 80)

    return len(checkbox_indices), keyword_findings


def run_checkbox_surroundings(
    output: OutputTarget = "stdout",
    stderr_output: OutputTarget | None = None,
) -> WorkflowResult:
    """CheckBox周辺要素調査の出力先を切り替えて実行する。"""

    result = None

    def _task() -> None:
        nonlocal result
        checkbox_count, keyword_findings = investigate_surrounding_elements()
        result = WorkflowResult(
            exit_code=0,
            summary={
                "status": "completed",
                "checkbox_count": checkbox_count,
                "keyword_findings": keyword_findings,
            }
        )

    log = route_output(_task, output, stderr_target=stderr_output)

    if result:
        result.log = log

    return result or WorkflowResult(exit_code=1, summary={"status": "failed"})


def main() -> None:
    parser = argparse.ArgumentParser(description="CheckBoxの周辺要素を調査するワークフロー")
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
    result = run_checkbox_surroundings(stdout_target, stderr_target)

    # サマリーを表示
    print(f"\n--- Summary ---")
    print(f"Exit Code: {result.exit_code}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
