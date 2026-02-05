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
from typing import Any

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


def _annotation_to_str(annotation: Any) -> str:
    """型注釈を人間向けの短い文字列にする（JSON Schemaではなく表示用）。"""
    if annotation is inspect._empty:
        return ""
    try:
        # typing objects
        return str(annotation).replace("typing.", "")
    except Exception:
        return repr(annotation)


def _is_public_driver_member(name: str) -> bool:
    if name.startswith("_"):
        return False
    if name.startswith("__") and name.endswith("__"):
        return False
    return True


def _iter_driver_members(
    driver: NativeBrowserDriver,
    *,
    include_private: bool = False,
    include_properties: bool = True,
    include_inherited: bool = True,
) -> list[tuple[str, Any]]:
    """現在のdriverインスタンスからメソッド/プロパティ候補を列挙する。"""
    members: list[tuple[str, Any]] = []
    seen: set[str] = set()

    # inspect.getmembers は inherited も拾う。不要なら type(driver).__dict__ だけ見る。
    if include_inherited:
        items = inspect.getmembers(type(driver))
    else:
        items = list(type(driver).__dict__.items())

    for name, member in items:
        if name in seen:
            continue
        seen.add(name)

        if not include_private and not _is_public_driver_member(name):
            continue

        # property
        if isinstance(member, property):
            if include_properties:
                members.append((name, member))
            continue

        # method/function
        if callable(member):
            members.append((name, member))
            continue

    members.sort(key=lambda x: x[0])
    return members


def _signature_to_json(sig: inspect.Signature) -> dict[str, Any]:
    params: list[dict[str, Any]] = []
    for p in sig.parameters.values():
        if p.name == "self":
            continue
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
            # 可変長は情報として載せるが、UI入力はargs/kwargsで受けるので必須ではない
            params.append(
                {
                    "name": p.name,
                    "kind": str(p.kind),
                    "required": False,
                    "default": None,
                    "annotation": _annotation_to_str(p.annotation),
                    "variadic": True,
                }
            )
            continue

        required = p.default is inspect._empty
        default = None if required else p.default
        params.append(
            {
                "name": p.name,
                "kind": str(p.kind),
                "required": required,
                "default": default,
                "annotation": _annotation_to_str(p.annotation),
            }
        )

    return {
        "signature": str(sig),
        "params": params,
        "return_annotation": _annotation_to_str(sig.return_annotation),
    }


def _get_capabilities_payload(
    driver: NativeBrowserDriver,
    *,
    include_private: bool = False,
    include_properties: bool = True,
    include_inherited: bool = True,
) -> dict[str, Any]:
    methods: list[dict[str, Any]] = []
    for name, member in _iter_driver_members(
        driver,
        include_private=include_private,
        include_properties=include_properties,
        include_inherited=include_inherited,
    ):
        if isinstance(member, property):
            doc = (member.fget.__doc__ or "") if getattr(member, "fget", None) else ""
            methods.append(
                {
                    "name": name,
                    "kind": "property",
                    "doc": doc.strip(),
                }
            )
            continue

        if callable(member):
            try:
                sig = inspect.signature(member)
                sig_json = _signature_to_json(sig)
            except Exception:
                sig_json = {"signature": "", "params": [], "return_annotation": ""}

            doc = (getattr(member, "__doc__", None) or "").strip()
            methods.append(
                {
                    "name": name,
                    "kind": "method",
                    **sig_json,
                    "doc": doc,
                }
            )

    return {
        "ok": True,
        "driver_class": type(driver).__name__,
        "methods": methods,
    }


def _invoke_driver_method(
    driver: NativeBrowserDriver,
    *,
    method: str,
    args: list[Any] | None,
    kwargs: dict[str, Any] | None,
) -> Any:
    """NativeBrowserDriverの任意メソッドを（可能な範囲で検証して）実行する。"""
    if not method:
        raise ValueError("method is required")
    if not _is_public_driver_member(method):
        raise ValueError(f"method not allowed: {method}")

    if not hasattr(driver, method):
        raise AttributeError(f"unknown method: {method}")

    target = getattr(driver, method)

    # property read
    if isinstance(getattr(type(driver), method, None), property):
        if args or kwargs:
            raise TypeError(f"{method} is a property; args/kwargs are not allowed")
        return target

    if not callable(target):
        return target

    a = args or []
    k = kwargs or {}

    # Signature validation (keeps server robust against driver spec changes)
    sig = inspect.signature(target)
    sig.bind_partial(*a, **k)  # raises TypeError on mismatch
    return target(*a, **k)


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

1. **要素スキャン**: `scan_page_elements` を実行して件数を確認
2. **一覧取得**: `get_current_elements_list` でダイアログ内の要素一覧を取得
3. **Edit要素を特定**: 一覧から「ファイル名(N):」に対応する `<Edit>` 要素のインデックスを確認
   - 通常は `[56] <Edit> ファイル名(N):` のような形式で表示される
4. **テキスト設定**: `set_edit_text` でインデックスとファイルパスを指定
   - 例: `set_edit_text(index=56, text="C:\\Users\\username\\Downloads\\file.txt")`
5. **開くボタンクリック**: `click_by_index` で「開く(O)」ボタンをクリック
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

1. `scan_page_elements` で要素をスキャン
2. `get_current_elements_list` で要素一覧を取得
3. 「ファイルをアップロード」ボタンを探す
   - 例: `[168] <Button> ファイルをアップロード. ドキュメント、データ、コードファイル`
4. `click_by_index` でそのボタンをクリック
5. `wait` で2秒程度待機（ダイアログが開くまで）

### Step 2: ファイル選択ダイアログでファイルを指定

1. `scan_page_elements` で「開く」ダイアログの要素をスキャン
2. `get_current_elements_list` で要素一覧を取得
3. 「ファイル名(N):」の `<Edit>` 要素のインデックスを確認
   - 例: `[56] <Edit> ファイル名(N):`
4. `set_edit_text` でファイルパスを入力
   - 例: `set_edit_text(index=56, text="C:\\Users\\username\\Downloads\\a.txt")`

### Step 3: 開くボタンをクリック

1. 「開く(O)」ボタンのインデックスを確認
   - 例: `[61] <Button> 開く(O)`
2. `click_by_index` でクリック
3. `wait` で2秒程度待機

### Step 4: 確認

- `screenshot` でアップロード完了を確認
- Geminiのチャット画面にファイルが添付されていればOK

## サンプルコード（MCP呼び出し順序）

```
1. scan_page_elements()
2. get_current_elements_list()
3. click_by_index(index=168)  # ファイルをアップロードボタン
4. wait(seconds=2)
5. scan_page_elements()
6. get_current_elements_list()
7. set_edit_text(index=56, text="C:\\Users\\gk3t-\\Downloads\\a.txt")
8. click_by_index(index=61)  # 開く(O)ボタン
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
    """固定ツールのみ公開（driverの変更に追従しやすいReflect+Invoke設計）。"""
    common_props = {
        "browser": {"type": "string", "enum": ["chrome", "edge"], "default": "chrome"},
        "start_if_not_found": {"type": "boolean", "default": False},
    }

    return [
        Tool(
            name="driver_get_capabilities",
            description=(
                "NativeBrowserDriverのメソッド/引数/Docstring等の仕様を取得します。"
                " driver側の変更にMCPサーバーを追従させないための反射ツールです。"
            ),
            inputSchema=build_schema(
                properties={
                    **common_props,
                    "include_private": {"type": "boolean", "default": False},
                    "include_properties": {"type": "boolean", "default": True},
                    "include_inherited": {"type": "boolean", "default": True},
                }
            ),
        ),
        Tool(
            name="driver_help",
            description="指定メソッドの signature / docstring を返します。",
            inputSchema=build_schema(
                properties={
                    **common_props,
                    "method": {"type": "string"},
                },
                required=["method"],
            ),
        ),
        Tool(
            name="driver_call",
            description=(
                "NativeBrowserDriverの任意メソッドを method + args/kwargs で実行します。"
                " 返り値はJSON/文字列/画像（base64）として返却します。"
            ),
            inputSchema=build_schema(
                properties={
                    **common_props,
                    "method": {"type": "string"},
                    "args": {"type": "array", "default": []},
                    "kwargs": {"type": "object", "default": {}},
                },
                required=["method"],
            ),
        ),
    ]




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
    """固定ツールの実行（Reflect+Invoke）。"""
    try:
        arguments = arguments or {}

        # 共通: driver選択
        browser = str(arguments.get("browser", "chrome")).lower()
        start_if_not_found = bool(arguments.get("start_if_not_found", False))
        driver = get_driver(browser=browser, start_if_not_found=start_if_not_found)

        if name == "driver_get_capabilities":
            payload = _get_capabilities_payload(
                driver,
                include_private=bool(arguments.get("include_private", False)),
                include_properties=bool(arguments.get("include_properties", True)),
                include_inherited=bool(arguments.get("include_inherited", True)),
            )
            return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

        if name == "driver_help":
            method = str(arguments.get("method", "")).strip()
            if not method:
                return _error_text("invalid_input", "driver_help: 'method' is required")

            if not _is_public_driver_member(method):
                return _error_text("invalid_input", f"driver_help: method not allowed: {method}")

            if not hasattr(driver, method):
                return _error_text("unknown_tool", f"driver_help: unknown method: {method}")

            member = getattr(driver, method)
            # property?
            if isinstance(getattr(type(driver), method, None), property):
                doc = (getattr(getattr(type(driver), method), "fget").__doc__ or "").strip()
                payload = {
                    "ok": True,
                    "driver_class": type(driver).__name__,
                    "name": method,
                    "kind": "property",
                    "doc": doc,
                }
                return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

            if callable(member):
                try:
                    sig = inspect.signature(member)
                    sig_json = _signature_to_json(sig)
                except Exception:
                    sig_json = {"signature": "", "params": [], "return_annotation": ""}

                doc = (getattr(member, "__doc__", None) or "").strip()
                payload = {
                    "ok": True,
                    "driver_class": type(driver).__name__,
                    "name": method,
                    "kind": "method",
                    **sig_json,
                    "doc": doc,
                }
                return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

            payload = {
                "ok": True,
                "driver_class": type(driver).__name__,
                "name": method,
                "kind": "value",
                "value": str(member),
            }
            return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

        if name == "driver_call":
            method = str(arguments.get("method", "")).strip()
            args = arguments.get("args") or []
            kwargs = arguments.get("kwargs") or {}
            if not isinstance(args, list):
                return _error_text("invalid_input", "driver_call: 'args' must be an array")
            if not isinstance(kwargs, dict):
                return _error_text("invalid_input", "driver_call: 'kwargs' must be an object")

            result = _invoke_driver_method(driver, method=method, args=args, kwargs=kwargs)

            # 画像返却のため、元メソッド名を渡す（screenshot等の特例処理を活かす）
            return _result_to_contents(method, result, {**kwargs, **{"args": args}})

        # 未知のtool名
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
