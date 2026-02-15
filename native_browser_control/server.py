#!/usr/bin/env python3
"""
Native Browser Control MCP Server

server側はセッション管理に専念し、ブラウザ操作はdriverへ委譲する。
"""

import argparse
import asyncio
import base64
import inspect
import io
import json
from dataclasses import asdict
from typing import Any

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import ImageContent, Resource, TextContent, Tool

from native_browser_control.driver import (
    ActionResult,
    NativeBrowserDriver,
    NativeBrowserError,
    NativeChromeDriver,
    NativeEdgeDriver,
    BROWSER_CONFIG,
)

__version__ = "0.1.0"

_sessions: dict[str, NativeBrowserDriver] = {}
_active_session_by_browser: dict[str, str] = {}


def _driver_class_for_browser(browser: str) -> type[NativeBrowserDriver]:
    key = (browser or "chrome").lower()
    if key == "edge":
        return NativeEdgeDriver
    return NativeChromeDriver


def build_schema(properties: dict[str, Any] | None = None, required: list[str] | None = None) -> dict[str, Any]:
    """JSON Schemaのobject定義を組み立てる。"""
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
    return [TextContent(type="text", text=json.dumps(_error_payload(code, message, data), ensure_ascii=False))]


def _exception_to_error_payload(exc: Exception) -> dict[str, Any]:
    if isinstance(exc, NativeBrowserError):
        return _error_payload(exc.code, str(exc), exc.data)
    if isinstance(exc, TimeoutError):
        return _error_payload("timeout", str(exc))
    if isinstance(exc, IndexError):
        return _error_payload("index_out_of_range", str(exc))
    if isinstance(exc, (KeyError, ValueError, TypeError, AttributeError)):
        return _error_payload("invalid_input", str(exc))
    return _error_payload("internal_error", str(exc))


def _annotation_to_str(annotation: Any) -> str:
    if annotation is inspect._empty:
        return ""
    try:
        return str(annotation).replace("typing.", "")
    except Exception:
        return repr(annotation)


def _is_public_driver_member(name: str) -> bool:
    if name.startswith("_"):
        return False
    if name.startswith("__") and name.endswith("__"):
        return False
    return True


def _signature_to_json(sig: inspect.Signature) -> dict[str, Any]:
    params: list[dict[str, Any]] = []
    for p in sig.parameters.values():
        if p.name == "self":
            continue
        if p.kind in (inspect.Parameter.VAR_POSITIONAL, inspect.Parameter.VAR_KEYWORD):
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


def _read_driver_member(target: Any, member_name: str) -> dict[str, Any]:
    if not member_name:
        raise ValueError("member is required")
    if not _is_public_driver_member(member_name):
        raise ValueError(f"member not allowed: {member_name}")
    if not hasattr(target, member_name):
        raise AttributeError(f"unknown member: {member_name}")

    member = getattr(target, member_name)
    owner = target if inspect.isclass(target) else type(target)
    class_member = getattr(owner, member_name, None)
    owner_name = owner.__name__

    if isinstance(class_member, property):
        if inspect.isclass(target):
            return {
                "ok": True,
                "driver_class": owner_name,
                "name": member_name,
                "kind": "property",
                "requires_session": True,
            }
        doc = (getattr(class_member, "fget").__doc__ or "").strip() if getattr(class_member, "fget", None) else ""
        return {
            "ok": True,
            "driver_class": owner_name,
            "name": member_name,
            "kind": "property",
            "value": member,
            "doc": doc,
        }

    if callable(member):
        try:
            sig_json = _signature_to_json(inspect.signature(member))
        except Exception:
            sig_json = {"signature": "", "params": [], "return_annotation": ""}

        doc = (getattr(member, "__doc__", None) or "").strip()
        return {
            "ok": True,
            "driver_class": owner_name,
            "name": member_name,
            "kind": "method",
            **sig_json,
            "doc": doc,
            "class_target": inspect.isclass(target),
        }

    return {
        "ok": True,
        "driver_class": owner_name,
        "name": member_name,
        "kind": "value",
        "value": member,
    }


def _invoke_member(target: Any, *, method: str, args: list[Any] | None, kwargs: dict[str, Any] | None) -> Any:
    if not method:
        raise ValueError("method is required")
    if not _is_public_driver_member(method):
        raise ValueError(f"method not allowed: {method}")
    if not hasattr(target, method):
        raise AttributeError(f"unknown method: {method}")

    member = getattr(target, method)
    owner = target if inspect.isclass(target) else type(target)
    class_member = getattr(owner, method, None)

    if isinstance(class_member, property):
        if args or kwargs:
            raise TypeError(f"{method} is a property; args/kwargs are not allowed")
        if inspect.isclass(target):
            raise TypeError(f"{method} is an instance property; class target is not allowed")
        return member

    if not callable(member):
        return member

    a = args or []
    k = kwargs or {}
    sig = inspect.signature(member)
    sig.bind_partial(*a, **k)
    return member(*a, **k)


def _window_to_payload(window: Any) -> dict[str, Any]:
    return {
        "handle": int(getattr(window, "handle", 0) or 0),
        "pid": int(window.process_id()),
        "title": str(window.window_text() or ""),
    }


def _create_session_from_window(browser: str, window: Any) -> NativeBrowserDriver:
    key = (browser or "chrome").lower()
    if key not in BROWSER_CONFIG:
        raise ValueError(f"unsupported browser: {browser}")

    driver_cls = _driver_class_for_browser(key)
    driver = object.__new__(driver_cls)
    driver.browser = key
    driver._config = BROWSER_CONFIG[key]
    driver.current_elements = []
    driver.current_elements_info = []
    driver.current_elements_truncated = False
    driver.app = None
    driver.window = None
    driver.connect(window)
    return driver


def _resolve_session(session_id: str | None, browser: str) -> tuple[str, NativeBrowserDriver]:
    sid = (session_id or "").strip()
    if not sid:
        sid = _active_session_by_browser.get(browser, "")
    if not sid:
        raise ValueError("session_id is required; call driver_call(method='get_browser_window') first")
    driver = _sessions.get(sid)
    if not driver:
        raise ValueError(f"unknown session_id: {sid}")
    return sid, driver


server = Server("native-browser-control")

RESOURCES = {
    "tips://session-flow": {
        "name": "セッション手順",
        "description": "get_browser_windowでセッションを作ってからdriver_callする手順",
        "content": """# セッション手順

1. `driver_call(method=\"get_browser_window\", class_target=true, kwargs={...})`
2. 返却された `session_id` を保持
3. `driver_call(method=\"navigate\", session_id=\"...\", args=[\"https://example.com\"])`
""",
    }
}


@server.list_resources()
async def list_resources() -> list[Resource]:
    return [
        Resource(
            uri=uri,
            name=info["name"],
            description=info["description"],
            mimeType="text/markdown",
        )
        for uri, info in RESOURCES.items()
    ]


@server.read_resource()
async def read_resource(uri: str) -> str:
    if uri in RESOURCES:
        return RESOURCES[uri]["content"]
    raise ValueError(f"Unknown resource: {uri}")


@server.list_tools()
async def list_tools() -> list[Tool]:
    common_props = {
        "browser": {"type": "string", "enum": ["chrome", "edge"], "default": "chrome"},
        "session_id": {"type": "string"},
    }

    return [
        Tool(
            name="driver_read",
            description="driverメンバー情報を返します。session_idがあればそのセッションを参照します。",
            inputSchema=build_schema(
                properties={
                    **common_props,
                    "member": {"type": "string"},
                },
                required=["member"],
            ),
        ),
        Tool(
            name="driver_call",
            description=(
                "driverメソッドを呼び出します。"
                " method='get_browser_window' は class_target=true で実行し、session_id を生成します。"
            ),
            inputSchema=build_schema(
                properties={
                    **common_props,
                    "method": {"type": "string"},
                    "args": {"type": "array", "default": []},
                    "kwargs": {"type": "object", "default": {}},
                    "class_target": {"type": "boolean", "default": False},
                },
                required=["method"],
            ),
        ),
        Tool(
            name="driver_tool_info",
            description="ドライバーが提供する公開メソッド一覧とシグネチャを返します。",
            inputSchema=build_schema(properties={**common_props}),
        ),
    ]


def _result_to_contents(result: Any, arguments: dict[str, Any]) -> list[TextContent | ImageContent]:
    fmt = str(arguments.get("fmt", "PNG")).upper()

    if isinstance(result, bytes):
        mime_type = "image/png" if fmt == "PNG" else "image/jpeg"
        img_base64 = base64.standard_b64encode(result).decode("utf-8")
        return [ImageContent(type="image", data=img_base64, mimeType=mime_type)]

    try:
        from PIL import Image as _PILImage
    except Exception:
        _PILImage = None

    if _PILImage is not None and isinstance(result, _PILImage.Image):
        mime_type = "image/png" if fmt == "PNG" else "image/jpeg"
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
    try:
        arguments = arguments or {}
        browser = str(arguments.get("browser", "chrome")).lower()

        if name == "driver_read":
            member = str(arguments.get("member", "")).strip()
            session_id = str(arguments.get("session_id", "")).strip()
            target: Any = NativeBrowserDriver
            if session_id:
                _, target = _resolve_session(session_id, browser)
            payload = _read_driver_member(target, member)
            return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

        if name == "driver_tool_info":
            session_id = str(arguments.get("session_id", "")).strip()
            if session_id:
                _, driver = _resolve_session(session_id, browser)
                info = type(driver).tool_info()
            else:
                info = _driver_class_for_browser(browser).tool_info()
            return [TextContent(type="text", text=json.dumps(info, ensure_ascii=False, indent=2))]

        if name == "driver_call":
            method = str(arguments.get("method", "")).strip()
            args = arguments.get("args") or []
            kwargs = arguments.get("kwargs") or {}
            class_target = bool(arguments.get("class_target", False))
            session_id = str(arguments.get("session_id", "")).strip()

            if not isinstance(args, list):
                return _error_text("invalid_input", "driver_call: 'args' must be an array")
            if not isinstance(kwargs, dict):
                return _error_text("invalid_input", "driver_call: 'kwargs' must be an object")

            if class_target or method == "get_browser_window":
                result = _invoke_member(NativeBrowserDriver, method=method, args=args, kwargs=kwargs)

                if method == "get_browser_window":
                    sid = session_id or f"{browser}:default"
                    driver = _create_session_from_window(browser, result)
                    _sessions[sid] = driver
                    _active_session_by_browser[browser] = sid
                    payload = {
                        "ok": True,
                        "session_id": sid,
                        "browser": browser,
                        "window": _window_to_payload(result),
                    }
                    return [TextContent(type="text", text=json.dumps(payload, ensure_ascii=False))]

                return _result_to_contents(result, kwargs)

            sid, driver = _resolve_session(session_id, browser)
            result = _invoke_member(driver, method=method, args=args, kwargs=kwargs)
            _active_session_by_browser[browser] = sid
            return _result_to_contents(result, kwargs)

        return _error_text("unknown_tool", f"call_tool: unknown tool '{name}'")
    except Exception as e:
        payload = _exception_to_error_payload(e)
        return _error_text(payload["code"], payload["message"], payload.get("data"))


async def run_server() -> None:
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Native Browser Control MCP Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"native-browser-control {__version__}",
    )
    parser.parse_args()
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
