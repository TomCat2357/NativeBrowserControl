#%%
from __future__ import annotations
import sys
import time
import io
import re
import os
import ctypes
import subprocess
import logging
from dataclasses import dataclass
from typing import Any, Optional, Literal, Union, Iterable, List, Callable

from pywinauto import Desktop, Application, mouse
from pywinauto.keyboard import send_keys
import win32con
import win32gui
import win32ui
import win32clipboard
import win32process
from PIL import Image
import mss

from pywinauto.findwindows import find_windows

# ロガーの設定
# ロガーのフォーマット設定
logging.basicConfig(
    level=logging.INFO,  # 必要に応じて logging.DEBUG に変更
    format='%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.StreamHandler()  # コンソールに出力
        # logging.FileHandler("debug.log", encoding="utf-8") # ファイルに保存したい場合は有効化
    ]
)

logger = logging.getLogger(__name__)

logger = logging.getLogger(__name__)
logger.debug('Debug')

desktop = Desktop(backend="uia")


def _env_exe_path(env_var: str, *parts: str) -> Optional[str]:
    base = os.getenv(env_var)
    if not base:
        return None
    return os.path.join(base, *parts)


def _default_exe_paths(browser: str) -> list[str]:
    if browser == "chrome":
        candidates = [
            _env_exe_path("ProgramFiles", "Google", "Chrome", "Application", "chrome.exe"),
            _env_exe_path("ProgramFiles(x86)", "Google", "Chrome", "Application", "chrome.exe"),
            _env_exe_path("LocalAppData", "Google", "Chrome", "Application", "chrome.exe"),
        ]
    elif browser == "edge":
        candidates = [
            _env_exe_path("ProgramFiles(x86)", "Microsoft", "Edge", "Application", "msedge.exe"),
            _env_exe_path("ProgramFiles", "Microsoft", "Edge", "Application", "msedge.exe"),
            _env_exe_path("LocalAppData", "Microsoft", "Edge", "Application", "msedge.exe"),
        ]
    else:
        candidates = []
    return [p for p in candidates if p]


# ブラウザ別設定
BROWSER_CONFIG = {
    "chrome": {
        "title_keywords": ["Chrome", "Google Chrome"],
        "title_regex": ".*Google Chrome.*",
        "start_command": ["start", "chrome"],
        "exe_name": "chrome.exe",
        "exe_paths": _default_exe_paths("chrome"),
        "launch_args": [],
        "address_bar_title_candidates": [
            "Address and search bar",
            "Search or enter web address",
        ],
        "address_bar_automation_id_candidates": [
            "Address and search bar",
            "address and search bar",
        ],
        "address_bar_control_types": ["Edit"],
    },
    "edge": {
        "title_keywords": ["Edge", "Microsoft Edge"],
        "title_regex": ".*Microsoft.*Edge.*",
        "start_command": ["start", "msedge"],
        "exe_name": r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        "exe_paths": _default_exe_paths("edge"),
        "launch_args": [],
        "address_bar_title_candidates": [
            "Address and search bar",
            "Search or enter web address",
        ],
        "address_bar_automation_id_candidates": [
            "Address and search bar",
            "address and search bar",
        ],
        "address_bar_control_types": ["Edit"],
    },
}


def _parse_index_range_slices(index_ranges: str) -> list[slice]:
    """
    例: "1:4,10:-1"
    - "," 区切り
    - 各トークンは "start:end"（Pythonのスライスと同等: start含む/end除外, 負数OK）
    """
    if index_ranges is None:
        return []

    tokens = [t.strip() for t in str(index_ranges).split(",") if t.strip()]
    slices: list[slice] = []
    for token in tokens:
        if token.count(":") != 1:
            raise InvalidInputError(
                f"parse_index_range_slices: invalid token format: {token!r} (expected 'start:end')",
                code="invalid_index_ranges",
            )
        start_s, end_s = (p.strip() for p in token.split(":", 1))
        start = int(start_s) if start_s != "" else None
        end = int(end_s) if end_s != "" else None
        slices.append(slice(start, end))
    return slices


def _indices_from_slices(range_slices: list[slice], *, length: int) -> list[int]:
    if length < 0:
        raise InvalidInputError("indices_from_slices: length must be >= 0", code="invalid_length")
    if not range_slices:
        return list(range(length))

    selected: set[int] = set()
    for sl in range_slices:
        selected.update(range(*sl.indices(length)))
    return sorted(selected)


def _scan_limit_for_slices(range_slices: list[slice]) -> Optional[int]:
    """
    負数や末尾(None)が無い場合のみ、必要なmatched要素数を事前に決めて早期breakできる。
    """
    if not range_slices:
        return None

    max_stop: int | None = 0
    for sl in range_slices:
        start = sl.start
        stop = sl.stop
        if start is not None and start < 0:
            return None
        if stop is None:
            return None
        if stop < 0:
            return None
        max_stop = max(max_stop or 0, stop)
    return max_stop


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
        raise UnsupportedBrowserError(
            f"find_browser_windows: unsupported browser: {browser}. "
            f"Supported: {list(BROWSER_CONFIG.keys())}",
        )

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
        raise UnsupportedBrowserError(
            f"get_browser_window: unsupported browser: {browser}. "
            f"Supported: {list(BROWSER_CONFIG.keys())}",
        )

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
        _launch_browser_process(config)
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

    raise WindowNotFoundError(f"get_browser_window: {browser} window not found")


def _build_window_info(window, browser: str) -> BrowserWindowInfo:
    """pywinauto window -> BrowserWindowInfo へ正規化して詰め替える。"""
    hwnd = int(window.handle)

    # PID / title
    try:
        pid = int(window.process_id())
    except Exception:
        pid = -1

    try:
        title = window.window_text() or ""
    except Exception:
        title = ""

    # 可視 / 最小化
    try:
        is_visible = bool(window.is_visible())
    except Exception:
        is_visible = False

    try:
        is_minimized = bool(win32gui.IsIconic(hwnd))
    except Exception:
        is_minimized = False

    # Rect（取得失敗は例外にする：後方互換不要のため）
    rect = _get_window_rect(hwnd)

    # Z-order（「現在のフォアグラウンドウィンドウ＝最前面」判定）
    try:
        fg_hwnd = int(win32gui.GetForegroundWindow() or 0)
        is_foreground = hwnd == fg_hwnd
    except Exception:
        is_foreground = False

    return BrowserWindowInfo(
        browser=browser,
        title=title,
        pid=pid,
        handle=hwnd,
        rect=rect,
        is_visible=is_visible,
        is_minimized=is_minimized,
        is_foreground=is_foreground,
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
        raise UnsupportedBrowserError(
            f"launch_browser_driver: unsupported browser: {browser}. "
            f"Supported: {list(BROWSER_CONFIG.keys())}",
        )

    _launch_browser_process(config)
    time.sleep(start_delay)
    return NativeBrowserDriver(browser=browser, retries=retries, start_if_not_found=False)


def connect_browser_by_index(
    browser: str = "chrome",
    *,
    window_index: int = 0,
    require_visible: bool = False,
    exclude_minimized: bool = False,
    retries: int = 3,
) -> "NativeBrowserDriver":
    """
    指定インデックスのブラウザウィンドウに接続してドライバーを返す。

    Args:
        browser: ブラウザ種別（chrome/edge）
        window_index: 接続するウィンドウのインデックス（Pythonスタイル、-1で最後）
        require_visible: 可視ウィンドウのみ対象
        exclude_minimized: 最小化ウィンドウを除外
        retries: 探索リトライ回数

    Raises:
        WindowNotFoundError: 指定ブラウザが見つからない場合
        InvalidInputError: 指定インデックスが範囲外の場合
    """
    windows = find_browser_windows(
        browser,
        require_visible=require_visible,
        exclude_minimized=exclude_minimized,
        retries=retries,
    )

    if not windows:
        raise WindowNotFoundError(f"connect_browser_by_index: no {browser} windows found")

    # Python-style indices (negative indices supported)
    try:
        target_window = windows[window_index]
    except IndexError as exc:
        raise InvalidInputError(
            "connect_browser_by_index: window_index out of range "
            f"(index={window_index}, count={len(windows)})",
            code="index_out_of_range",
            data={"window_index": window_index, "window_count": len(windows)},
        ) from exc

    # NativeBrowserDriverインスタンスを作成し、指定ウィンドウに接続
    driver = object.__new__(NativeBrowserDriver)
    driver.browser = browser
    driver._config = BROWSER_CONFIG[browser]
    driver.current_elements = {}
    driver.current_elements_info = {}
    driver.current_elements_truncated = False
    driver.app = None
    driver.window = None
    _enable_dpi_awareness()
    driver.connect(target_window)

    return driver


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


class NativeBrowserError(Exception):
    code = "native_browser_error"

    def __init__(self, message: str, *, code: str | None = None, data: Any | None = None):
        super().__init__(message)
        self.code = code or self.code
        self.data = data

    def as_payload(self) -> dict[str, Any]:
        return {"code": self.code, "message": str(self), "data": self.data}


class InvalidInputError(NativeBrowserError):
    code = "invalid_input"


class UnsupportedBrowserError(InvalidInputError):
    code = "unsupported_browser"


class WindowNotFoundError(NativeBrowserError):
    code = "window_not_found"


class ElementNotFoundError(NativeBrowserError):
    code = "element_not_found"


class ClipboardError(NativeBrowserError):
    code = "clipboard_error"


class LaunchError(NativeBrowserError):
    code = "launch_failed"


class ScreenshotError(NativeBrowserError):
    code = "screenshot_failed"


class ExternalApiError(NativeBrowserError):
    code = "external_api_error"


class ActionFailedError(NativeBrowserError):
    code = "action_failed"


class BrowserTimeoutError(NativeBrowserError, TimeoutError):
    code = "timeout"


@dataclass(frozen=True)
class ActionResult:
    ok: bool
    code: str
    message: str
    data: Any | None = None

    @staticmethod
    def success(message: str, *, data: Any | None = None, code: str = "ok") -> "ActionResult":
        return ActionResult(True, code, message, data=data)

    @staticmethod
    def failure(code: str, message: str, *, data: Any | None = None) -> "ActionResult":
        return ActionResult(False, code, message, data=data)


def _raise_for_result(result: ActionResult) -> None:
    if result.ok:
        return

    if result.code == "element_not_found":
        raise ElementNotFoundError(result.message, data=result.data)
    if result.code == "timeout":
        raise BrowserTimeoutError(result.message, data=result.data)
    if result.code == "clipboard_error":
        raise ClipboardError(result.message, data=result.data)
    if result.code == "invalid_input":
        raise InvalidInputError(result.message, data=result.data)

    raise ActionFailedError(result.message, data=result.data)


def _get_clipboard_text() -> ActionResult:
    """クリップボードからテキストを取得する"""
    try:
        win32clipboard.OpenClipboard()
        try:
            text = win32clipboard.GetClipboardData(win32con.CF_UNICODETEXT)
            return ActionResult.success("clipboard_get: ok", data=text)
        except Exception as e:
            return ActionResult.failure(
                "clipboard_error",
                f"clipboard_get: failed to read clipboard data: {e}",
            )
        finally:
            win32clipboard.CloseClipboard()
    except Exception as e:
        return ActionResult.failure(
            "clipboard_error",
            f"clipboard_get: failed to open clipboard: {e}",
        )


def wait_until(
    predicate: Callable[[], bool],
    timeout_s: float = 2.0,
    interval_s: float = 0.05,
) -> bool:
    """条件を満たすまで待機し、timeout内に満たせなければFalseを返す。"""
    timeout_s = max(0.0, float(timeout_s))
    interval_s = max(0.01, float(interval_s))
    deadline = time.time() + timeout_s
    while time.time() <= deadline:
        try:
            if predicate():
                return True
        except Exception:
            pass
        time.sleep(interval_s)
    return False


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


@dataclass(frozen=True)
class BrowserWindowInfo:
    """起動中のブラウザウィンドウ情報（Rect + 前面判定付き）。"""
    browser: str
    title: str
    pid: int
    handle: int
    rect: Rect
    is_visible: bool
    is_minimized: bool
    is_foreground: bool  # Z-order判定（最前面＝フォアグラウンド）


def _get_window_rect(hwnd: int) -> Rect:
    l, t, r, b = win32gui.GetWindowRect(hwnd)
    return Rect(l, t, r, b)


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


def _launch_browser_process(config: dict[str, Any]) -> None:
    exe_paths = config.get("exe_paths") or []
    launch_args = config.get("launch_args") or []
    for exe in exe_paths:
        if exe and os.path.exists(exe):
            subprocess.Popen([exe, *launch_args], shell=False)
            return

    start_command = config.get("start_command")
    if start_command:
        subprocess.Popen(start_command, shell=True)
        return

    raise LaunchError("launch_browser_process: no valid browser launch configuration found")


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
        raise ScreenshotError("capture_printwindow: invalid window size (w/h <= 0)")

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
        raise ScreenshotError("capture_printwindow: PrintWindow failed (returned 0)")

    return img


def _capture_by_screen_rect(rect: Rect) -> Image.Image:
    if rect.width <= 0 or rect.height <= 0:
        raise ScreenshotError("capture_screen: invalid rect size (width/height <= 0)")

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
            raise UnsupportedBrowserError(
                f"NativeBrowserDriver: unsupported browser: {browser}. "
                f"Supported: {list(BROWSER_CONFIG.keys())}",
            )

        self.browser = browser
        self._config = BROWSER_CONFIG[browser]
        _enable_dpi_awareness()

        self.current_elements = {}
        self.current_elements_info = {}
        self.current_elements_truncated = False
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
        logger.info(f"Connected to {self.browser.capitalize()} (PID: {pid}).")


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
            raise ExternalApiError("ensure_visible: invalid hwnd (window does not exist)")

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

    def _prepare_for_input(
        self,
        maximize: bool,
        foreground: bool,
        settle_ms: int,
        focus: bool = True,
    ) -> None:
        self.ensure_visible(maximize=maximize, foreground=foreground, settle_ms=settle_ms)
        if focus:
            try:
                self.window.set_focus()
            except Exception:
                pass

    def _send_shortcut(
        self,
        action: Optional[Callable[[], None]] = None,
        *,
        keys: Optional[str] = None,
        maximize: bool = False,
        foreground: bool = True,
        settle_ms: int = 80,
        focus: bool = True,
        post_sleep_s: float = 0.0,
    ) -> None:
        self.ensure_visible(maximize=maximize, foreground=foreground, settle_ms=settle_ms)
        if focus:
            try:
                self.window.set_focus()
            except Exception:
                pass

        if keys:
            send_keys(keys)
        if action:
            action()

        if post_sleep_s > 0:
            time.sleep(post_sleep_s)

    def _prepare_for_read(
        self,
        foreground: bool = False,
        maximize: bool = False,
        settle_ms: int = 0,
    ) -> None:
        if foreground or maximize:
            self.ensure_visible(maximize=maximize, foreground=foreground, settle_ms=settle_ms)
        elif settle_ms > 0:
            time.sleep(settle_ms / 1000.0)

    def _wait_for_clipboard_text(
        self,
        previous_text: Optional[str],
        *,
        timeout_s: float = 0.8,
        interval_s: float = 0.05,
    ) -> ActionResult:
        latest: dict[str, Optional[str] | bool] = {"text": None, "updated": False}
        last_error: ActionResult | None = None

        def predicate() -> bool:
            nonlocal last_error
            result = _get_clipboard_text()
            if not result.ok:
                last_error = result
                return False
            latest["text"] = result.data
            latest["updated"] = (
                result.data is not None
                if previous_text is None
                else result.data != previous_text
            )
            return result.data is not None

        ok = wait_until(predicate, timeout_s=timeout_s, interval_s=interval_s)
        if not ok:
            if last_error and last_error.code == "clipboard_error":
                return ActionResult.failure(
                    "clipboard_error",
                    f"clipboard_wait: {last_error.message}",
                    data=last_error.data,
                )
            return ActionResult.failure(
                "timeout",
                f"clipboard_wait: timeout after {timeout_s}s",
                data=latest["text"],
            )

        message = "clipboard_wait: updated" if latest["updated"] else "clipboard_wait: read (update not confirmed)"
        return ActionResult.success(message, data=latest["text"])

    def _perform_clipboard_transfer(
        self,
        shortcut: str,
        *,
        timeout_s: float = 0.8,
        settle_ms: int = 80,
    ) -> ActionResult:
        """
        共通のクリップボード転送処理:
            - 入力準備
            - 事前クリップボード取得
            - 指定ショートカット送信
            - クリップボード更新待機
        """
        self._prepare_for_input(maximize=False, foreground=True, settle_ms=settle_ms)
        previous_result = _get_clipboard_text()
        previous = previous_result.data if previous_result.ok else None
        send_keys(shortcut)
        return self._wait_for_clipboard_text(previous, timeout_s=timeout_s, interval_s=0.05)

    def set_edit_text(self, index: int, text: str) -> str:
        """スキャンした要素のテキストを設定する"""
        result = self.set_edit_text_result(index, text)
        _raise_for_result(result)
        return result.message

    def set_edit_text_result(self, index: int, text: str) -> ActionResult:
        """スキャンした要素のテキストを設定する（ActionResult版）"""
        if index not in self.current_elements:
            return ActionResult.failure(
                "element_not_found",
                f"set_edit_text: element not found (index={index})",
            )

        elem = self.current_elements[index]

        try:
            self._prepare_for_input(maximize=False, foreground=True, settle_ms=80)
            elem.set_text(text)
            preview = text[:50] + ("..." if len(text) > 50 else "")
            return ActionResult.success(
                f"set_edit_text: ok (index={index}, text={preview})",
            )
        except Exception as e:
            return ActionResult.failure(
                "action_failed",
                f"set_edit_text: failed to set text (index={index}): {e}",
            )

    def set_edit_text_or_raise(self, index: int, text: str) -> None:
        """スキャンした要素のテキストを設定する（失敗時例外）"""
        result = self.set_edit_text_result(index, text)
        _raise_for_result(result)

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
                    raise ScreenshotError(
                        "screenshot: PrintWindow returned a blank image (possible GPU/occlusion issue)"
                    )
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
            raise ScreenshotError("screenshot: failed to capture screenshot. " + " | ".join(errors))

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

    def navigate(self, url: str, timeout_s: float = 5.0, interval_s: float = 0.1):
        """Ctrl+LでURLバーにフォーカスし、クリップボード経由で入力して移動"""
        self._prepare_for_input(maximize=False, foreground=True, settle_ms=80)
        previous_url = self.get_address_bar_url()
        send_keys("^l")
        wait_until(lambda: self.get_address_bar_url() != "Unknown", timeout_s=1.0, interval_s=0.05)
        _set_clipboard_text(url)
        send_keys("^v")
        send_keys("{ENTER}")

        def _url_changed() -> bool:
            current = self.get_address_bar_url()
            if current in ("Unknown", ""):
                return False
            return current != previous_url or url in current

        wait_until(_url_changed, timeout_s=timeout_s, interval_s=interval_s)

    def get_address_bar_url(self):
        """アドレスバーからURLを取得"""
        self._prepare_for_read()
        config = self._config
        control_types = config.get("address_bar_control_types") or ["Edit"]
        id_candidates = config.get("address_bar_automation_id_candidates") or []
        title_candidates = config.get("address_bar_title_candidates") or []

        for candidate_id in id_candidates:
            for control_type in control_types:
                try:
                    items = self.window.descendants(
                        control_type=control_type,
                        automation_id=candidate_id,
                    )
                except Exception:
                    continue
                for item in items:
                    try:
                        return item.get_value()
                    except Exception:
                        continue

        for candidate_title in title_candidates:
            for control_type in control_types:
                try:
                    items = self.window.descendants(
                        control_type=control_type,
                        title=candidate_title,
                    )
                except Exception:
                    continue
                for item in items:
                    try:
                        return item.get_value()
                    except Exception:
                        continue

        for control_type in control_types:
            try:
                edits = self.window.descendants(control_type=control_type)
            except Exception:
                continue
            for item in edits:
                try:
                    return item.get_value()
                except Exception:
                    continue

        return "Unknown"


    def scan_page_elements(
        self,
        control_type=None,
        title=None,
        max_elements=500,
        *,
        foreground: bool = False,
        maximize: bool = False,
        settle_ms: int = 0,
        update_mode: Literal["overwrite", "add", "preserve"] = "overwrite",
    ):
        self._prepare_for_read(foreground=foreground, maximize=maximize, settle_ms=settle_ms)

        elements_map: dict[int, Any] = {}
        elements_info: dict[int, dict[str, object]] = {}

        descendants_kwargs: dict[str, Any] = {}
        if control_type is not None:
            descendants_kwargs["control_type"] = control_type
        if title is not None:
            descendants_kwargs["title"] = title
        all_items = self.window.descendants(**descendants_kwargs) if descendants_kwargs else self.window.descendants()

        truncated = False
        max_elements = int(max_elements) if max_elements is not None else 0
        for item in all_items:
            if len(elements_map) >= max_elements:
                truncated = True
                break

            try:
                name = item.window_text()
            except Exception:
                name = ""

            try:
                f_class = item.friendly_class_name()
            except Exception:
                try:
                    f_class = item.element_info.control_type
                except Exception:
                    f_class = "Unknown"

            try:
                aid = item.element_info.automation_id
            except Exception:
                aid = ""
            aid = "" if aid is None else str(aid)

            index = len(elements_map)
            elements_map[index] = item
            elements_info[index] = {
                "control_type": str(f_class) if f_class is not None else "Unknown",
                "name": name or "",
                "automation_id": aid,
            }

        if update_mode == "overwrite":
            # 現在の要素を完全に置き換え
            self.current_elements = elements_map
            self.current_elements_info = elements_info
            self.current_elements_truncated = truncated
        elif update_mode == "add":
            # 既存インデックスを保持して新しいインデックスで追加
            max_index = max(self.current_elements.keys()) if self.current_elements else -1
            for idx, (elem, info) in enumerate(zip(elements_map.values(), elements_info.values())):
                new_idx = max_index + idx + 1
                self.current_elements[new_idx] = elem
                self.current_elements_info[new_idx] = info
        elif update_mode == "preserve":
            # スキャン結果は返すが、current_elementsは変更しない
            pass

        return f"Found {len(elements_map)} elements."

    def filter_current_elements(
        self,
        *,
        class_names: Optional[Union[str, Iterable[str]]] = None,
        control_types: Optional[Union[str, Iterable[str]]] = None,
        name_regex: Optional[str] = None,
        value_regex: Optional[str] = None,
        only_visible: bool = False,
        require_enabled: bool = False,
        min_width: Optional[int] = None,
        min_height: Optional[int] = None,
        only_focusable: bool = False,
        automation_id_regex: Optional[str] = None,
        omit_no_name: bool = False,
        min_separator_count: int = 0,
        update_mode: Literal["overwrite", "preserve"] = "overwrite",
        output: str = "simple",
    ) -> str:

        control_types_list = None
        if control_types:
            control_types_list = [control_types] if isinstance(control_types, str) else list(control_types)

        class_names_list = None
        if class_names:
            class_names_list = [class_names] if isinstance(class_names, str) else list(class_names)

        compiled_regex = re.compile(name_regex) if name_regex else None
        compiled_value_regex = re.compile(value_regex) if value_regex else None
        compiled_automation_id_regex = (
            re.compile(automation_id_regex) if automation_id_regex else None
        )

        separator_threshold = max(0, int(min_separator_count or 0))
        separator_hits = 0

        matched_items: list[tuple[Any, str, str, str]] = []
        for index in sorted(self.current_elements.keys()):
            item = self.current_elements[index]
            try:
                name = item.window_text()
            except Exception:
                name = ""
            name = name or ""

            try:
                f_class = item.friendly_class_name()
            except Exception:
                try:
                    f_class = item.element_info.control_type
                except Exception:
                    f_class = "Unknown"

            try:
                element_control_type = item.element_info.control_type
            except Exception:
                element_control_type = None

            value = ""
            if compiled_value_regex:
                try:
                    value = item.get_value()
                except Exception:
                    value = ""
                value = "" if value is None else str(value)
                if not compiled_value_regex.search(value):
                    continue

            try:
                is_separator = element_control_type == "Separator"
                if is_separator:
                    separator_hits += 1
                    if separator_threshold and separator_hits <= separator_threshold:
                        continue

                if separator_threshold and separator_hits < separator_threshold:
                    continue

                if not name and omit_no_name:
                    unnamed_allowed_types = [
                        "CheckBox",
                        "Button",
                        "RadioButton",
                        "ComboBox",
                        "ListBox",
                        "Edit",
                        "Slider",
                        "Spinner",
                        "TabItem",
                        "ToggleButton",
                        "SplitButton",
                        "MenuItem",
                        "Link",
                        "Hyperlink",
                        "Separator",
                    ]
                    if element_control_type in unnamed_allowed_types:
                        name = f"<{element_control_type}>"
                    else:
                        continue

                if control_types_list:
                    if element_control_type is None or element_control_type not in control_types_list:
                        continue

                if min_width is not None or min_height is not None:
                    rect = item.rectangle()
                    if (min_width is not None and rect.width() <= min_width) or (min_height is not None and rect.height() <= min_height):
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

                if class_names_list:
                    try:
                        if f_class not in class_names_list:
                            continue
                    except Exception:
                        continue

                if compiled_regex and not compiled_regex.search(name):
                    continue

                try:
                    auto_id = item.element_info.automation_id
                except Exception:
                    auto_id = ""
                auto_id = "" if auto_id is None else str(auto_id)

                if compiled_automation_id_regex:
                    if not compiled_automation_id_regex.search(auto_id):
                        continue

                aid = auto_id

                matched_items.append((item, f_class, name, aid))
            except Exception as e:
                logger.debug(
                    f"filter_current_elements: Exception at index {index}: "
                    f"{type(e).__name__}: {e}"
                )
                continue

        logger.debug(
            f"filter_current_elements: Processed {len(self.current_elements)} elements, "
            f"matched {len(matched_items)} items"
        )

        selected_indices = list(range(len(matched_items)))
        elements_map: dict[int, Any] = {}
        elements_info: dict[int, dict[str, object]] = {}
        for current_index in selected_indices:
            item, f_class, name, aid = matched_items[current_index]
            elements_map[current_index] = item
            elements_info[current_index] = {
                "control_type": str(f_class) if f_class is not None else "Unknown",
                "name": name or "",
                "automation_id": aid,
            }

        output_mode = str(output or "simple").lower()
        if output_mode == "simple":
            result = f"Filtered {len(elements_map)} elements."
        elif output_mode == "summary":
            result = self._format_elements_summary(elements_map, elements_info, truncated=False)
        elif output_mode == "full":
            result = self._format_elements_list(elements_map, elements_info, truncated=False)
        else:
            raise InvalidInputError(
                f"filter_current_elements: unknown output mode: {output!r}",
                code="invalid_output_mode",
            )

        if update_mode == "overwrite":
            # 現在の要素を完全に置き換え
            self.current_elements = elements_map
            self.current_elements_info = elements_info
            self.current_elements_truncated = False
        elif update_mode == "preserve":
            # フィルタ結果は返すが、current_elementsは変更しない
            pass

        logger.debug(
            f"filter_current_elements: Final result = {len(elements_map)} elements, "
            f"update_mode={update_mode}"
        )

        return result

    def _ensure_current_elements_info(self) -> dict[int, dict[str, object]]:
        info = getattr(self, "current_elements_info", None)
        if isinstance(info, dict) and set(info.keys()) == set(self.current_elements.keys()):
            return info

        info = {}
        for index, item in self.current_elements.items():
            try:
                control_type = item.friendly_class_name()
            except Exception:
                try:
                    control_type = item.element_info.control_type
                except Exception:
                    control_type = "Unknown"

            try:
                name = item.window_text()
            except Exception:
                name = ""

            try:
                aid = item.element_info.automation_id
            except Exception:
                aid = ""
            aid = "" if aid is None else str(aid)

            info[index] = {
                "control_type": str(control_type) if control_type is not None else "Unknown",
                "name": name,
                "automation_id": aid,
            }

        self.current_elements_info = info
        return info

    def _format_elements_list(
        self,
        elements_map: dict[int, Any],
        elements_info: dict[int, dict[str, object]],
        *,
        truncated: bool,
    ) -> str:
        lines: list[str] = []
        for index in sorted(elements_map.keys()):
            info = elements_info.get(index, {})
            control_type = info.get("control_type") or "Unknown"
            name = info.get("name") or ""
            aid = info.get("automation_id")
            name_part = f" {name}" if name else ""
            aid_str = f" [ID:{aid}]" if aid else ""
            lines.append(f"[{index}] <{control_type}>{name_part}{aid_str}")

        if truncated:
            lines.append("... (more elements truncated)")

        return "\n".join(lines)

    def _format_elements_summary(
        self,
        elements_map: dict[int, Any],
        elements_info: dict[int, dict[str, object]],
        *,
        truncated: bool,
    ) -> str:
        type_counts: dict[str, int] = {}
        for index in elements_map.keys():
            info = elements_info.get(index, {})
            control_type = info.get("control_type") or "Unknown"
            type_counts[control_type] = type_counts.get(control_type, 0) + 1

        summary_lines = [f"Total elements: {len(elements_map)}"]
        if type_counts:
            summary_lines.append("Elements by type:")
            for control_type_name, count in sorted(type_counts.items()):
                summary_lines.append(f"  {control_type_name}: {count}")
        if truncated:
            summary_lines.append("... (more elements truncated)")
        return "\n".join(summary_lines)

    def get_current_elements_list(self) -> str:
        info_map = self._ensure_current_elements_info()
        return self._format_elements_list(
            self.current_elements,
            info_map,
            truncated=self.current_elements_truncated,
        )

    def get_current_elements_summary(self) -> str:
        info_map = self._ensure_current_elements_info()
        return self._format_elements_summary(
            self.current_elements,
            info_map,
            truncated=self.current_elements_truncated,
        )

    def click_by_index(self, index):
        result = self.click_by_index_result(index)
        _raise_for_result(result)
        return result.message

    def click_by_index_result(self, index: int) -> ActionResult:
        if index not in self.current_elements:
            return ActionResult.failure(
                "element_not_found",
                f"click_by_index: element not found (index={index})",
            )

        elem = self.current_elements[index]
        try:
            elem.invoke()
            return ActionResult.success(
                f"click_by_index: ok (index={index})",
                data={"method": "invoke"},
            )
        except Exception as invoke_error:
            try:
                self._prepare_for_input(maximize=False, foreground=True, settle_ms=80)
                elem.click_input()
                return ActionResult.success(
                    f"click_by_index: ok (index={index})",
                    data={"method": "click_input", "invoke_error": str(invoke_error)},
                )
            except Exception as click_error:
                return ActionResult.failure(
                    "action_failed",
                    "click_by_index: failed to click "
                    f"(index={index}): invoke={invoke_error}; click_input={click_error}",
                )

    def click_by_index_or_raise(self, index: int) -> None:
        result = self.click_by_index_result(index)
        _raise_for_result(result)

    def select_all_and_get_text(self) -> str:
        """Ctrl+Aで全選択してCtrl+Cでクリップボードにコピーし、テキストを取得"""
        result = self.select_all_and_get_text_result()
        _raise_for_result(result)
        return "" if result.data is None else str(result.data)

    def select_all_and_get_text_result(self) -> ActionResult:
        """Ctrl+Aで全選択してCtrl+Cでクリップボードにコピーし、テキストを取得（ActionResult版）"""
        return self._perform_clipboard_transfer("^a^c", timeout_s=1.2, settle_ms=100)

    def select_all_and_get_text_or_raise(self) -> str:
        result = self.select_all_and_get_text_result()
        _raise_for_result(result)
        return "" if result.data is None else str(result.data)

    # ========================================
    # ページスクロール機能
    # ========================================

    def scroll_down(self, amount: int = 500) -> None:
        """指定したピクセル数だけ下にスクロール"""
        def _action() -> None:
            for _ in range(amount // 100):
                send_keys("{DOWN}")
                time.sleep(0.01)

        self._send_shortcut(_action)

    def scroll_up(self, amount: int = 500) -> None:
        """指定したピクセル数だけ上にスクロール"""
        def _action() -> None:
            for _ in range(amount // 100):
                send_keys("{UP}")
                time.sleep(0.01)

        self._send_shortcut(_action)

    def scroll_to_bottom(self) -> None:
        """ページの最下部までスクロール"""
        self._send_shortcut(keys="^{END}", post_sleep_s=0.2)

    def scroll_to_top(self) -> None:
        """ページの最上部までスクロール"""
        self._send_shortcut(keys="^{HOME}", post_sleep_s=0.2)

    def page_down(self) -> None:
        """Page Downキーでスクロール"""
        self._send_shortcut(keys="{PGDN}", post_sleep_s=0.1)

    def page_up(self) -> None:
        """Page Upキーでスクロール"""
        self._send_shortcut(keys="{PGUP}", post_sleep_s=0.1)

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
            raise InvalidInputError("type_text: method must be 'paste' or 'type'", code="invalid_method")

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
        self._send_shortcut(keys="^t", post_sleep_s=0.3)

    def close_tab(self) -> None:
        """現在のタブを閉じる (Ctrl+W)"""
        self._send_shortcut(keys="^w", post_sleep_s=0.3)

    def next_tab(self) -> None:
        """次のタブに切り替え (Ctrl+Tab)"""
        self._send_shortcut(keys="^{TAB}", post_sleep_s=0.2)

    def previous_tab(self) -> None:
        """前のタブに切り替え (Ctrl+Shift+Tab)"""
        self._send_shortcut(keys="^+{TAB}", post_sleep_s=0.2)

    # ========================================
    # ブラウザ操作機能
    # ========================================

    def back(self) -> None:
        """戻る (Alt+←)"""
        self._send_shortcut(keys="%{LEFT}", post_sleep_s=0.5)

    def forward(self) -> None:
        """進む (Alt+→)"""
        self._send_shortcut(keys="%{RIGHT}", post_sleep_s=0.5)

    def refresh(self) -> None:
        """ページをリロード (F5)"""
        self._send_shortcut(keys="{F5}", post_sleep_s=0.5)

    def zoom_in(self) -> None:
        """ズームイン (Ctrl++)"""
        self._send_shortcut(keys="^{+}", post_sleep_s=0.2)

    def zoom_out(self) -> None:
        """ズームアウト (Ctrl+-)"""
        self._send_shortcut(keys="^{-}", post_sleep_s=0.2)

    def reset_zoom(self) -> None:
        """ズームをリセット (Ctrl+0)"""
        self._send_shortcut(keys="^0", post_sleep_s=0.2)

    # ========================================
    # 待機・検証機能
    # ========================================

    def wait_for_idle(self, seconds: float = 2) -> None:
        """指定秒数待機"""
        time.sleep(seconds)

    def get_page_title(self) -> str:
        """現在のページタイトルを取得"""
        self._prepare_for_read()
        try:
            return self.window.window_text()
        except Exception as e:
            raise ExternalApiError(f"get_page_title: failed to read window title: {e}") from e

    def get_browser_summary(self, max_text_len: int = 50) -> dict[str, object]:
        """現在のブラウザ概要をJSON向けdictで返す（途中出力なし）"""
        self._prepare_for_read()

        def _norm_trunc(value: object) -> str:
            s = "" if value is None else str(value)
            s = s.replace("\r", " ").replace("\n", " ").strip()
            if max_text_len and max_text_len > 0 and len(s) > max_text_len:
                return s[:max_text_len]
            return s

        hwnd = self.hwnd

        # 1) URL
        try:
            url = self.get_address_bar_url()
        except Exception as e:
            url = f"Error: {e}"

        # 2) タイトル
        try:
            title = self.get_page_title()
        except Exception as e:
            title = f"Error: {e}"

        # 3) 状態（最小化/通常/最大化 + 可視/不可視）
        window_state = "normal"
        try:
            if win32gui.IsIconic(hwnd):
                window_state = "minimized"
            elif win32gui.IsZoomed(hwnd):
                window_state = "maximized"
        except Exception:
            pass

        try:
            visible = bool(win32gui.IsWindowVisible(hwnd))
        except Exception:
            try:
                visible = bool(self.window.is_visible())
            except Exception:
                visible = False

        try:
            offscreen = bool(self.window.element_info.element.CurrentIsOffscreen)
        except Exception:
            offscreen = not visible

        # 4) 位置・サイズ
        rect_payload: dict[str, object]
        try:
            rect = _get_window_rect(hwnd)
            rect_payload = {
                "left": rect.left,
                "top": rect.top,
                "right": rect.right,
                "bottom": rect.bottom,
                "width": rect.width,
                "height": rect.height,
            }
        except Exception as e:
            rect_payload = {"error": _norm_trunc(e)}

        # 5) descendants統計
        descendants_payload: dict[str, object] = {
            "total": 0,
            "visible_total": 0,
            "invisible_total": 0,
            "visible_by_control_type": {},
            "invisible_by_control_type": {},
        }
        self.current_elements = {}
        self.current_elements_info = {}
        self.current_elements_truncated = False
        try:
            items = self.window.descendants()
            descendants_payload["total"] = len(items)

            visible_map = descendants_payload["visible_by_control_type"]
            invisible_map = descendants_payload["invisible_by_control_type"]

            elements_map: dict[int, Any] = {}
            elements_info: dict[int, dict[str, object]] = {}
            for index, item in enumerate(items):
                elements_map[index] = item
                try:
                    control_type = getattr(getattr(item, "element_info", None), "control_type", None)
                except Exception:
                    control_type = None

                if not control_type:
                    try:
                        control_type = item.friendly_class_name()
                    except Exception:
                        control_type = "Unknown"

                control_type = str(control_type)

                try:
                    name = item.window_text()
                except Exception:
                    name = ""

                try:
                    aid = item.element_info.automation_id
                except Exception:
                    aid = ""
                aid = "" if aid is None else str(aid)

                elements_info[index] = {
                    "control_type": control_type,
                    "name": name,
                    "automation_id": aid,
                }

                try:
                    is_visible = bool(item.is_visible())
                except Exception:
                    is_visible = False

                if is_visible:
                    descendants_payload["visible_total"] = int(descendants_payload["visible_total"]) + 1
                    visible_map[control_type] = int(visible_map.get(control_type, 0)) + 1
                else:
                    descendants_payload["invisible_total"] = int(descendants_payload["invisible_total"]) + 1
                    invisible_map[control_type] = int(invisible_map.get(control_type, 0)) + 1

            self.current_elements = elements_map
            self.current_elements_info = elements_info
        except Exception as e:
            descendants_payload["error"] = _norm_trunc(e)

        return {
            "url": _norm_trunc(url),
            "title": _norm_trunc(title),
            "state": {
                "window": window_state,
                "visible": visible,
                "offscreen": offscreen,
            },
            "rect": rect_payload,
            "descendants": descendants_payload,
        }

    # ========================================
    # ページソース取得
    # ========================================

    def get_page_source(self, *, wait_seconds: float = 1.5, close_after: bool = True, save_path: Optional[str] = None) -> str:
        """
        Ctrl+Uでソースビューを開き、全選択コピーしてHTMLを返す。
        close_after=Trueならソースビューのタブを閉じて元のタブに戻る。
        """
        self._prepare_for_input(maximize=False, foreground=True, settle_ms=80)
        send_keys("^u")
        wait_until(
            lambda: str(self.get_address_bar_url()).startswith("view-source:"),
            timeout_s=wait_seconds,
            interval_s=0.1,
        )

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
        self._send_shortcut(keys="^v", post_sleep_s=0.2)

    def copy_selected_text(self) -> str:
        """選択済みのテキストをコピーして取得 (Ctrl+C)"""
        result = self.copy_selected_text_result()
        _raise_for_result(result)
        return "" if result.data is None else str(result.data)

    def copy_selected_text_result(self) -> ActionResult:
        """選択済みのテキストをコピーして取得 (Ctrl+C, ActionResult版)"""
        return self._perform_clipboard_transfer("^c", timeout_s=0.8, settle_ms=80)

    def copy_selected_text_or_raise(self) -> str:
        result = self.copy_selected_text_result()
        _raise_for_result(result)
        return "" if result.data is None else str(result.data)

    def cut_text(self) -> str:
        """選択済みのテキストをカットして取得 (Ctrl+X)"""
        result = self.cut_text_result()
        _raise_for_result(result)
        return "" if result.data is None else str(result.data)

    def cut_text_result(self) -> ActionResult:
        """選択済みのテキストをカットして取得 (Ctrl+X, ActionResult版)"""
        return self._perform_clipboard_transfer("^x", timeout_s=0.8, settle_ms=80)

    def cut_text_or_raise(self) -> str:
        result = self.cut_text_result()
        _raise_for_result(result)
        return "" if result.data is None else str(result.data)

    # ========================================
    # 座標操作
    # ========================================

    def click_at_position(self, x: int, y: int) -> None:
        """指定座標をクリック（ウィンドウ相対座標）"""
        self._send_shortcut(
            lambda: self.window.click_input(coords=(x, y)),
            post_sleep_s=0.2,
        )

    def double_click_at_position(self, x: int, y: int) -> None:
        """指定座標をダブルクリック（ウィンドウ相対座標）"""
        self._send_shortcut(
            lambda: self.window.double_click_input(coords=(x, y)),
            post_sleep_s=0.2,
        )

    def right_click_at_position(self, x: int, y: int) -> None:
        """指定座標を右クリック（ウィンドウ相対座標）"""
        self._send_shortcut(
            lambda: self.window.right_click_input(coords=(x, y)),
            post_sleep_s=0.2,
        )

    def move_mouse_to_element(self, index: int) -> None:
        """スキャンした要素の位置にマウスを移動"""
        if index not in self.current_elements:
            raise ElementNotFoundError(
                f"move_mouse_to_element: element not found (index={index})",
                code="element_not_found",
            )

        element = self.current_elements[index]
        try:
            element.set_focus()
            time.sleep(0.1)
            rect = element.rectangle()
            # 矩形の中心座標を計算
            x = (rect.left + rect.right) // 2
            y = (rect.top + rect.bottom) // 2

            #self.ensure_visible(maximize=False, foreground=True, settle_ms=0)
            mouse.move(coords=(x, y))
            time.sleep(0.1)
        except Exception as e:
            raise ActionFailedError(
                f"move_mouse_to_element: failed to move mouse to element (index={index}): {e}",
                code="action_failed",
            )

    def move_mouse_to_position(self, x: int, y: int) -> None:
        """指定座標にマウスを移動（スクリーン絶対座標）"""
        try:
            self.ensure_visible(maximize=False, foreground=True, settle_ms=0)
            mouse.move(x, y)
            time.sleep(0.1)
        except Exception as e:
            raise ActionFailedError(
                f"move_mouse_to_position: failed to move mouse to ({x}, {y}): {e}",
                code="action_failed",
            )

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
                raise InvalidInputError(
                    "capture_full_screen: invalid monitor number "
                    f"(monitor={monitor}, available=0-{len(sct.monitors) - 1})",
                    code="invalid_monitor",
                )

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
