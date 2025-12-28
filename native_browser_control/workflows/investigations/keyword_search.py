"""
「収受」「文書」などのキーワードを含む全要素を検索
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

def search_keyword():
    """キーワードを含む要素を検索"""
    print("=" * 80)
    print("キーワード検索")
    print("=" * 80)

    # ブラウザに接続
    print("\n[1] ブラウザに接続中...")
    driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
    print("    接続完了")

    # CheckBoxの数を確認し、必要に応じて「添付表示」ボタンをクリック
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
        print("\n[3] 「添付表示」ボタンをクリックして画面を切り替え...")
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
                print(f"    「添付表示」ボタンをクリックしました")
                time.sleep(1.5)
        except Exception as exc:
            print(f"    エラー: {exc}")
    else:
        print("\n[3] CheckBoxが複数あるため、切り替え不要")

    # 全要素をスキャン
    print("\n[4] 全要素をスキャン中...")
    driver.scan_page_elements(
        max_elements=1000,
        foreground=True,
        settle_ms=100,
    )
    print(f"    {len(driver.current_elements)}個の要素が見つかりました")

    # キーワードを含む要素を検索
    keywords = ["収受", "文書", "添付", "PDF", "Excel", "xlsx", "pdf"]

    print(f"\n[5] キーワード {keywords} を含む要素を検索...")
    print("=" * 80)

    found_elements = []

    for idx, elem_wrapper in driver.current_elements.items():
        try:
            info = elem_wrapper.element_info
            text = elem_wrapper.window_text()
            name = info.name
            automation_id = info.automation_id
            control_type = info.control_type

            # キーワードチェック
            text_lower = text.lower() if text else ""
            name_lower = name.lower() if name else ""
            automation_id_lower = automation_id.lower() if automation_id else ""

            for keyword in keywords:
                if keyword.lower() in text_lower or keyword.lower() in name_lower or keyword.lower() in automation_id_lower:
                    found_elements.append({
                        'index': idx,
                        'control_type': control_type,
                        'text': text,
                        'name': name,
                        'automation_id': automation_id,
                        'keyword': keyword
                    })
                    break

        except Exception:
            continue

    print(f"    {len(found_elements)}個の要素が見つかりました\n")

    # 見つかった要素を表示
    for elem in found_elements:
        print(f"[{elem['index']}] {elem['control_type']}")
        print(f"  keyword:       '{elem['keyword']}'")
        print(f"  text:          '{elem['text']}'")
        print(f"  name:          '{elem['name']}'")
        print(f"  automation_id: '{elem['automation_id']}'")
        print()

    print("=" * 80)
    print("検索完了")
    print("=" * 80)


def run_keyword_search(
    output: OutputTarget = "stdout",
    stderr_output: OutputTarget | None = None,
) -> WorkflowResult:
    """キーワード検索結果を指定出力先へ送る。"""

    result = None

    def _task() -> None:
        nonlocal result
        search_keyword()
        result = WorkflowResult(
            exit_code=0,
            summary={"status": "completed"}
        )

    log = route_output(_task, output, stderr_target=stderr_output)

    if result:
        result.log = log

    return result or WorkflowResult(exit_code=1, summary={"status": "failed"})


def main() -> None:
    parser = argparse.ArgumentParser(description="指定キーワードを含む要素を検索するワークフロー")
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
    result = run_keyword_search(stdout_target, stderr_target)

    # サマリーを表示
    print(f"\n--- Summary ---")
    print(f"Exit Code: {result.exit_code}")
    for key, value in result.summary.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
