"""
決裁確認ページから情報を抽出し、添付ファイルをダウンロードして展開するスクリプト
"""
import argparse
import json
import logging
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, List

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
from native_browser_control.workflows.extraction.kesai_page import run_kesai_extraction

logger = setup_logger(__name__)


def extract_kesai_info(
    output_target: OutputTarget = "stdout",
    stderr_output: OutputTarget | None = None,
    save_to_file: bool = False,
    output_filename: str = "kesai_info.txt",
) -> str:
    """決裁ページの情報抽出を実行し、結果を返す。"""
    logger.info("=" * 80)
    logger.info("決裁情報抽出中...")
    logger.info("=" * 80)

    output, exit_code = run_kesai_extraction(output_target, stderr_output)

    if exit_code != 0:
        logger.warning(f"抽出処理が終了コード {exit_code} で終了しました")

    # ファイルに保存（オプション）
    if save_to_file:
        with open(output_filename, "w", encoding="utf-8") as f:
            f.write(output)
        logger.info(f"出力を {output_filename} に保存しました。")

    return output


def load_attachment_info() -> Dict[str, List[Dict[str, str]]]:
    """kesai_data.jsonから添付ファイル情報を読み込む"""
    try:
        with open("kesai_data.json", "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("添付ファイル", {})
    except Exception as exc:
        logger.warning(f"kesai_data.jsonの読み込みに失敗: {exc}")
        return {}


def find_attachment_switch_button(driver) -> int:
    """添付表示切り替えボタンのインデックスを見つける"""
    try:
        # Button要素をスキャン
        driver.scan_page_elements(
            control_type="Button",
            max_elements=100,
            foreground=True,
            settle_ms=100,
        )

        # 「添付表示」を含むボタンを探す
        driver.filter_current_elements(
            name_regex="添付表示",
            output="simple",
            overwrite=True,
        )

        if driver.current_elements:
            # 最初のボタンのインデックスを返す
            return min(driver.current_elements.keys())
    except Exception as exc:
        logger.warning(f"添付表示切り替えボタンが見つかりません: {exc}")

    return None


def download_attachments_once(driver, attachment_count: int) -> bool:
    """
    添付ファイルを1回ダウンロード

    Args:
        driver: NativeEdgeDriver インスタンス
        attachment_count: 添付ファイル数（0=スキップ、1=単一ファイル、2以上=ZIP）

    Returns:
        bool: ダウンロード成功したか
    """
    if attachment_count == 0:
        logger.info("  添付ファイルなし。スキップします。")
        return False

    try:
        # 1. CheckBox要素をスキャン
        logger.debug("  1. CheckBox要素をスキャン中...")
        driver.scan_page_elements(
            control_type="CheckBox",
            max_elements=50,
            foreground=True,
            settle_ms=100,
        )

        if not driver.current_elements:
            logger.error("    エラー: CheckBoxが見つかりません")
            return False

        # 2. all_checkboxをクリック（通常はインデックス0）
        logger.debug("  2. 全選択チェックボックスをクリック...")
        checkbox_idx = min(driver.current_elements.keys())
        driver.click_by_index(checkbox_idx)
        time.sleep(0.5)

        # 3. Button要素をスキャン
        logger.debug("  3. Button要素をスキャン中...")
        driver.scan_page_elements(
            control_type="Button",
            max_elements=100,
            foreground=True,
            settle_ms=100,
        )

        # 4. 「表示」ボタンでフィルタリング
        logger.debug("  4. 「表示」ボタンを検索中...")
        driver.filter_current_elements(
            name_regex="表示",
            output="simple",
            overwrite=True,
        )

        # 「表示」というシンプルな名前のボタンを探す
        display_button_idx = None
        for idx in sorted(driver.current_elements.keys()):
            elem_wrapper = driver.current_elements[idx]
            try:
                name = elem_wrapper.window_text()
                if name == "表示":
                    display_button_idx = idx
                    break
            except Exception:
                continue

        if display_button_idx is None:
            logger.error("    エラー: 「表示」ボタンが見つかりません")
            return False

        # 5. 「表示」ボタンをクリック
        logger.debug(f"  5. 「表示」ボタンをクリック (index={display_button_idx})...")
        driver.click_by_index(display_button_idx)
        time.sleep(1.5)  # ダウンロードダイアログが開くまで待機

        # 6. SplitButton要素をスキャン
        logger.debug("  6. SplitButton要素をスキャン中...")
        driver.scan_page_elements(
            control_type="SplitButton",
            max_elements=50,
            foreground=True,
            settle_ms=100,
        )

        # 7. 「保存」ボタンでフィルタリング
        logger.debug("  7. 「保存」ボタンを検索中...")
        driver.filter_current_elements(
            name_regex="保存",
            output="simple",
            overwrite=True,
        )

        if not driver.current_elements:
            logger.error("    エラー: 「保存」ボタンが見つかりません")
            return False

        # 8. 「保存」ボタンをクリック
        save_button_idx = min(driver.current_elements.keys())
        logger.debug(f"  8. 「保存」ボタンをクリック (index={save_button_idx})...")
        driver.click_by_index(save_button_idx)
        time.sleep(2)  # ダウンロード開始を待機

        logger.info("  ダウンロード完了")
        return True

    except Exception as exc:
        logger.error(f"  ダウンロード中にエラーが発生しました: {exc}")
        return False


def extract_downloaded_zips(downloads_dir: str, zip_count: int) -> None:
    """
    ダウンロードされたZIPファイルを展開して削除

    Args:
        downloads_dir: ダウンロードディレクトリ
        zip_count: 処理するZIPファイル数
    """
    if zip_count == 0:
        logger.info("  ZIPファイルはありません。展開処理をスキップします。")
        return

    logger.info("=" * 80)
    logger.info("ZIPファイル展開中...")
    logger.info("=" * 80)

    downloads_path = Path(downloads_dir)

    # 最新のZIPファイルを取得
    zip_files = sorted(downloads_path.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)

    if not zip_files:
        logger.warning("  ZIPファイルが見つかりません")
        return

    # 指定された数のZIPファイルを処理
    zip_files_to_process = zip_files[:zip_count]

    logger.info(f"  処理するZIPファイル: {len(zip_files_to_process)}件")
    for zip_file in zip_files_to_process:
        logger.info(f"    - {zip_file.name}")

    # 各ZIPファイルを展開
    for zip_file in zip_files_to_process:
        logger.info(f"  展開中: {zip_file.name}")

        # PowerShellで展開（日本語ファイル名対応）
        ps_command = f"Expand-Archive -Path '{zip_file}' -DestinationPath '{downloads_path}' -Force"

        result = subprocess.run(
            ["powershell.exe", "-Command", ps_command],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            logger.info(f"    展開完了: {zip_file.name}")

            # ZIPファイルを削除
            try:
                zip_file.unlink()
                logger.info(f"    削除完了: {zip_file.name}")
            except Exception as exc:
                logger.warning(f"    ZIPファイルの削除に失敗: {exc}")
        else:
            logger.error(f"    展開に失敗: {result.stderr}")

    logger.info("ZIPファイル処理完了")


def main(
    save_output: bool = False,
    output_filename: str = "kesai_info.txt",
    output_target: OutputTarget = "stdout",
    stderr_output: OutputTarget | None = None,
) -> WorkflowResult:
    """メイン処理"""
    logger.info("決裁ファイル一括ダウンロードスクリプト")
    logger.info("=" * 80)

    # 1. 決裁情報を抽出
    extract_kesai_info(
        output_target=output_target,
        stderr_output=stderr_output,
        save_to_file=save_output,
        output_filename=output_filename,
    )

    # 2. 添付ファイル情報を読み込む
    logger.info("=" * 80)
    logger.info("添付ファイル情報を確認中...")
    logger.info("=" * 80)

    attachment_info = load_attachment_info()

    if not attachment_info:
        logger.warning("  添付ファイル情報が見つかりません。処理を終了します。")
        return WorkflowResult(
            exit_code=0,
            summary={"status": "no_attachments", "categories": {}}
        )

    # カテゴリごとの添付ファイル数をリストアップ
    categories = list(attachment_info.keys())
    attachment_counts = []

    for category in categories:
        files = attachment_info[category]
        count = len(files) if files else 0
        attachment_counts.append(count)
        logger.info(f"  {category}: {count}件")

    # 全カテゴリで添付ファイルが0件なら終了
    if all(count == 0 for count in attachment_counts):
        logger.info("  全カテゴリで添付ファイルが0件です。ダウンロード処理をスキップします。")
        return WorkflowResult(
            exit_code=0,
            summary={"status": "no_files", "categories": dict(zip(categories, attachment_counts))}
        )

    # 3. Edgeに接続
    logger.info("=" * 80)
    logger.info("Edgeに接続中...")
    logger.info("=" * 80)

    try:
        driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
        logger.info("  接続完了")
    except Exception as exc:
        logger.error(f"  Edgeに接続できません: {exc}")
        return WorkflowResult(
            exit_code=1,
            summary={"status": "connection_error", "error": str(exc)}
        )

    # 4. 添付ファイルを最大2回ダウンロード
    logger.info("=" * 80)
    logger.info("添付ファイルダウンロード中...")
    logger.info("=" * 80)

    download_results = []  # (成功/失敗, 添付ファイル数) のリスト
    max_attempts = len(attachment_counts)

    for attempt in range(max_attempts):
        logger.info("=" * 40)
        logger.info(f"ダウンロード {attempt + 1}回目:")
        logger.info(f"カテゴリ: {categories[attempt]}")
        logger.info(f"添付ファイル数: {attachment_counts[attempt]}件")
        logger.info("=" * 40)

        if download_attachments_once(driver, attachment_counts[attempt]):
            download_results.append((True, attachment_counts[attempt]))
            logger.info("  ダウンロード成功")
        else:
            download_results.append((False, attachment_counts[attempt]))
            # 添付ファイルが0件の場合は失敗扱いにしない
            if attachment_counts[attempt] > 0:
                logger.warning("  ダウンロード失敗")

        # 最後の試行でなければ、切り替えボタンを探してクリック
        if attempt < max_attempts - 1:
            logger.debug("  添付表示切り替えボタンを検索中...")
            switch_button_idx = find_attachment_switch_button(driver)

            if switch_button_idx is not None:
                logger.debug(f"  切り替えボタンをクリック (index={switch_button_idx})...")
                driver.click_by_index(switch_button_idx)
                time.sleep(1.5)  # 画面更新待ち
            else:
                logger.warning("  切り替えボタンが見つかりません。")
                # 切り替えボタンがない場合は、残りの試行をスキップ
                break

    # ダウンロード結果のサマリー
    logger.info("=" * 80)
    logger.info("ダウンロード結果:")
    logger.info("=" * 80)

    successful_downloads = 0
    zip_download_count = 0
    category_results = {}

    for i, (success, count) in enumerate(download_results):
        if success and count > 0:
            successful_downloads += 1
            if count >= 2:
                zip_download_count += 1
            status = f"✓ 成功 ({count}件"
            if count >= 2:
                status += ", ZIP形式"
            elif count == 1:
                status += ", 単一ファイル"
            status += ")"
            category_results[categories[i]] = {"success": True, "count": count}
        elif count == 0:
            status = "- スキップ (0件)"
            category_results[categories[i]] = {"success": True, "count": 0, "skipped": True}
        else:
            status = "✗ 失敗"
            category_results[categories[i]] = {"success": False, "count": count}

        logger.info(f"  {categories[i]}: {status}")

    # 5. ダウンロードしたZIPファイルを展開
    downloads_dir = r"C:\Users\sa11882\Downloads"
    extract_downloaded_zips(downloads_dir, zip_download_count)

    logger.info("=" * 80)
    logger.info("全処理完了")
    logger.info(f"  成功: {successful_downloads}件")
    logger.info(f"  ZIP展開: {zip_download_count}件")
    logger.info("=" * 80)

    return WorkflowResult(
        exit_code=0,
        summary={
            "status": "completed",
            "successful_downloads": successful_downloads,
            "zip_extractions": zip_download_count,
            "categories": category_results,
        }
    )


def cli() -> int:
    parser = argparse.ArgumentParser(description="決裁添付ファイルを一括ダウンロード")
    parser.add_argument("--save", "-s", action="store_true", help="決裁情報をファイルへ保存")
    parser.add_argument(
        "--output-file",
        default="kesai_info.txt",
        help="--save指定時に書き出すファイル名",
    )
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
    result = None

    def _task() -> None:
        nonlocal result
        result = main(args.save, args.output_file, stdout_target, stderr_target)

    log = route_output(_task, stdout_target, stderr_target=stderr_target)

    if result:
        result.log = log
        # サマリーを表示
        print(f"\n--- Summary ---")
        print(f"Exit Code: {result.exit_code}")
        for key, value in result.summary.items():
            print(f"{key}: {value}")
        return result.exit_code

    return 1


if __name__ == "__main__":
    raise SystemExit(cli())
