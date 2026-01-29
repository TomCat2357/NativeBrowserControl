#!/usr/bin/env python3
"""
Native Browser Control MCP Server

Windows UI Automation経由でChrome/Edgeを制御するMCPサーバー。
Seleniumを使用せず、pywinautoを使った直接制御を提供します。
"""

import argparse
import asyncio
import base64
import io
import json
import inspect
from dataclasses import asdict
from typing import Any, Literal, get_args, get_origin

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Tool,
    TextContent,
    ImageContent,
    Resource,
)

from native_browser_control.driver import (
    NativeBrowserDriver,
    NativeChromeDriver,
    NativeEdgeDriver,
    ActionResult,
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
    """??????????????????"""
    schema: dict[str, Any] = {"type": "object", "properties": properties or {}}
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

    driver = DRIVER_FACTORIES[key](launch=start_if_not_found)
    _drivers[key] = driver
    return driver


def _schema_type_from_annotation(annotation: Any, default: Any) -> tuple[str, list[Any] | None]:
    if annotation is inspect._empty:
        if isinstance(default, bool):
            return "boolean", None
        if isinstance(default, int) and not isinstance(default, bool):
            return "integer", None
        if isinstance(default, float):
            return "number", None
        if isinstance(default, list):
            return "array", None
        if isinstance(default, dict):
            return "object", None
        return "string", None

    origin = get_origin(annotation)
    if origin is not None:
        if origin is list:
            return "array", None
        if origin is dict:
            return "object", None
        if origin is tuple:
            return "array", None
        if origin is set:
            return "array", None
        if origin is Literal:
            values = list(get_args(annotation))
            enum_type = "string"
            if values and isinstance(values[0], bool):
                enum_type = "boolean"
            elif values and isinstance(values[0], int):
                enum_type = "integer"
            return enum_type, values

    if annotation is bool:
        return "boolean", None
    if annotation is int:
        return "integer", None
    if annotation is float:
        return "number", None
    if annotation is str:
        return "string", None

    return "object", None


def _build_schema_from_signature(sig: inspect.Signature) -> dict[str, Any]:
    properties: dict[str, Any] = {}
    required: list[str] = []

    for param in sig.parameters.values():
        if param.name == "self":
            continue
        if param.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            continue
        default = param.default
        param_type, enum_values = _schema_type_from_annotation(param.annotation, default)
        prop: dict[str, Any] = {"type": param_type}
        if enum_values:
            prop["enum"] = enum_values
        properties[param.name] = prop
        if default is inspect._empty:
            required.append(param.name)

    return build_schema(properties=properties, required=required or None)


def _iter_driver_tools() -> list[tuple[str, Any]]:
    tools: list[tuple[str, Any]] = []
    for name, member in NativeBrowserDriver.__dict__.items():
        if name.startswith("_") or (name.startswith("__") and name.endswith("__")):
            continue
        tools.append((name, member))
    return tools


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
    """???????????????????????????"""
    tools: list[Tool] = []
    for name, member in _iter_driver_tools():
        if isinstance(member, property):
            schema = build_schema()
            description = member.__doc__ or f"NativeBrowserDriver.{name}"
        elif callable(member):
            schema = _build_schema_from_signature(inspect.signature(member))
            description = member.__doc__ or f"NativeBrowserDriver.{name}"
        else:
            continue
        tools.append(
            Tool(
                name=name,
                description=description.strip() if description else f"NativeBrowserDriver.{name}",
                inputSchema=schema,
            )
        )
    return tools




def _result_to_contents(name: str, result: Any, arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    if name in ("screenshot", "capture_full_screen"):
        fmt = str(arguments.get("fmt", "PNG")).upper()
        mime_type = "image/png" if fmt == "PNG" else "image/jpeg"
        if isinstance(result, bytes):
            img_bytes = result
        else:
            try:
                from PIL import Image as _PILImage
            except Exception as exc:
                raise RuntimeError(f"PIL is required to encode images: {exc}") from exc

            if not isinstance(result, _PILImage.Image):
                raise ValueError(f"{name}: unexpected result type: {type(result)}")
            buf = io.BytesIO()
            save_kwargs: dict[str, Any] = {}
            if fmt == "JPEG":
                quality = arguments.get("quality")
                if quality is not None:
                    save_kwargs["quality"] = int(quality)
                save_kwargs["optimize"] = True
            result.save(buf, format=fmt, **save_kwargs)
            img_bytes = buf.getvalue()

        img_base64 = base64.standard_b64encode(img_bytes).decode("utf-8")
        return [ImageContent(type="image", data=img_base64, mimeType=mime_type)]

    if isinstance(result, ActionResult):
        return [TextContent(type="text", text=json.dumps(asdict(result), ensure_ascii=False))]

    if isinstance(result, (dict, list)):
        return [TextContent(type="text", text=json.dumps(result, ensure_ascii=False))]

    if isinstance(result, str):
        return [TextContent(type="text", text=result)]

    if result is None:
        return [TextContent(type="text", text="ok")]

    return [TextContent(type="text", text=str(result))]


@server.call_tool()
async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    """??????????????"""
    arguments = arguments or {}
    browser = arguments.pop("browser", "chrome")
    try:
        driver = get_driver(browser)
        if not hasattr(driver, name):
            return _error_text("unknown_tool", f"call_tool: unknown tool '{name}'")

        member = getattr(driver, name)
        if callable(member):
            result = member(**arguments)
        else:
            result = member

        return _result_to_contents(name, result, arguments)
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
