#!/usr/bin/env python3
"""
Native Browser Control MCP Server

Windows UI Automation経由でChrome/Edgeを制御するMCPサーバー。
Seleniumを使用せず、pywinautoを使った直接制御を提供します。
"""

import argparse
import asyncio
import base64
import json
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    Resource,
)

from native_browser_control.core.driver import (
    NativeBrowserDriver,
    NativeChromeDriver,
    NativeEdgeDriver,
    NativeBrowserError,
    UnsupportedBrowserError,
    list_running_browser_drivers,
    launch_browser_driver,
    connect_browser_by_index,
)

# バージョン情報
__version__ = "0.1.0"

# ブラウザごとのドライバーインスタンス（遅延初期化）
DRIVER_FACTORIES: dict[str, type[NativeBrowserDriver]] = {
    "chrome": NativeChromeDriver,
    "edge": NativeEdgeDriver,
}
_drivers: dict[str, NativeBrowserDriver] = {}

BROWSER_PROPERTY = {
    "browser": {
        "type": "string",
        "enum": ["chrome", "edge"],
        "description": "対象ブラウザ（省略時: chrome）",
    }
}


def build_schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    """共通のbrowserオプションを付与した入力スキーマを生成"""
    props = {**(properties or {}), **BROWSER_PROPERTY}
    schema: dict[str, Any] = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


def _error_payload(code: str, message: str, data: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": False, "code": code, "message": message}
    if data is not None:
        payload["data"] = data
    return payload


def _error_text(code: str, message: str, data: Any | None = None) -> list[TextContent]:
    payload = _error_payload(code, message, data)
    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]


def _exception_to_error_payload(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, NativeBrowserError):
        return _error_payload(exc.code, str(exc), exc.data)
    if isinstance(exc, TimeoutError):
        return _error_payload("timeout", str(exc))
    if isinstance(exc, IndexError):
        return _error_payload("index_out_of_range", str(exc))
    if isinstance(exc, (KeyError, ValueError, TypeError)):
        return _error_payload("invalid_input", str(exc))
    return _error_payload("internal_error", str(exc))


def get_driver(browser: str = "chrome", *, start_if_not_found: bool = False) -> NativeBrowserDriver:
    """指定ブラウザのドライバーを取得（起動中のみ）。"""
    key = (browser or "chrome").lower()
    if key not in DRIVER_FACTORIES:
        supported = ", ".join(DRIVER_FACTORIES)
        raise UnsupportedBrowserError(
            f"get_driver: unsupported browser: {browser}. Supported: {supported}"
        )

    cached = _drivers.get(key)
    if cached:
        try:
            if cached.window.exists(timeout=0):
                return cached
        except Exception:
            pass
        _drivers.pop(key, None)

    driver = DRIVER_FACTORIES[key](start_if_not_found=start_if_not_found)
    _drivers[key] = driver
    return driver


# MCPサーバーの作成
server = Server("native-browser-control")

# リソース定義（Tips情報）
RESOURCES = {
    "tips://file-dialog-text-input": {
        "name": "ファイルダイアログでのテキスト入力方法",
        "description": "Windowsの「開く」ダイアログでファイル名テキストボックスにパスを入力する手順",
        "content": """# ファイルダイアログでのテキスト入力方法

Windowsの「開く」ダイアログ（ファイル選択画面）でファイル名を入力する手順です。

## 手順

1. **要素スキャン**: `scan_elements` を実行して件数を確認
2. **一覧取得**: `list_elements` でダイアログ内の要素一覧を取得
3. **Edit要素を特定**: 一覧から「ファイル名(N):」に対応する `<Edit>` 要素のインデックスを確認
   - 通常は `[56] <Edit> ファイル名(N):` のような形式で表示される
4. **テキスト設定**: `set_element_text` でインデックスとファイルパスを指定
   - 例: `set_element_text(index=56, text="C:\\Users\\username\\Downloads\\file.txt")`
5. **開くボタンクリック**: `click_element` で「開く(O)」ボタンをクリック
   - 通常は `[61] <Button> 開く(O)` のようなインデックス

## 注意点

- パスにはバックスラッシュ `\\` を使用（Windowsパス形式）
- インデックス番号はダイアログの状態により変わるため、毎回スキャンで確認が必要
"""
    },
    "tips://gemini-file-upload": {
        "name": "Geminiでのファイルアップロード手順",
        "description": "Google Geminiページを開いてファイルをアップロードするまでの一連の流れ",
        "content": """# Geminiでのファイルアップロード手順

Google Geminiのチャット画面でローカルファイルをアップロードする完全な手順です。

## 前提条件

- ChromeでGeminiページ (https://gemini.google.com/app?hl=ja) が開いていること
- Googleアカウントにログイン済みであること

## 手順

### Step 1: ファイルアップロードメニューを開く

1. `scan_elements` で要素をスキャン
2. `list_elements` で要素一覧を取得
3. 「ファイルをアップロード」ボタンを探す
   - 例: `[168] <Button> ファイルをアップロード. ドキュメント、データ、コードファイル`
4. `click_element` でそのボタンをクリック
5. `wait` で2秒程度待機（ダイアログが開くまで）

### Step 2: ファイル選択ダイアログでファイルを指定

1. `scan_elements` で「開く」ダイアログの要素をスキャン
2. `list_elements` で要素一覧を取得
3. 「ファイル名(N):」の `<Edit>` 要素のインデックスを確認
   - 例: `[56] <Edit> ファイル名(N):`
4. `set_element_text` でファイルパスを入力
   - 例: `set_element_text(index=56, text="C:\\Users\\username\\Downloads\\a.txt")`

### Step 3: 開くボタンをクリック

1. 「開く(O)」ボタンのインデックスを確認
   - 例: `[61] <Button> 開く(O)`
2. `click_element` でクリック
3. `wait` で2秒程度待機

### Step 4: 確認

- `screenshot` でアップロード完了を確認
- Geminiのチャット画面にファイルが添付されていればOK

## サンプルコード（MCP呼び出し順序）

```
1. scan_elements()
2. list_elements()
3. click_element(index=168)  # ファイルをアップロードボタン
4. wait(seconds=2)
5. scan_elements()
6. list_elements()
7. set_element_text(index=56, text="C:\\Users\\gk3t-\\Downloads\\a.txt")
8. click_element(index=61)  # 開く(O)ボタン
9. wait(seconds=2)
10. screenshot()  # 確認
```

## 注意点

- インデックス番号は画面状態により変わるため、毎回スキャンで確認が必要
- ファイルパスはフルパスで指定（相対パスは不可）
- 日本語ファイル名も使用可能
"""
    }
}


@server.list_resources()
async def list_resources() -> list[Resource]:
    """利用可能なリソース（Tips情報）のリストを返す"""
    return [
        Resource(
            uri=uri,
            name=info["name"],
            description=info["description"],
            mimeType="text/markdown"
        )
        for uri, info in RESOURCES.items()
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    """指定されたリソースの内容を返す"""
    if uri in RESOURCES:
        return RESOURCES[uri]["content"]
    raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def list_tools() -> list[Tool]:
    """利用可能なツールのリストを返す"""
    return [
        Tool(
            name="list_browser_windows",
            description="起動中のブラウザウィンドウ一覧を取得します（Chrome/Edge対応、ドライバー接続先の選択用）。インデックス番号付きで表示されます。",
            inputSchema=build_schema(
                properties={
                    "require_visible": {
                        "type": "boolean",
                        "description": "可視ウィンドウのみを対象にするか",
                    },
                    "exclude_minimized": {
                        "type": "boolean",
                        "description": "最小化されたウィンドウを除外するか",
                    },
                }
            ),
        ),
        Tool(
            name="connect_browser",
            description="指定ブラウザに接続します（Chrome/Edge対応）。window_indexで接続先を選択（省略時は0番目、-1で最後）。ブラウザが未起動の場合は起動します。",
            inputSchema=build_schema(
                properties={
                    "window_index": {
                        "type": "integer",
                        "description": "接続するウィンドウのインデックス（0=最初、-1=最後、省略時は0）。list_browser_windowsで確認可能。",
                    },
                }
            ),
        ),
        # ナビゲーション
        Tool(
            name="navigate",
            description="指定したURLに移動します（Chrome/Edge対応）",
            inputSchema=build_schema(
                properties={
                    "url": {"type": "string", "description": "移動先のURL"},
                },
                required=["url"],
            ),
        ),
        Tool(
            name="get_url",
            description="現在のページのURLを取得します（Chrome/Edge対応）",
            inputSchema=build_schema(),
        ),
        Tool(
            name="get_title",
            description="現在のページのタイトルを取得します（Chrome/Edge対応）",
            inputSchema=build_schema(),
        ),
        Tool(
            name="get_browser_summary",
            description="現在のブラウザ概要（URL/タイトル/状態/位置サイズ/descendants統計）をJSONで取得します（Chrome/Edge対応）",
            inputSchema=build_schema(
                properties={
                    "max_text_len": {
                        "type": "integer",
                        "description": "URL/タイトル等の最大文字数（デフォルト: 50）",
                    },
                }
            ),
        ),

        # スクリーンショット
        Tool(
            name="screenshot",
            description="ブラウザウィンドウのスクリーンショットを撮影します（Chrome/Edge対応、base64エンコードされた画像を返します）",
            inputSchema=build_schema(
                properties={
                    "format": {
                        "type": "string",
                        "enum": ["PNG", "JPEG"],
                        "description": "画像フォーマット（デフォルト: PNG）",
                    },
                    "quality": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 100,
                        "description": "JPEG品質（1-100、デフォルト: 90）",
                    },
                }
            ),
        ),
        Tool(
            name="full_screenshot",
            description="画面全体のスクリーンショットを撮影します（Chrome/Edge対応、ブラウザ以外も含む）",
            inputSchema=build_schema(
                properties={
                    "monitor": {
                        "type": "integer",
                        "description": "モニター番号（0=全モニター、1=プライマリ、2=セカンダリ...）",
                    },
                    "format": {
                        "type": "string",
                        "enum": ["PNG", "JPEG"],
                        "description": "画像フォーマット（デフォルト: PNG）",
                    },
                }
            ),
        ),

        # コンテンツ取得
        Tool(
            name="get_page_text",
            description="現在のページの全テキストを取得します（Chrome/Edge対応、Ctrl+A, Ctrl+Cで取得）",
            inputSchema=build_schema(),
        ),
        Tool(
            name="get_page_source",
            description="現在のページのHTMLソースを取得します（Chrome/Edge対応）",
            inputSchema=build_schema(),
        ),

        # テキスト入力
        Tool(
            name="type_text",
            description="フォーカス中の要素にテキストを入力します（Chrome/Edge対応）",
            inputSchema=build_schema(
                properties={
                    "text": {"type": "string", "description": "入力するテキスト"},
                    "method": {
                        "type": "string",
                        "enum": ["paste", "type"],
                        "description": "入力方法（paste=クリップボード経由、type=一文字ずつ）",
                    },
                },
                required=["text"],
            ),
        ),
        Tool(
            name="find_text",
            description="ページ内検索を開いてテキストを検索します（Chrome/Edge対応、Ctrl+F）",
            inputSchema=build_schema(
                properties={
                    "text": {"type": "string", "description": "検索するテキスト"},
                },
                required=["text"],
            ),
        ),

        # スクロール
        Tool(
            name="scroll",
            description="ページをスクロールします（Chrome/Edge対応）",
            inputSchema=build_schema(
                properties={
                    "direction": {
                        "type": "string",
                        "enum": ["down", "up", "top", "bottom", "page_down", "page_up"],
                        "description": "スクロール方向",
                    },
                    "amount": {
                        "type": "integer",
                        "description": "スクロール量（down/upの場合のみ、デフォルト: 500）",
                    },
                },
                required=["direction"],
            ),
        ),

        # タブ操作
        Tool(
            name="new_tab",
            description="新しいタブを開きます（Chrome/Edge対応、Ctrl+T）",
            inputSchema=build_schema(),
        ),
        Tool(
            name="close_tab",
            description="現在のタブを閉じます（Chrome/Edge対応、Ctrl+W）",
            inputSchema=build_schema(),
        ),
        Tool(
            name="switch_tab",
            description="タブを切り替えます（Chrome/Edge対応）",
            inputSchema=build_schema(
                properties={
                    "direction": {
                        "type": "string",
                        "enum": ["next", "previous"],
                        "description": "切り替え方向",
                    }
                },
                required=["direction"],
            ),
        ),

        # ブラウザ操作
        Tool(
            name="back",
            description="前のページに戻ります（Alt+←）",
            inputSchema=build_schema(),
        ),
        Tool(
            name="forward",
            description="次のページに進みます（Alt+→）",
            inputSchema=build_schema(),
        ),
        Tool(
            name="refresh",
            description="ページをリロードします（F5）",
            inputSchema=build_schema(),
        ),
        Tool(
            name="zoom",
            description="ズーム操作を行います",
            inputSchema=build_schema(
                properties={
                    "action": {
                        "type": "string",
                        "enum": ["in", "out", "reset"],
                        "description": "ズーム操作（in=拡大、out=縮小、reset=リセット）",
                    }
                },
                required=["action"],
            ),
        ),

        # クリック操作
        Tool(
            name="click",
            description="指定した座標をクリックします（ウィンドウ相対座標）",
            inputSchema=build_schema(
                properties={
                    "x": {"type": "integer", "description": "X座標"},
                    "y": {"type": "integer", "description": "Y座標"},
                    "click_type": {
                        "type": "string",
                        "enum": ["single", "double", "right"],
                        "description": "クリックの種類（デフォルト: single）",
                    },
                },
                required=["x", "y"],
            ),
        ),

        # 要素操作

        Tool(
            name="scan_elements",
            description="ページ上のUI要素をスキャンして current_elements を更新します。",
            inputSchema=build_schema(
                properties={
                    "control_type": {
                        "type": "string",
                        "description": "UIAのcontrol_typeで絞り込み（例: Button, Edit, Link）",
                    },
                    "title": {
                        "type": "string",
                        "description": "UIAのtitleで絞り込み（window_text相当）",
                    },
                    "max_elements": {
                        "type": "integer",
                        "description": "取得上限（デフォルト: 500）",
                    },
                    "update_mode": {
                        "type": "string",
                        "enum": ["overwrite", "add", "preserve"],
                        "description": "要素更新モード: overwrite=上書き（デフォルト）, add=追加, preserve=変更なし",
                    },
                }
            ),
        ),
        Tool(
            name="filter_elements",
            description="scan_elements で取得した current_elements を条件で絞り込みます。",
            inputSchema=build_schema(
                properties={
                    "class_names": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                        "description": "friendly_class_name() と一致するクラス名（単体/配列、OR条件）",
                    },
                    "control_types": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                        "description": "element_info.control_type と一致（単体/配列、OR条件）",
                    },
                    "name_regex": {
                        "type": "string",
                        "description": "window_text に対する正規表現",
                    },
                    "value_regex": {
                        "type": "string",
                        "description": "get_value() に対する正規表現",
                    },
                    "only_visible": {
                        "type": "boolean",
                        "description": "可視要素のみ（デフォルト: false）",
                    },
                    "require_enabled": {
                        "type": "boolean",
                        "description": "有効な要素のみ（デフォルト: false）",
                    },
                    "min_width": {
                        "type": "integer",
                        "description": "最小幅（px）",
                    },
                    "min_height": {
                        "type": "integer",
                        "description": "最小高さ（px）",
                    },
                    "only_focusable": {
                        "type": "boolean",
                        "description": "キーボードフォーカス可能のみ（デフォルト: false）",
                    },
                    "automation_id": {
                        "oneOf": [
                            {"type": "string"},
                            {"type": "array", "items": {"type": "string"}},
                        ],
                        "description": "automation_id の完全一致（単体/配列）",
                    },
                    "automation_id_regex": {
                        "type": "string",
                        "description": "automation_id に対する正規表現",
                    },
                    "omit_no_name": {
                        "type": "boolean",
                        "description": "名前なし要素を除外（デフォルト: true）",
                    },
                    "min_separator_count": {
                        "type": "integer",
                        "description": "先頭のSeparatorをスキップする閾値（0で無効）",
                    },
                    "update_mode": {
                        "type": "string",
                        "enum": ["overwrite", "add", "preserve"],
                        "description": "要素更新モード: overwrite=上書き（デフォルト）, add=追加, preserve=変更なし",
                    },
                    "output": {
                        "type": "string",
                        "enum": ["simple", "summary", "full"],
                        "description": "出力形式（simple=件数, summary=集計, full=一覧）",
                    },
                }
            ),
        ),
        Tool(
            name="list_elements",
            description="直近の scan_elements / filter_elements 結果を一覧表示します。",
            inputSchema=build_schema(),
        ),
        Tool(
            name="elements_summary",
            description="直近の scan_elements / filter_elements 結果をタイプ別に集計します。",
            inputSchema=build_schema(),
        ),
        Tool(
            name="click_element",
            description="スキャンした要素をインデックスでクリックします（先にscan_elementsを実行してください）",
            inputSchema=build_schema(
                properties={
                    "index": {
                        "type": "integer",
                        "description": "クリックする要素のインデックス",
                    }
                },
                required=["index"],
            ),
        ),
        Tool(
            name="set_element_text",
            description="スキャンした要素のテキストを設定します（先にscan_elementsを実行してください）",
            inputSchema=build_schema(
                properties={
                    "index": {
                        "type": "integer",
                        "description": "テキストを設定する要素のインデックス",
                    },
                    "text": {"type": "string", "description": "設定するテキスト"},
                },
                required=["index", "text"],
            ),
        ),

        # 待機
        Tool(
            name="wait",
            description="指定した秒数待機します",
            inputSchema=build_schema(
                properties={
                    "seconds": {"type": "number", "description": "待機秒数（デフォルト: 2）"},
                }
            ),
        ),

        # クリップボード
        Tool(
            name="copy_selected",
            description="選択中のテキストをコピーして取得します（Ctrl+C）",
            inputSchema=build_schema(),
        ),
        Tool(
            name="paste",
            description="クリップボードの内容を貼り付けます（Ctrl+V）",
            inputSchema=build_schema(),
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    """ツールを実行する"""
    arguments = arguments or {}
    browser = arguments.get("browser", "chrome")
    try:
        if name == "list_browser_windows":
            require_visible = bool(arguments.get("require_visible", False))
            exclude_minimized = bool(arguments.get("exclude_minimized", False))
            infos = list_running_browser_drivers(
                browser,
                require_visible=require_visible,
                exclude_minimized=exclude_minimized,
                retries=2,
            )
            if not infos:
                return [TextContent(type="text", text="No running target browser windows found.")]

            lines = [
                (
                    f"[{i}] {info.browser}: PID={info.pid}, HWND={info.handle}, "
                    f"Rect=({info.rect.left},{info.rect.top},{info.rect.right},{info.rect.bottom}), "
                    f"Foreground={info.is_foreground}, Visible={info.is_visible}, "
                    f"Minimized={info.is_minimized}, Title={info.title}"
                )
                for i, info in enumerate(infos)
            ]
            return [TextContent(type="text", text="\n".join(lines))]

        if name == "connect_browser":
            key = browser.lower()
            window_index = arguments.get("window_index", 0)
            running = list_running_browser_drivers(browser, retries=1)

            if running:
                # 既存ブラウザがある場合はインデックス指定で接続
                driver = connect_browser_by_index(browser, window_index=window_index)
                _drivers[key] = driver
                return [
                    TextContent(
                        type="text",
                        text=(
                            f"{browser} ウィンドウ[{window_index}]に接続しました。"
                            f" PID={driver.window.process_id()}, HWND={driver.hwnd}"
                        ),
                    )
                ]

            # ブラウザが起動していない場合は新規起動
            driver = launch_browser_driver(browser)
            _drivers[key] = driver
            return [
                TextContent(
                    type="text",
                    text=(
                        f"{browser} を起動し、PID={driver.window.process_id()}, HWND={driver.hwnd} に接続しました。"
                    ),
                )
            ]

        driver = get_driver(browser)
        # ナビゲーション
        if name == "navigate":
            url = arguments["url"]
            driver.navigate(url)
            return [TextContent(type="text", text=f"URLに移動しました: {url}")]

        elif name == "get_url":
            url = driver.get_address_bar_url()
            return [TextContent(type="text", text=url)]

        elif name == "get_title":
            title = driver.get_page_title()
            return [TextContent(type="text", text=title)]

        elif name == "get_browser_summary":
            max_text_len = int(arguments.get("max_text_len", 50))
            summary = driver.get_browser_summary(max_text_len=max_text_len)
            return [
                TextContent(type="text", text=json.dumps(summary, ensure_ascii=False))
            ]

        # スクリーンショット
        elif name == "screenshot":
            fmt = arguments.get("format", "PNG")
            quality = arguments.get("quality", 90)
            img_bytes = driver.screenshot(
                as_bytes=True,
                fmt=fmt,
                quality=quality
            )
            img_base64 = base64.standard_b64encode(img_bytes).decode("utf-8")
            mime_type = "image/png" if fmt == "PNG" else "image/jpeg"
            return [ImageContent(type="image", data=img_base64, mimeType=mime_type)]

        elif name == "full_screenshot":
            monitor = arguments.get("monitor", 0)
            fmt = arguments.get("format", "PNG")
            img_bytes = driver.capture_full_screen(
                monitor=monitor,
                as_bytes=True,
                fmt=fmt
            )
            img_base64 = base64.standard_b64encode(img_bytes).decode("utf-8")
            mime_type = "image/png" if fmt == "PNG" else "image/jpeg"
            return [ImageContent(type="image", data=img_base64, mimeType=mime_type)]

        # コンテンツ取得
        elif name == "get_page_text":
            text = driver.select_all_and_get_text()
            return [TextContent(type="text", text=text)]

        elif name == "get_page_source":
            source = driver.get_page_source()
            return [TextContent(type="text", text=source)]

        # テキスト入力
        elif name == "type_text":
            text = arguments["text"]
            method = arguments.get("method", "paste")
            driver.type_text(text, method=method)
            return [TextContent(type="text", text=f"テキストを入力しました: {text[:50]}{'...' if len(text) > 50 else ''}")]

        elif name == "find_text":
            text = arguments["text"]
            driver.find_text_on_page(text)
            return [TextContent(type="text", text=f"ページ内検索を開きました: {text}")]

        # スクロール
        elif name == "scroll":
            direction = arguments["direction"]
            amount = arguments.get("amount", 500)

            if direction == "down":
                driver.scroll_down(amount)
            elif direction == "up":
                driver.scroll_up(amount)
            elif direction == "top":
                driver.scroll_to_top()
            elif direction == "bottom":
                driver.scroll_to_bottom()
            elif direction == "page_down":
                driver.page_down()
            elif direction == "page_up":
                driver.page_up()

            return [TextContent(type="text", text=f"スクロールしました: {direction}")]

        # タブ操作
        elif name == "new_tab":
            driver.new_tab()
            return [TextContent(type="text", text="新しいタブを開きました")]

        elif name == "close_tab":
            driver.close_tab()
            return [TextContent(type="text", text="タブを閉じました")]

        elif name == "switch_tab":
            direction = arguments["direction"]
            if direction == "next":
                driver.next_tab()
            else:
                driver.previous_tab()
            return [TextContent(type="text", text=f"タブを切り替えました: {direction}")]

        # ブラウザ操作
        elif name == "back":
            driver.back()
            return [TextContent(type="text", text="前のページに戻りました")]

        elif name == "forward":
            driver.forward()
            return [TextContent(type="text", text="次のページに進みました")]

        elif name == "refresh":
            driver.refresh()
            return [TextContent(type="text", text="ページをリロードしました")]

        elif name == "zoom":
            action = arguments["action"]
            if action == "in":
                driver.zoom_in()
            elif action == "out":
                driver.zoom_out()
            else:
                driver.reset_zoom()
            return [TextContent(type="text", text=f"ズーム操作を実行しました: {action}")]

        # クリック操作
        elif name == "click":
            x = arguments["x"]
            y = arguments["y"]
            click_type = arguments.get("click_type", "single")

            if click_type == "single":
                driver.click_at_position(x, y)
            elif click_type == "double":
                driver.double_click_at_position(x, y)
            else:
                driver.right_click_at_position(x, y)

            return [TextContent(type="text", text=f"クリックしました: ({x}, {y}) - {click_type}")]

        # 要素操作

        elif name == "scan_elements":
            control_type = arguments.get("control_type")
            title = arguments.get("title")
            max_elements = arguments.get("max_elements", 500)
            update_mode = arguments.get("update_mode", "overwrite")

            result = driver.scan_page_elements(
                control_type=control_type,
                title=title,
                max_elements=max_elements,
                update_mode=update_mode,
            )
            return [TextContent(type="text", text=result)]

        elif name == "filter_elements":
            class_names = arguments.get("class_names")
            control_types = arguments.get("control_types")
            name_regex = arguments.get("name_regex")
            value_regex = arguments.get("value_regex")
            only_visible = arguments.get("only_visible", False)
            require_enabled = arguments.get("require_enabled", False)
            min_width = arguments.get("min_width", 0)
            min_height = arguments.get("min_height", 0)
            only_focusable = arguments.get("only_focusable", False)
            automation_id_regex = arguments.get("automation_id_regex")
            omit_no_name = arguments.get("omit_no_name", True)
            min_separator_count = arguments.get("min_separator_count", 0)
            update_mode = arguments.get("update_mode", "overwrite")
            output = arguments.get("output", "simple")

            result = driver.filter_current_elements(
                class_names=class_names,
                control_types=control_types,
                name_regex=name_regex,
                value_regex=value_regex,
                only_visible=only_visible,
                require_enabled=require_enabled,
                min_width=min_width,
                min_height=min_height,
                only_focusable=only_focusable,
                automation_id_regex=automation_id_regex,
                omit_no_name=omit_no_name,
                min_separator_count=min_separator_count,
                update_mode=update_mode,
                output=output,
            )
            return [TextContent(type="text", text=result)]

        elif name == "list_elements":

            result = driver.get_current_elements_list()
            return [TextContent(type="text", text=result if result else "No elements found.")]

        elif name == "elements_summary":
            result = driver.get_current_elements_summary()
            return [TextContent(type="text", text=result)]

        elif name == "click_element":
            index = arguments["index"]
            result = driver.click_by_index(index)
            return [TextContent(type="text", text=result)]

        elif name == "set_element_text":
            index = arguments["index"]
            text = arguments["text"]
            result = driver.set_edit_text(index, text)
            return [TextContent(type="text", text=result)]

        # 待機
        elif name == "wait":
            seconds = arguments.get("seconds", 2)
            driver.wait_for_idle(seconds)
            return [TextContent(type="text", text=f"{seconds}秒待機しました")]

        # クリップボード
        elif name == "copy_selected":
            text = driver.copy_selected_text()
            return [TextContent(type="text", text=text)]

        elif name == "paste":
            driver.paste_from_clipboard()
            return [TextContent(type="text", text="クリップボードの内容を貼り付けました")]

        else:
            return _error_text("unknown_tool", f"call_tool: unknown tool '{name}'")

    except Exception as e:
        payload = _exception_to_error_payload(e)
        return _error_text(payload["code"], payload["message"], payload.get("data"))


async def run_server():
    """MCPサーバーを起動"""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


def main():
    """エントリーポイント"""
    parser = argparse.ArgumentParser(
        description="Native Browser Control MCP Server - Windows UI Automation経由でChrome/Edgeを制御",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"native-browser-control {__version__}",
    )

    # 引数をパース（--helpや--versionの処理）
    parser.parse_args()

    # MCPサーバーとして起動
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
