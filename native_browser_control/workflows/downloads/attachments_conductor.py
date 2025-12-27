"""
決裁ファイル一括ダウンロードスクリプト v2
機能を細かく切り分け、コンダクター関数が全体を制御する設計
"""
import argparse
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from native_browser_control.core.driver import NativeEdgeDriver
from native_browser_control.utils.output import add_output_argument, route_output


# ================================================================================
# ユーティリティ関数
# ================================================================================

def print_section(title: str) -> None:
    """セクションヘッダーを表示"""
    print("\n" + "=" * 80)
    print(title)
    print("=" * 80)


def print_step(step: str) -> None:
    """ステップ情報を表示"""
    print(f"\n  {step}")


# ================================================================================
# ステップ1: ダウンロードフォルダをクリア
# ================================================================================

def clear_download_folder(downloads_dir: str) -> bool:
    """
    ダウンロードフォルダ内の全ファイルを削除

    Args:
        downloads_dir: ダウンロードディレクトリパス

    Returns:
        bool: 成功したか
    """
    print_section("ダウンロードフォルダをクリア")

    try:
        ps_command = f"Get-ChildItem -Path '{downloads_dir}\\*' -File | Remove-Item -Force"
        result = subprocess.run(
            ["powershell.exe", "-Command", ps_command],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            print("  [OK] ダウンロードフォルダを空にしました")
            return True
        else:
            print(f"  [ERROR] エラー: {result.stderr}")
            return False
    except Exception as exc:
        print(f"  [ERROR] 例外が発生: {exc}")
        return False


# ================================================================================
# ステップ2: ブラウザに接続
# ================================================================================

def connect_to_browser() -> Optional[NativeEdgeDriver]:
    """
    Edgeブラウザに接続

    Returns:
        NativeEdgeDriver | None: ドライバーインスタンス（失敗時はNone）
    """
    print_section("Edgeブラウザに接続")

    try:
        driver = NativeEdgeDriver(retries=2, start_if_not_found=False)
        print("  [OK] 接続完了")
        return driver
    except Exception as exc:
        print(f"  [ERROR] 接続失敗: {exc}")
        return None


# ================================================================================
# ステップ3: 現在表示中の添付ファイル情報をスキャン
# ================================================================================

def scan_current_attachment_info(driver: NativeEdgeDriver) -> int:
    """
    現在表示されている添付ファイルの数を取得（「文書」種類を除外）

    Args:
        driver: NativeEdgeDriver インスタンス

    Returns:
        int: 添付ファイル数（エラー時は-1）
    """
    print_section("添付ファイル情報をスキャン")

    try:
        # 全要素をスキャン
        print_step("要素をスキャン中...")
        driver.scan_page_elements(
            max_elements=500,
            foreground=True,
            settle_ms=100,
        )

        # CheckBoxの数をカウント（全選択用1個 + ファイル数）
        driver.filter_current_elements(
            control_types="CheckBox",
            output="simple",
            overwrite=True,
        )

        checkbox_count = len(driver.current_elements)

        if checkbox_count <= 1:
            # CheckBoxが0個または1個（全選択のみ） → 添付ファイルなし
            file_count = 0
        else:
            # 「文書」種類を除外してカウント
            checkbox_indices = sorted(driver.current_elements.keys())
            file_count = 0

            for idx in checkbox_indices[1:]:  # 最初のCheckBox（all_checkbox）をスキップ
                elem_wrapper = driver.current_elements[idx]
                try:
                    name = elem_wrapper.window_text()
                    # 「文書」種類を除外
                    if "文書" not in name:
                        file_count += 1
                except Exception:
                    # 名前が取得できない場合はカウントに含める
                    file_count += 1

        print(f"  [OK] 添付ファイル: {file_count}件（「文書」種類を除く）")
        return file_count

    except Exception as exc:
        print(f"  [ERROR] スキャン失敗: {exc}")
        return -1


# ================================================================================
# ユーティリティ: ダイアログ・通知を閉じる
# ================================================================================

def dismiss_message_dialog(driver: NativeEdgeDriver) -> bool:
    """
    「Webページからのメッセージ」ダイアログのOKボタンを押す

    Args:
        driver: NativeEdgeDriver インスタンス

    Returns:
        bool: 成功したか（ダイアログがない場合もTrue）
    """
    try:
        # Button要素をスキャン
        driver.scan_page_elements(
            control_type="Button",
            max_elements=50,
            foreground=True,
            settle_ms=100,
        )

        # OKボタンを検索
        driver.filter_current_elements(
            name_regex="OK",
            output="simple",
            overwrite=True,
        )

        if not driver.current_elements:
            # OKボタンがなければダイアログが出ていない
            return True

        # OKボタンをクリック
        ok_button_idx = min(driver.current_elements.keys())
        driver.click_by_index(ok_button_idx)
        time.sleep(0.3)
        print("    [INFO] メッセージダイアログを閉じました")
        return True

    except Exception as exc:
        print(f"    [WARNING] ダイアログ処理で例外: {exc}")
        return True  # 失敗しても続行


def close_download_notifications(driver: NativeEdgeDriver) -> bool:
    """
    「ダウンロードが完了しました」通知の×ボタンを全て押す

    Args:
        driver: NativeEdgeDriver インスタンス

    Returns:
        bool: 成功したか
    """
    try:
        # Button要素をスキャン
        driver.scan_page_elements(
            control_type="Button",
            max_elements=100,
            foreground=True,
            settle_ms=100,
        )

        # Closeボタンを検索（AutomationId="Close" または 名前が空で×の役割）
        close_buttons = []
        for idx, elem_wrapper in driver.current_elements.items():
            try:
                # AutomationIdがCloseのボタンを探す
                automation_id = elem_wrapper.element_info.automation_id
                if automation_id and "Close" in automation_id:
                    close_buttons.append(idx)
            except Exception:
                continue

        if not close_buttons:
            # Closeボタンがなければ通知が出ていない
            return True

        # 全てのCloseボタンをクリック
        for idx in close_buttons:
            try:
                driver.click_by_index(idx)
                time.sleep(0.2)
            except Exception:
                continue

        print(f"    [INFO] {len(close_buttons)}個のダウンロード通知を閉じました")
        return True

    except Exception as exc:
        print(f"    [WARNING] 通知クローズで例外: {exc}")
        return True  # 失敗しても続行


# ================================================================================
# ステップ4: 添付ファイルをダウンロード
# ================================================================================

def download_attachments(driver: NativeEdgeDriver, file_count: int) -> bool:
    """
    添付ファイルをダウンロード

    Args:
        driver: NativeEdgeDriver インスタンス
        file_count: 添付ファイル数

    Returns:
        bool: ダウンロード成功したか
    """
    print_section(f"添付ファイルをダウンロード ({file_count}件)")

    if file_count == 0:
        print("  [-] 添付ファイルなし。スキップします")
        return True  # スキップは成功扱い

    try:
        # 4-0. 処理開始時のダイアログを閉じる
        print_step("0. メッセージダイアログをチェック...")
        dismiss_message_dialog(driver)

        # 4-1. CheckBoxをスキャン
        print_step("1. CheckBox要素をスキャン中...")
        driver.scan_page_elements(
            control_type="CheckBox",
            max_elements=50,
            foreground=True,
            settle_ms=100,
        )

        if not driver.current_elements:
            print("    [ERROR] CheckBoxが見つかりません")
            return False

        # 4-2. CheckBoxを個別にチェック（all_checkboxと「文書」種類を除外）
        print_step("2. CheckBoxを個別にチェック中...")
        checkbox_indices = sorted(driver.current_elements.keys())

        # 最初のCheckBoxはall_checkboxとして除外
        all_checkbox_idx = checkbox_indices[0] if checkbox_indices else None
        print(f"    [INFO] all_checkbox (index={all_checkbox_idx}) をスキップ")

        checked_count = 0
        for idx in checkbox_indices[1:]:  # 最初のCheckBoxをスキップ
            elem_wrapper = driver.current_elements[idx]
            try:
                # 要素名を取得
                name = elem_wrapper.window_text()

                # 「文書」種類を除外
                if "文書" in name:
                    print(f"    [SKIP] index={idx}, name='{name}' (文書種類)")
                    continue

                # トグル状態を確認
                toggle_state = elem_wrapper.get_toggle_state()

                # 未チェックならクリック
                if toggle_state != 1:  # 1 = チェック済み
                    driver.click_by_index(idx)
                    checked_count += 1
                    print(f"    [CHECK] index={idx}, name='{name}'")
                    time.sleep(0.1)
                else:
                    print(f"    [INFO] index={idx}, name='{name}' (既にチェック済み)")

            except Exception as exc:
                print(f"    [WARNING] index={idx} の処理で例外: {exc}")
                continue

        print(f"    [OK] {checked_count}個のCheckBoxをチェックしました")
        time.sleep(0.5)

        # 4-3. Button要素をスキャン
        print_step("3. Button要素をスキャン中...")
        driver.scan_page_elements(
            control_type="Button",
            max_elements=100,
            foreground=True,
            settle_ms=100,
        )

        # 4-4. 「表示」ボタンでフィルタリング
        print_step("4. 「表示」ボタンを検索中...")
        driver.filter_current_elements(
            name_regex="表示",
            output="simple",
            overwrite=True,
        )

        # 正確に「表示」という名前のボタンを探す
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
            print("    [ERROR] 「表示」ボタンが見つかりません")
            return False

        # 4-5. 「表示」ボタンをクリック
        print_step(f"5. 「表示」ボタンをクリック (index={display_button_idx})...")
        driver.click_by_index(display_button_idx)
        time.sleep(1.5)  # ダウンロードダイアログ待機

        # 4-5-1. 「表示」ボタンクリック後のダイアログを閉じる
        print_step("5-1. メッセージダイアログをチェック...")
        dismiss_message_dialog(driver)

        # 4-6. SplitButton要素をスキャン
        print_step("6. SplitButton要素をスキャン中...")
        driver.scan_page_elements(
            control_type="SplitButton",
            max_elements=50,
            foreground=True,
            settle_ms=100,
        )

        # 4-7. 「保存」ボタンでフィルタリング
        print_step("7. 「保存」ボタンを検索中...")
        driver.filter_current_elements(
            name_regex="保存",
            output="simple",
            overwrite=True,
        )

        if not driver.current_elements:
            print("    [ERROR] 「保存」ボタンが見つかりません")
            return False

        # 4-8. 「保存」ボタンをクリック
        save_button_idx = min(driver.current_elements.keys())
        print_step(f"8. 「保存」ボタンをクリック (index={save_button_idx})...")
        driver.click_by_index(save_button_idx)
        time.sleep(2)  # ダウンロード完了待機

        # 4-9. ダウンロード完了通知を閉じる
        print_step("9. ダウンロード完了通知を閉じる...")
        close_download_notifications(driver)

        print("  [OK] ダウンロード完了")
        return True

    except Exception as exc:
        print(f"  [ERROR] ダウンロード失敗: {exc}")
        return False


# ================================================================================
# ステップ5: 最新のZIPファイルを検索
# ================================================================================

def find_latest_zip(downloads_dir: str) -> Optional[Path]:
    """
    ダウンロードフォルダ内の最新のZIPファイルを検索

    Args:
        downloads_dir: ダウンロードディレクトリパス

    Returns:
        Path | None: ZIPファイルのパス（見つからない場合はNone）
    """
    downloads_path = Path(downloads_dir)
    zip_files = sorted(downloads_path.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)

    if zip_files:
        return zip_files[0]
    else:
        return None


# ================================================================================
# ステップ6: ZIPファイルを展開して削除
# ================================================================================

def extract_and_delete_zip(downloads_dir: str, file_count: int) -> bool:
    """
    ダウンロードされたZIPファイルを展開して削除

    Args:
        downloads_dir: ダウンロードディレクトリパス
        file_count: 添付ファイル数（2件以上でZIP、1件で単一ファイル、0件でスキップ）

    Returns:
        bool: 成功したか
    """
    print_section("ZIPファイルを展開・削除")

    # ファイル数に応じた処理
    if file_count == 0:
        print("  [-] 添付ファイルなし。スキップします")
        return True

    if file_count == 1:
        print("  [-] 単一ファイルのため、ZIP展開不要")
        return True

    # 2件以上 → ZIP形式
    try:
        # 最新のZIPファイルを検索
        print_step("最新のZIPファイルを検索中...")
        zip_file = find_latest_zip(downloads_dir)

        if not zip_file:
            print("    [ERROR] ZIPファイルが見つかりません")
            return False

        print(f"    見つかりました: {zip_file.name}")

        # ZIPを展開
        print_step(f"ZIPファイルを展開中: {zip_file.name}")
        ps_command = f"Expand-Archive -Path '{zip_file}' -DestinationPath '{downloads_dir}' -Force"

        result = subprocess.run(
            ["powershell.exe", "-Command", ps_command],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"    [ERROR] 展開失敗: {result.stderr}")
            return False

        print("    [OK] 展開完了")

        # ZIPファイルを削除
        print_step(f"ZIPファイルを削除中: {zip_file.name}")
        try:
            zip_file.unlink()
            print("    [OK] 削除完了")
        except Exception as exc:
            print(f"    [ERROR] 削除失敗: {exc}")
            return False

        print("  [OK] ZIP処理完了")
        return True

    except Exception as exc:
        print(f"  [ERROR] 例外が発生: {exc}")
        return False


# ================================================================================
# ステップ7: 添付表示を切り替え
# ================================================================================

def switch_attachment_view(driver: NativeEdgeDriver) -> bool:
    """
    添付表示切り替えボタンをクリック

    Args:
        driver: NativeEdgeDriver インスタンス

    Returns:
        bool: 成功したか
    """
    print_section("添付表示を切り替え")

    try:
        # Button要素をスキャン
        print_step("Button要素をスキャン中...")
        driver.scan_page_elements(
            control_type="Button",
            max_elements=100,
            foreground=True,
            settle_ms=100,
        )

        # 「添付表示」ボタンでフィルタリング
        print_step("「添付表示」ボタンを検索中...")
        driver.filter_current_elements(
            name_regex="添付表示",
            output="simple",
            overwrite=True,
        )

        if not driver.current_elements:
            print("    [ERROR] 切り替えボタンが見つかりません")
            return False

        # 切り替えボタンをクリック
        switch_button_idx = min(driver.current_elements.keys())
        print_step(f"切り替えボタンをクリック (index={switch_button_idx})...")
        driver.click_by_index(switch_button_idx)
        time.sleep(1.5)  # 画面更新待機

        print("  [OK] 切り替え完了")
        return True

    except Exception as exc:
        print(f"  [ERROR] 切り替え失敗: {exc}")
        return False


# ================================================================================
# コンダクター関数: 全体の流れを制御
# ================================================================================

def main_conductor(downloads_dir: str = r"C:\Users\sa11882\Downloads") -> int:
    """
    メインのコンダクター関数
    各ステップを順番に実行し、エラーハンドリングを行う

    Args:
        downloads_dir: ダウンロードディレクトリパス

    Returns:
        int: 終了コード（0=成功、1=失敗）
    """
    print("=" * 80)
    print("決裁ファイル一括ダウンロードスクリプト v2")
    print("=" * 80)

    # ステップ1: ダウンロードフォルダをクリア
    if not clear_download_folder(downloads_dir):
        print("\n[ERROR] ダウンロードフォルダのクリアに失敗しました")
        return 1

    # ステップ2: ブラウザに接続
    driver = connect_to_browser()
    if driver is None:
        print("\n[ERROR] ブラウザへの接続に失敗しました")
        return 1

    # ステップ2-1: ブラウザ接続直後のダイアログをチェック
    print_section("初期ダイアログをチェック")
    dismiss_message_dialog(driver)

    # ステップ3: 1回目 - 現在表示中の添付ファイル情報をスキャン
    file_count_1 = scan_current_attachment_info(driver)
    if file_count_1 < 0:
        print("\n[ERROR] 添付ファイル情報のスキャンに失敗しました")
        return 1

    # ステップ4: 1回目 - 添付ファイルをダウンロード
    if not download_attachments(driver, file_count_1):
        print("\n[ERROR] 1回目のダウンロードに失敗しました")
        return 1

    # ステップ5: 1回目 - ZIPファイルを展開・削除
    if not extract_and_delete_zip(downloads_dir, file_count_1):
        print("\n[ERROR] 1回目のZIP処理に失敗しました")
        return 1

    # ステップ6: 添付表示を切り替え
    if not switch_attachment_view(driver):
        print("\n[ERROR] 添付表示の切り替えに失敗しました")
        return 1

    # ステップ7: 2回目 - 切り替え後の添付ファイル情報をスキャン
    file_count_2 = scan_current_attachment_info(driver)
    if file_count_2 < 0:
        print("\n[ERROR] 切り替え後の添付ファイル情報のスキャンに失敗しました")
        return 1

    # ステップ8: 2回目 - 添付ファイルをダウンロード
    if not download_attachments(driver, file_count_2):
        print("\n[ERROR] 2回目のダウンロードに失敗しました")
        return 1

    # ステップ9: 2回目 - ZIPファイルを展開・削除
    if not extract_and_delete_zip(downloads_dir, file_count_2):
        print("\n[ERROR] 2回目のZIP処理に失敗しました")
        return 1

    # 完了サマリー
    print_section("処理完了")
    print(f"  1回目: {file_count_1}件のファイルをダウンロード")
    print(f"  2回目: {file_count_2}件のファイルをダウンロード")
    print(f"  合計: {file_count_1 + file_count_2}件")
    print("=" * 80)

    return 0


# ================================================================================
# エントリーポイント
# ================================================================================


def cli() -> int:
    parser = argparse.ArgumentParser(description="決裁ファイルを段階的にダウンロード (v2)")
    add_output_argument(parser)
    args = parser.parse_args()

    exit_code = 0

    def _task() -> None:
        nonlocal exit_code
        exit_code = main_conductor()

    route_output(_task, args.output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(cli())
