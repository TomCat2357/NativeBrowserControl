#%%
import sys
import time
import io
import re
import ctypes
import subprocess
from dataclasses import dataclass
from typing import Optional, Literal, Union, Iterable, List

from pywinauto import Desktop, Application
from pywinauto.keyboard import send_keys

import win32con
import win32gui
import win32ui
import win32clipboard
import win32process
from PIL import Image
import mss

from pywinauto.findwindows import find_windows

desktop = Desktop(backend="uia")

# ブラウザ別設定
BROWSER_CONFIG = {
    "chrome": {
        "title_keywords": ["Chrome", "Google Chrome"],
        "title_regex": ".*Google Chrome.*",
        "start_command": ["start", "chrome"],
        "exe_name": "chrome.exe",
    },
    "edge": {
        "title_keywords": ["Edge", "Microsoft Edge"],
        "title_regex": ".*Microsoft.*Edge.*",
        "start_command": ["start", "msedge"],
        "exe_name": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    },
}


def _match_browser_window(
    window,
    *,
    keywords: list[str],
    title_re: Optional[str],
    require_visible: bool,
    require_enabled: bool,
    exclude_minimized: bool,
    class_name: Optional[str],
    window_predicate,
    exe_filter: Optional[str],
) -> bool:
    """ブラウザウィンドウ探索用の共通フィルター。"""
    title = window.window_text() or ""

    if exclude_minimized:
        try:
            if win32gui.IsIconic(window.handle):
                return False
        except Exception:
            return False

    if require_visible:
        try:
            if not window.is_visible():
                return False
        except Exception:
            return False

    if require_enabled:
        try:
            if not window.is_enabled():
                return False
        except Exception:
            return False

    if class_name:
        try:
            if window.class_name() != class_name:
                return False
        except Exception:
            return False

    keyword_hit = any(kw in title for kw in keywords) if keywords else False
    regex_hit = bool(re.search(title_re, title)) if title_re else False
    if not keyword_hit and not regex_hit:
        return False

    if exe_filter:
        try:
            pid = window.process_id()
            image_path = _get_process_image_path(pid)
            if image_path:
                lowered_path = image_path.lower()
                lowered_filter = exe_filter.lower()
                if lowered_filter not in lowered_path and not lowered_path.endswith(lowered_filter):
                    return False
        except Exception:
            return False

    if window_predicate and not window_predicate(window):
        return False

    return True


def find_browser_windows(
    browser: str = "chrome",
    *,
    extra_title_keywords: Optional[Iterable[str]] = None,
    title_regex: Optional[str] = None,
    require_visible: bool = False,
    require_enabled: bool = False,
    exclude_minimized: bool = False,
    class_name: Optional[str] = None,
    control_type: str = "Window",
    window_predicate=None,
    exe_name: Optional[str] = None,
    retries: int = 1,
) -> List:
    """
    指定ブラウザの起動中ウィンドウを列挙する。

    追加条件:
        - extra_title_keywords: タイトル部分一致の追加キーワード
        - title_regex: タイトル正規表現（既定の title_regex を上書き）
        - require_visible: 可視ウィンドウのみ
        - require_enabled: 有効ウィンドウのみ
        - exclude_minimized: 最小化されたウィンドウを除外
        - class_name: Win32 クラス名で絞り込み
        - control_type: Desktop.windows の control_type
        - window_predicate: callable(window) -> bool で任意絞り込み
        - exe_name: 実行ファイル名/パスに含まれる文字列で絞り込み
        - retries: 探索リトライ回数
    """
    config = BROWSER_CONFIG.get(browser)
    if not config:
        raise ValueError(f"Unsupported browser: {browser}. Supported: {list(BROWSER_CONFIG.keys())}")

    keywords = list(config["title_keywords"]) + list(extra_title_keywords or [])
    title_re = title_regex or config.get("title_regex")
    exe_filter = exe_name or config.get("exe_name")
    retries = max(1, int(retries))

    for attempt in range(retries):
        matches = [
            w
            for w in desktop.windows(control_type=control_type)
            if _match_browser_window(
                w,
                keywords=keywords,
                title_re=title_re,
                require_visible=require_visible,
                require_enabled=require_enabled,
                exclude_minimized=exclude_minimized,
                class_name=class_name,
                window_predicate=window_predicate,
                exe_filter=exe_filter,
            )
        ]
        if matches:
            return matches
        if attempt < retries - 1:
            time.sleep(1)
    return []


def get_browser_window(
    browser: str = "chrome",
    *,
    extra_title_keywords: Optional[Iterable[str]] = None,
    title_regex: Optional[str] = None,
    require_visible: bool = False,
    require_enabled: bool = False,
    exclude_minimized: bool = False,
    class_name: Optional[str] = None,
    control_type: str = "Window",
    window_predicate=None,
    exe_name: Optional[str] = None,
    retries: int = 3,
    start_if_not_found: bool = False,
):
    """
    指定ブラウザのウィンドウを取得（既存ウィンドウのみ）。

    起動されていない場合は例外を投げる。start_if_not_found=True の場合のみ起動を試みる。
    """
    config = BROWSER_CONFIG.get(browser)
    if not config:
        raise ValueError(f"Unsupported browser: {browser}. Supported: {list(BROWSER_CONFIG.keys())}")

    matches = find_browser_windows(
        browser,
        extra_title_keywords=extra_title_keywords,
        title_regex=title_regex,
        require_visible=require_visible,
        require_enabled=require_enabled,
        exclude_minimized=exclude_minimized,
        class_name=class_name,
        control_type=control_type,
        window_predicate=window_predicate,
        exe_name=exe_name,
        retries=retries,
    )

    if matches:
        return matches[0]

    if start_if_not_found:
        subprocess.Popen(config["start_command"], shell=True)
        time.sleep(1)
        matches = find_browser_windows(
            browser,
            extra_title_keywords=extra_title_keywords,
            title_regex=title_regex,
            require_visible=require_visible,
            require_enabled=require_enabled,
            exclude_minimized=exclude_minimized,
            class_name=class_name,
            control_type=control_type,
            window_predicate=window_predicate,
            exe_name=exe_name,
            retries=retries,
        )
        if matches:
            return matches[0]

    raise RuntimeError(f"{browser.capitalize()} Window Not Found.")


def _build_window_info(window, browser: str) -> BrowserWindowInfo:
    try:
        pid = window.process_id()
    except Exception:
        pid = -1
    try:
        title = window.window_text() or ""
    except Exception:
        title = ""
    try:
        is_visible = bool(window.is_visible())
    except Exception:
        is_visible = False
    try:
        is_minimized = bool(win32gui.IsIconic(window.handle))
    except Exception:
        is_minimized = False

    return BrowserWindowInfo(
        browser=browser,
        title=title,
        pid=pid,
        handle=int(window.handle),
        is_visible=is_visible,
        is_minimized=is_minimized,
    )


def list_running_browser_drivers(
    browser: Optional[str] = None,
    *,
    require_visible: bool = False,
    exclude_minimized: bool = False,
    retries: int = 1,
) -> list[BrowserWindowInfo]:
    """起動中のブラウザドライバ一覧を取得する。"""

    targets = [browser] if browser else list(BROWSER_CONFIG.keys())
    results: list[BrowserWindowInfo] = []

    for b in targets:
        matches = find_browser_windows(
            b,
            require_visible=require_visible,
            exclude_minimized=exclude_minimized,
            retries=retries,
        )
        results.extend(_build_window_info(w, b) for w in matches)

    return results


def launch_browser_driver(
    browser: str = "chrome", *, retries: int = 5, start_delay: float = 1.0
) -> "NativeBrowserDriver":
    """ブラウザを起動してドライバーを返す。"""

    config = BROWSER_CONFIG.get(browser)
    if not config:
        raise ValueError(f"Unsupported browser: {browser}. Supported: {list(BROWSER_CONFIG.keys())}")

    subprocess.Popen(config["start_command"], shell=True)
    time.sleep(start_delay)
    return NativeBrowserDriver(browser=browser, retries=retries, start_if_not_found=False)


# -----------------------------
# DPI awareness (座標ズレ対策)
# -----------------------------
def _enable_dpi_awareness() -> None:
    try:
        DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = -4
        ctypes.windll.user32.SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
        return
    except Exception:
        pass

    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


def _set_clipboard_text(text: str) -> None:
    """クリップボードにテキストをセットする"""
    win32clipboard.OpenClipboard()
    try:
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardData(win32con.CF_UNICODETEXT, text)
    finally:
        win32clipboard.CloseClipboard()


@dataclass(frozen=True)
class Rect:
    left: int
    top: int
    right: int
    bottom: int

    @property
    def width(self) -> int:
        return max(0, self.right - self.left)

    @property
    def height(self) -> int:
        return max(0, self.bottom - self.top)


def _get_window_rect(hwnd: int) -> Rect:
    l, t, r, b = win32gui.GetWindowRect(hwnd)
    return Rect(l, t, r, b)


@dataclass(frozen=True)
class BrowserWindowInfo:
    browser: str
    title: str
    pid: int
    handle: int
    is_visible: bool
    is_minimized: bool

    def to_dict(self) -> dict[str, Union[str, int, bool]]:
        return {
            "browser": self.browser,
            "title": self.title,
            "pid": self.pid,
            "handle": self.handle,
            "is_visible": self.is_visible,
            "is_minimized": self.is_minimized,
        }


def _get_process_image_path(pid: int) -> Optional[str]:
    """プロセスの実行ファイルパスを取得（失敗時は None）"""
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    handle = None
    try:
        handle = win32process.OpenProcess(PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, pid)
        try:
            return win32process.GetModuleFileNameEx(handle, 0)
        finally:
            ctypes.windll.kernel32.CloseHandle(handle)
    except Exception:
        if handle:
            ctypes.windll.kernel32.CloseHandle(handle)
        return None


def _is_probably_blank(img: Image.Image) -> bool:
    if img.mode != "RGB":
        img = img.convert("RGB")
    small = img.resize((64, 64))
    px = list(small.getdata())

    r = [p[0] for p in px]
    g = [p[1] for p in px]
    b = [p[2] for p in px]

    def var(a):
        m = sum(a) / len(a)
        return sum((x - m) ** 2 for x in a) / len(a)

    return (var(r) + var(g) + var(b)) < 2.0


def _capture_by_printwindow(hwnd: int) -> Image.Image:
    rect = _get_window_rect(hwnd)
    w, h = rect.width, rect.height
    if w <= 0 or h <= 0:
        raise RuntimeError("Window size is invalid (w/h <= 0).")

    hwnd_dc = win32gui.GetWindowDC(hwnd)
    mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
    save_dc = mfc_dc.CreateCompatibleDC()

    bmp = win32ui.CreateBitmap()
    bmp.CreateCompatibleBitmap(mfc_dc, w, h)
    save_dc.SelectObject(bmp)

    # 0=default, 2=PW_RENDERFULLCONTENT（Chromeでは不安定な場合あり）
    flags = 2
    result = ctypes.windll.user32.PrintWindow(hwnd, save_dc.GetSafeHdc(), flags)

    bmpinfo = bmp.GetInfo()
    bmpstr = bmp.GetBitmapBits(True)

    img = Image.frombuffer(
        "RGB",
        (bmpinfo["bmWidth"], bmpinfo["bmHeight"]),
        bmpstr,
        "raw",
        "BGRX",
        0,
        1,
    )

    win32gui.DeleteObject(bmp.GetHandle())
    save_dc.DeleteDC()
    mfc_dc.DeleteDC()
    win32gui.ReleaseDC(hwnd, hwnd_dc)

    if result != 1:
        raise RuntimeError("PrintWindow failed (returned 0).")

    return img


def _capture_by_screen_rect(rect: Rect) -> Image.Image:
    if rect.width <= 0 or rect.height <= 0:
        raise RuntimeError("Rect size is invalid (width/height <= 0).")

    with mss.mss() as sct:
        monitor = {"left": rect.left, "top": rect.top, "width": rect.width, "height": rect.height}
        shot = sct.grab(monitor)
        return Image.frombytes("RGB", shot.size, shot.rgb)


def _force_foreground(hwnd: int) -> None:
    try:
        win32gui.BringWindowToTop(hwnd)
    except Exception:
        pass

    try:
        fg = win32gui.GetForegroundWindow()
        if fg:
            current_tid = win32gui.GetWindowThreadProcessId(fg)[0]
            target_tid = win32gui.GetWindowThreadProcessId(hwnd)[0]
            my_tid = ctypes.windll.kernel32.GetCurrentThreadId()

            ctypes.windll.user32.AttachThreadInput(my_tid, current_tid, True)
            ctypes.windll.user32.AttachThreadInput(my_tid, target_tid, True)
            try:
                win32gui.SetForegroundWindow(hwnd)
            finally:
                ctypes.windll.user32.AttachThreadInput(my_tid, target_tid, False)
                ctypes.windll.user32.AttachThreadInput(my_tid, current_tid, False)
        else:
            win32gui.SetForegroundWindow(hwnd)
    except Exception:
        try:
            win32gui.BringWindowToTop(hwnd)
        except Exception:
            pass


class NativeBrowserDriver:
    """Chrome/Edge共通の基底クラス"""

    def __init__(
        self,
        browser: str = "chrome",
        *,
        extra_title_keywords: Optional[Iterable[str]] = None,
        title_regex: Optional[str] = None,
        require_visible: bool = False,
        require_enabled: bool = False,
        exclude_minimized: bool = False,
        class_name: Optional[str] = None,
        control_type: str = "Window",
        window_predicate=None,
        exe_name: Optional[str] = None,
        retries: int = 3,
        start_if_not_found: bool = False,
    ):
        if browser not in BROWSER_CONFIG:
            raise ValueError(f"Unsupported browser: {browser}. Supported: {list(BROWSER_CONFIG.keys())}")

        self.browser = browser
        self._config = BROWSER_CONFIG[browser]
        _enable_dpi_awareness()
        
        self.current_elements = {}
        self.app = None
        self.window = None

        # 1. まずウィンドウを確実に取得する（なければ起動も含めて get_browser_window が担当）
        found_window = get_browser_window(
            browser,
            extra_title_keywords=extra_title_keywords,
            title_regex=title_regex,
            require_visible=require_visible,
            require_enabled=require_enabled,
            exclude_minimized=exclude_minimized,
            class_name=class_name,
            control_type=control_type,
            window_predicate=window_predicate,
            exe_name=exe_name,
            retries=retries,
            start_if_not_found=start_if_not_found,
        )
        
        # 2. 取得したウィンドウ情報を元に接続する
        self.connect(found_window)

    def connect(self, target_window):
        """特定されたウィンドウのPIDとハンドルを使って確実に接続する"""

        # プロセスID (PID) を使ってアプリケーションに接続
        # これにより、同じタイトルの別ウィンドウがあっても正しいプロセスを掴める
        pid = target_window.process_id()
        self.app = Application(backend="uia").connect(process=pid)

        # ウィンドウハンドル (HWND) を使ってウィンドウオブジェクトを生成
        # これにより、ElementAmbiguousError（候補が複数あるエラー）を完全に回避できる
        self.window = self.app.window(handle=target_window.handle)
        
        self.window.wait("visible", timeout=20)
        print(f"Connected to {self.browser.capitalize()} (PID: {pid}).")


    @property
    def hwnd(self) -> int:
        return int(self.window.handle)

    def ensure_visible(
        self,
        maximize: bool = True,
        foreground: bool = True,
        settle_ms: int = 150,
    ) -> None:
        """撮影・操作の成功率を上げるために復帰/最大化/前面化する"""
        hwnd = self.hwnd
        if not win32gui.IsWindow(hwnd):
            raise RuntimeError("Invalid hwnd (window does not exist).")

        try:
            if win32gui.IsIconic(hwnd):
                win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
        except Exception:
            pass

        if maximize:
            try:
                win32gui.ShowWindow(hwnd, win32con.SW_MAXIMIZE)
            except Exception:
                pass

        if foreground:
            _force_foreground(hwnd)

        if settle_ms > 0:
            time.sleep(settle_ms / 1000.0)
    
    def set_edit_text(self, index: int, text: str) -> str:
        """スキャンした要素のテキストを設定する"""
        if index not in self.current_elements:
            return f"Index {index} not found"

        elem = self.current_elements[index]

        try:
            elem.set_text(text)
            return f"Set text for index {index}: {text[:50]}{'...' if len(text) > 50 else ''}"
        except Exception as e:
            return f"Failed to set text for index {index}: {e}"

    def screenshot(
        self,
        file_path: Optional[str] = None,
        *,
        prefer: Literal["printwindow", "screen"] = "printwindow",
        allow_fallback: bool = True,
        prepare_window: bool = True,
        maximize_before: bool = True,
        foreground_before: bool = True,
        settle_ms: int = 150,
        as_bytes: bool = False,
        fmt: Literal["PNG", "JPEG"] = "PNG",
        quality: int = 90,
    ) -> Union[Image.Image, bytes]:
        """
        Chromeデバッグモードなしのスクショ（ウィンドウ全体）。
        - prefer='printwindow' : PrintWindow優先（隠れていても取れる場合あり。ただしChromeは黒画面になることがある）
        - prefer='screen'      : 画面キャプチャ優先（最も安定しがちだが、ウィンドウが見えている必要あり）
        """
        if prepare_window:
            self.ensure_visible(
                maximize=maximize_before,
                foreground=foreground_before,
                settle_ms=settle_ms,
            )

        hwnd = self.hwnd
        rect = _get_window_rect(hwnd)

        img: Optional[Image.Image] = None
        errors = []

        def try_printwindow() -> bool:
            nonlocal img
            try:
                im = _capture_by_printwindow(hwnd)
                if _is_probably_blank(im):
                    raise RuntimeError("PrintWindow returned a blank image (probable GPU/occlusion issue).")
                img = im
                return True
            except Exception as e:
                errors.append(f"printwindow: {e}")
                return False

        def try_screen() -> bool:
            nonlocal img
            try:
                img = _capture_by_screen_rect(rect)
                return True
            except Exception as e:
                errors.append(f"screen: {e}")
                return False

        if prefer == "printwindow":
            ok = try_printwindow()
            if (not ok) and allow_fallback:
                ok = try_screen()
        else:
            ok = try_screen()
            if (not ok) and allow_fallback:
                ok = try_printwindow()

        if not img:
            raise RuntimeError("Failed to capture screenshot. " + " | ".join(errors))

        if file_path:
            save_kwargs = {}
            if fmt == "JPEG":
                save_kwargs["quality"] = int(quality)
                save_kwargs["optimize"] = True
            img.save(file_path, format=fmt, **save_kwargs)

        if as_bytes:
            buf = io.BytesIO()
            save_kwargs = {}
            if fmt == "JPEG":
                save_kwargs["quality"] = int(quality)
                save_kwargs["optimize"] = True
            img.save(buf, format=fmt, **save_kwargs)
            return buf.getvalue()

        return img

    def navigate(self, url: str):
        """Ctrl+LでURLバーにフォーカスし、クリップボード経由で入力して移動"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^l")
        time.sleep(0.1)
        _set_clipboard_text(url)
        send_keys("^v")
        time.sleep(0.1)
        send_keys("{ENTER}")
        time.sleep(1)

    def get_address_bar_url(self):
        """アドレスバーからURLを取得"""
        try:
            address_bar = self.window.descendants(control_type="Edit", title="Address and search bar")[0]
            return address_bar.get_value()
        except Exception:
            edits = self.window.descendants(control_type="Edit")
            if edits:
                try:
                    return edits[0].get_value()
                except Exception:
                    pass
            return "Unknown"

    def scan_page_elements(
        self,
        control_type=None,
        max_elements=500,
        *,
        name_contains: Optional[Union[str, Iterable[str]]] = None,
        name_regex: Optional[str] = None,
        class_name: Optional[str] = None,
        only_visible: bool = False,
        require_enabled: bool = False,
        min_width: int = 0,
        min_height: int = 0,
        only_focusable: bool = False,
        start_index: int = 0,
        end_index: Optional[int] = None,
        automation_id: Optional[Union[str, Iterable[str]]] = None,
    ):
        """
        現在のページの主要要素をリストアップ（発見順にインデックスを付与）。

        追加条件:
            - name_contains: 部分一致（str または Iterable[str]）
            - name_regex: タイトル/ラベルの正規表現
            - class_name: friendly_class_name() で一致
            - only_visible: 可視要素のみ
            - require_enabled: 有効要素のみ
            - min_width / min_height: サイズ下限（px）
            - only_focusable: キーボードフォーカス可能なもののみ
            - start_index / end_index: 条件を満たしたものの発見順インデックス範囲で出力（0-based, end は inclusive）
            - automation_id: automation_id で一致（str または Iterable[str]）
        """
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()

        elements_map = {}
        text_output = []
        matched_index = 0

        contains_list = None
        if name_contains:
            contains_list = [name_contains] if isinstance(name_contains, str) else list(name_contains)

        automation_id_list = None
        if automation_id:
            automation_id_list = [automation_id] if isinstance(automation_id, str) else list(automation_id)

        compiled_regex = re.compile(name_regex) if name_regex else None

        if control_type:
            all_items = self.window.descendants(control_type=control_type)
        else:
            all_items = self.window.descendants()

        for item in all_items:
            try:
                name = item.window_text()
                if not name:
                    continue

                rect = item.rectangle()
                if rect.height() <= min_height or rect.width() <= min_width:
                    continue

                if only_visible:
                    try:
                        if not item.is_visible():
                            continue
                    except Exception:
                        continue

                if require_enabled:
                    try:
                        if not item.is_enabled():
                            continue
                    except Exception:
                        continue

                if only_focusable:
                    try:
                        if not item.is_keyboard_focusable():
                            continue
                    except Exception:
                        continue

                if class_name:
                    try:
                        if item.friendly_class_name() != class_name:
                            continue
                    except Exception:
                        continue

                if contains_list and not any(sub in name for sub in contains_list):
                    continue

                if compiled_regex and not compiled_regex.search(name):
                    continue

                if automation_id_list:
                    try:
                        auto_id = item.element_info.automation_id
                        if auto_id is None or all(auto_id != aid for aid in automation_id_list):
                            continue
                    except Exception:
                        continue

                c_type = item.friendly_class_name()

                current_index = matched_index
                matched_index += 1

                if current_index < start_index:
                    continue
                if end_index is not None and current_index > end_index:
                    break

                elements_map[current_index] = item
                text_output.append(f"[{current_index}] <{c_type}> {name}")

                if len(elements_map) >= max_elements:
                    text_output.append("... (more elements truncated)")
                    break
            except Exception:
                continue

        self.current_elements = elements_map
        return "\n".join(text_output)

    def click_by_index(self, index):
        if index in self.current_elements:
            elem = self.current_elements[index]
            try:
                elem.invoke()
            except Exception:
                elem.click_input()
            return f"Clicked index {index}"
        return "Index not found"

    def select_all_and_get_text(self) -> str:
        """Ctrl+Aで全選択してCtrl+Cでクリップボードにコピーし、テキストを取得"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=100)
        self.window.set_focus()
        time.sleep(0.1)

        # Ctrl+A で全選択
        send_keys("^a")
        time.sleep(0.2)

        # Ctrl+C でコピー
        send_keys("^c")
        time.sleep(0.3)

        # クリップボードからテキストを取得
        try:
            win32clipboard.OpenClipboard()
            try:
                text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                return text
            except Exception as e:
                return f"Error getting clipboard data: {e}"
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            return f"Error opening clipboard: {e}"

    # ========================================
    # ページスクロール機能
    # ========================================

    def scroll_down(self, amount: int = 500) -> None:
        """指定したピクセル数だけ下にスクロール"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        for _ in range(amount // 100):
            send_keys("{DOWN}")
            time.sleep(0.01)

    def scroll_up(self, amount: int = 500) -> None:
        """指定したピクセル数だけ上にスクロール"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        for _ in range(amount // 100):
            send_keys("{UP}")
            time.sleep(0.01)

    def scroll_to_bottom(self) -> None:
        """ページの最下部までスクロール"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^{END}")
        time.sleep(0.2)

    def scroll_to_top(self) -> None:
        """ページの最上部までスクロール"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^{HOME}")
        time.sleep(0.2)

    def page_down(self) -> None:
        """Page Downキーでスクロール"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("{PGDN}")
        time.sleep(0.1)

    def page_up(self) -> None:
        """Page Upキーでスクロール"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("{PGUP}")
        time.sleep(0.1)

    # ========================================
    # テキスト入力・検索機能
    # ========================================

    def type_text(self, text: str, *, method: Literal["paste", "type"] = "paste") -> None:
        """
        フォーカス中の要素にテキストを入力。
        method="paste" でクリップボード経由のCtrl+V（デフォルト）、
        method="type" で一文字ずつ送信。
        """
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()

        if method == "paste":
            _set_clipboard_text(text)
            send_keys("^v")
        elif method == "type":
            send_keys(text, with_spaces=True)
        else:
            raise ValueError("method must be 'paste' or 'type'.")

        time.sleep(0.1)

    def find_text_on_page(self, search_text: str, *, method: Literal["paste", "type"] = "paste") -> None:
        """Ctrl+Fでページ内検索を開き、指定方式で入力"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^f")
        time.sleep(0.3)
        self.type_text(search_text, method=method)
        time.sleep(0.2)

    # ========================================
    # タブ操作機能
    # ========================================

    def new_tab(self) -> None:
        """新しいタブを開く (Ctrl+T)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^t")
        time.sleep(0.3)

    def close_tab(self) -> None:
        """現在のタブを閉じる (Ctrl+W)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^w")
        time.sleep(0.3)

    def next_tab(self) -> None:
        """次のタブに切り替え (Ctrl+Tab)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^{TAB}")
        time.sleep(0.2)

    def previous_tab(self) -> None:
        """前のタブに切り替え (Ctrl+Shift+Tab)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^+{TAB}")
        time.sleep(0.2)

    # ========================================
    # ブラウザ操作機能
    # ========================================

    def back(self) -> None:
        """戻る (Alt+←)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("%{LEFT}")
        time.sleep(0.5)

    def forward(self) -> None:
        """進む (Alt+→)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("%{RIGHT}")
        time.sleep(0.5)

    def refresh(self) -> None:
        """ページをリロード (F5)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("{F5}")
        time.sleep(0.5)

    def zoom_in(self) -> None:
        """ズームイン (Ctrl++)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^{+}")
        time.sleep(0.2)

    def zoom_out(self) -> None:
        """ズームアウト (Ctrl+-)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^{-}")
        time.sleep(0.2)

    def reset_zoom(self) -> None:
        """ズームをリセット (Ctrl+0)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^0")
        time.sleep(0.2)

    # ========================================
    # 待機・検証機能
    # ========================================

    def wait_for_idle(self, seconds: float = 2) -> None:
        """指定秒数待機"""
        time.sleep(seconds)

    def get_page_title(self) -> str:
        """現在のページタイトルを取得"""
        try:
            return self.window.window_text()
        except Exception as e:
            return f"Error getting title: {e}"

    # ========================================
    # ページソース取得
    # ========================================

    def get_page_source(self, *, wait_seconds: float = 1.5, close_after: bool = True, save_path: Optional[str] = None) -> str:
        """
        Ctrl+Uでソースビューを開き、全選択コピーしてHTMLを返す。
        close_after=Trueならソースビューのタブを閉じて元のタブに戻る。
        """
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^u")
        time.sleep(wait_seconds)

        source = self.select_all_and_get_text()

        if save_path and isinstance(source, str):
            with open(save_path, "w", encoding="utf-8") as f:
                f.write(source)

        if close_after:
            try:
                self.close_tab()
            except Exception:
                pass
            time.sleep(0.2)

        return source

    # ========================================
    # クリップボード操作拡張
    # ========================================

    def paste_from_clipboard(self) -> None:
        """クリップボードから貼り付け (Ctrl+V)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^v")
        time.sleep(0.2)

    def copy_selected_text(self) -> str:
        """選択済みのテキストをコピーして取得 (Ctrl+C)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^c")
        time.sleep(0.3)

        try:
            win32clipboard.OpenClipboard()
            try:
                text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                return text
            except Exception as e:
                return f"Error getting clipboard data: {e}"
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            return f"Error opening clipboard: {e}"

    def cut_text(self) -> str:
        """選択済みのテキストをカットして取得 (Ctrl+X)"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        send_keys("^x")
        time.sleep(0.3)

        try:
            win32clipboard.OpenClipboard()
            try:
                text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
                return text
            except Exception as e:
                return f"Error getting clipboard data: {e}"
            finally:
                win32clipboard.CloseClipboard()
        except Exception as e:
            return f"Error opening clipboard: {e}"

    # ========================================
    # 座標操作
    # ========================================

    def click_at_position(self, x: int, y: int) -> None:
        """指定座標をクリック（ウィンドウ相対座標）"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        self.window.click_input(coords=(x, y))
        time.sleep(0.2)

    def double_click_at_position(self, x: int, y: int) -> None:
        """指定座標をダブルクリック（ウィンドウ相対座標）"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        self.window.double_click_input(coords=(x, y))
        time.sleep(0.2)

    def right_click_at_position(self, x: int, y: int) -> None:
        """指定座標を右クリック（ウィンドウ相対座標）"""
        self.ensure_visible(maximize=False, foreground=True, settle_ms=80)
        self.window.set_focus()
        self.window.right_click_input(coords=(x, y))
        time.sleep(0.2)

    # ========================================
    # 全画面スクリーンショット
    # ========================================

    def capture_full_screen(
        self,
        file_path: Optional[str] = None,
        *,
        monitor: int = 0,
        as_bytes: bool = False,
        fmt: Literal["PNG", "JPEG"] = "PNG",
        quality: int = 90,
    ) -> Union[Image.Image, bytes]:
        """
        現在の画面全体を純粋にスクリーンショット（Chrome以外も含む全画面）。

        Args:
            file_path: 保存先パス（Noneの場合は保存しない）
            monitor: モニター番号（0=すべてのモニター、1=プライマリ、2=セカンダリ...）
            as_bytes: Trueの場合、バイト列で返す
            fmt: 画像フォーマット（"PNG"または"JPEG"）
            quality: JPEG品質（1-100）

        Returns:
            PIL.Image.Image または bytes
        """
        with mss.mss() as sct:
            # monitor=0 ですべてのモニター、1以降で個別モニター
            if monitor < 0 or monitor > len(sct.monitors) - 1:
                raise ValueError(f"Invalid monitor number: {monitor}. Available: 0-{len(sct.monitors) - 1}")

            shot = sct.grab(sct.monitors[monitor])
            img = Image.frombytes("RGB", shot.size, shot.rgb)

            if file_path:
                save_kwargs = {}
                if fmt == "JPEG":
                    save_kwargs["quality"] = int(quality)
                    save_kwargs["optimize"] = True
                img.save(file_path, format=fmt, **save_kwargs)

            if as_bytes:
                buf = io.BytesIO()
                save_kwargs = {}
                if fmt == "JPEG":
                    save_kwargs["quality"] = int(quality)
                    save_kwargs["optimize"] = True
                img.save(buf, format=fmt, **save_kwargs)
                return buf.getvalue()

            return img


class NativeChromeDriver(NativeBrowserDriver):
    """Chrome専用ドライバー（後方互換性のため）"""

    def __init__(self, *, retries: int = 3, start_if_not_found: bool = False):
        super().__init__(browser="chrome", retries=retries, start_if_not_found=start_if_not_found)


class NativeEdgeDriver(NativeBrowserDriver):
    """Microsoft Edge専用ドライバー"""

    def __init__(self, *, retries: int = 3, start_if_not_found: bool = False):
        super().__init__(browser="edge", retries=retries, start_if_not_found=start_if_not_found)


if __name__ == "__main__":
    # Chrome の例
    driver = NativeChromeDriver(start_if_not_found=True)
    driver.navigate("https://www.google.com")
    driver.screenshot(file_path="chrome.png", prefer="printwindow", allow_fallback=True)

    # Edge の例（コメント解除で実行可能）
    # edge_driver = NativeEdgeDriver()
    # edge_driver.navigate("https://www.google.com")
    # edge_driver.screenshot(file_path="edge.png", prefer="printwindow", allow_fallback=True)
