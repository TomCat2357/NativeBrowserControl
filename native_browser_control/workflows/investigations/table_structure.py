"""
テーブル全体構造を調査
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

def investigate_table_structure():
    """テーブル全体構造を調査"""
    logger.info("=" * 80)
    logger.info("テーブル構造調査")
    logger.info("=" * 80)

    # ブラウザに接続
    logger.info("[1] ブラウザに接続中...")
    driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
    logger.info("    接続完了")

    # CheckBoxの数を確認
    logger.info("[2] CheckBoxの数を確認...")
    driver.scan_page_elements(control_type="CheckBox", max_elements=50, foreground=True, settle_ms=100)
    checkbox_count = len(driver.current_elements)
    logger.info(f"    現在のCheckBox数: {checkbox_count}個")

    if checkbox_count <= 2:
        driver.scan_page_elements(control_type="Button", max_elements=100, foreground=True, settle_ms=100)
        driver.filter_current_elements(name_regex="添付表示", output="simple", overwrite=True)
        if driver.current_elements:
            driver.click_by_index(min(driver.current_elements.keys()))
            time.sleep(1.5)

    # 全要素をスキャン
    logger.info("[3] 全要素をスキャン中...")
    driver.scan_page_elements(max_elements=1000, foreground=True, settle_ms=100)
    logger.info(f"    {len(driver.current_elements)}個の要素が見つかりました")

    # CheckBoxを特定
    checkbox_indices = []
    for idx, elem_wrapper in driver.current_elements.items():
        try:
            if elem_wrapper.element_info.control_type == "CheckBox":
                checkbox_indices.append(idx)
        except Exception:
            continue

    logger.info(f"[4] CheckBox: {len(checkbox_indices)}個")
    logger.info(f"    インデックス: {checkbox_indices}")

    # 最初のCheckBox（全選択）の前50要素を表示（テーブルヘッダー調査）
    logger.info("[5] テーブルヘッダー調査（全選択CheckBoxの前50要素）...")
    logger.info("=" * 80)

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

                logger.info(f"{marker}[{elem_idx}] {control_type:15s} text='{display_text}', name='{display_name}'")

        except Exception:
            pass

    # 全選択CheckBoxから2個目のCheckBoxまでの全要素を表示（1行目のデータ）
    logger.info(f"[6] 1行目のデータ（CheckBox #{checkbox_indices[0]} から #{checkbox_indices[1]} まで）...")
    logger.info("=" * 80)

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

                    logger.info(f"  [{elem_idx}] {control_type:15s} text='{display_text}', name='{display_name}'")

            except Exception:
                pass

    # 2行目のデータ（2個目から3個目のCheckBoxまで）
    logger.info(f"[7] 2行目のデータ（CheckBox #{checkbox_indices[1]} から #{checkbox_indices[2]} まで）...")
    logger.info("=" * 80)

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

                    logger.info(f"  [{elem_idx}] {control_type:15s} text='{display_text}', name='{display_name}'")

            except Exception:
                pass

    # 7行目のデータ（最後のCheckBoxから後ろ80要素）
    logger.info(f"[8] 7行目のデータ（最後のCheckBox #{checkbox_indices[-1]} から後ろ80要素）...")
    logger.info("=" * 80)

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

                    logger.info(f"{marker}[{elem_idx}] {control_type:15s} text='{display_text}', name='{display_name}'")

            except Exception:
                pass

    logger.info("=" * 80)
    logger.info("調査完了")
    logger.info("=" * 80)


def run_table_structure(
    output: OutputTarget = "stdout",
    stderr_output: OutputTarget | None = None,
) -> WorkflowResult:
    """テーブル構造調査を指定出力先で実行する。"""

    result = None

    def _task() -> None:
        nonlocal result
        investigate_table_structure()
        result = WorkflowResult(
            exit_code=0,
            summary={"status": "completed"}
        )

    log = route_output(_task, output, stderr_target=stderr_output)

    if result:
        result.log = log

    return result or WorkflowResult(exit_code=1, summary={"status": "failed"})


def main() -> None:
    parser = argparse.ArgumentParser(description="テーブル全体構造を調査するワークフロー")
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
    result = run_table_structure(stdout_target, stderr_target)

    # サマリーを表示
    print(f"\n--- Summary ---")
    print(f"Exit Code: {result.exit_code}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
