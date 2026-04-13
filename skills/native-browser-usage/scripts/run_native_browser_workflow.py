#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from native_browser_control.driver import (  # noqa: E402
    ActionResult,
    BROWSER_CONFIG,
    NativeBrowserDriver,
    NativeBrowserError,
    connect_browser_by_index,
    launch_browser_driver,
)

logging.getLogger().setLevel(logging.WARNING)
logging.getLogger("native_browser_control.driver").setLevel(logging.WARNING)


class WorkflowError(Exception):
    def __init__(self, code: str, message: str, data: Any | None = None) -> None:
        super().__init__(message)
        self.code = code
        self.data = data


def _error_payload(code: str, message: str, data: Any | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": False, "error": {"code": code, "message": message}}
    if data is not None:
        payload["error"]["data"] = data
    return payload


def _normalize_browser(value: Any) -> str:
    browser = str(value or "").strip().lower()
    if not browser:
        raise WorkflowError("browser_required", "Top-level 'browser' is required.")
    if browser not in BROWSER_CONFIG:
        raise WorkflowError(
            "invalid_browser",
            f"Unsupported browser: {browser}",
            {"supported": sorted(BROWSER_CONFIG.keys())},
        )
    return browser


def _require_dict(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise WorkflowError("invalid_spec", f"'{name}' must be an object.")
    return value


def _require_list(value: Any, name: str) -> list[Any]:
    if not isinstance(value, list):
        raise WorkflowError("invalid_spec", f"'{name}' must be an array.")
    return value


def _require_str(value: Any, name: str) -> str:
    if value is None:
        raise WorkflowError("invalid_spec", f"'{name}' is required.")
    text = str(value)
    if not text:
        raise WorkflowError("invalid_spec", f"'{name}' must not be empty.")
    return text


def _coerce_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return bool(value)


def _coerce_int(value: Any, default: int | None = None, name: str | None = None) -> int:
    if value is None:
        if default is None:
            raise WorkflowError("invalid_spec", f"'{name}' is required.")
        return default
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise WorkflowError("invalid_spec", f"'{name or 'value'}' must be an integer.") from exc


def _coerce_float(value: Any, default: float | None = None, name: str | None = None) -> float:
    if value is None:
        if default is None:
            raise WorkflowError("invalid_spec", f"'{name}' is required.")
        return default
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise WorkflowError("invalid_spec", f"'{name or 'value'}' must be a number.") from exc


def _timestamp_slug() -> str:
    return datetime.now().strftime("%Y%m%d-%H%M%S-%f")


def _artifact_dir(spec: dict[str, Any]) -> Path:
    raw_dir = spec.get("artifact_dir")
    if raw_dir:
        path = Path(str(raw_dir)).expanduser()
        if not path.is_absolute():
            path = (Path.cwd() / path).resolve()
    else:
        path = Path(tempfile.mkdtemp(prefix="native-browser-usage-")).resolve()
    path.mkdir(parents=True, exist_ok=True)
    return path


def _resolve_output_path(
    step: dict[str, Any],
    artifact_dir: Path,
    *,
    default_prefix: str,
    extension: str,
    field_name: str = "file_path",
) -> Path:
    raw_path = step.get(field_name)
    if raw_path:
        path = Path(str(raw_path)).expanduser()
        if not path.is_absolute():
            path = artifact_dir / path
    else:
        path = artifact_dir / f"{default_prefix}-{_timestamp_slug()}{extension}"
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _window_payload(driver: NativeBrowserDriver) -> dict[str, Any]:
    return {
        "handle": int(getattr(driver.window, "handle", 0) or 0),
        "pid": int(driver.window.process_id()),
        "title": str(driver.window.window_text() or ""),
    }


def _elements_payload(driver: NativeBrowserDriver) -> dict[str, Any]:
    info_list = list(getattr(driver, "current_elements_info", []) or [])
    items = []
    for index, info in enumerate(info_list):
        if not isinstance(info, dict):
            info = {}
        items.append(
            {
                "index": index,
                "control_type": str(info.get("control_type", "")),
                "name": str(info.get("name", "")),
                "automation_id": str(info.get("automation_id", "")),
            }
        )
    return {
        "count": len(items),
        "truncated": bool(getattr(driver, "current_elements_truncated", False)),
        "elements": items,
    }


def _result_payload(result: ActionResult) -> dict[str, Any]:
    return asdict(result)


def _connect_driver(browser: str, connect_spec: dict[str, Any]) -> NativeBrowserDriver:
    launch = _coerce_bool(connect_spec.get("launch"), default=False)
    has_window_index = "window_index" in connect_spec
    retries = _coerce_int(connect_spec.get("retries"), default=3, name="connect.retries")

    if launch and has_window_index:
        raise WorkflowError(
            "invalid_connect",
            "'connect.window_index' and 'connect.launch' cannot be used together.",
        )
    if launch:
        return launch_browser_driver(
            browser=browser,
            retries=retries,
            start_delay=_coerce_float(
                connect_spec.get("start_delay"),
                default=1.0,
                name="connect.start_delay",
            ),
        )
    if has_window_index:
        return connect_browser_by_index(
            browser=browser,
            window_index=_coerce_int(
                connect_spec.get("window_index"),
                name="connect.window_index",
            ),
            require_visible=_coerce_bool(connect_spec.get("require_visible"), default=False),
            exclude_minimized=_coerce_bool(
                connect_spec.get("exclude_minimized"),
                default=False,
            ),
            retries=retries,
        )
    raise WorkflowError(
        "invalid_connect",
        "'connect' must specify either 'window_index' or 'launch: true'.",
    )


def _ensure_scan_state(scan_ready: bool, action: str) -> None:
    if not scan_ready:
        raise WorkflowError(
            "scan_required",
            f"Action '{action}' requires a prior 'scan' step in the same workflow.",
        )


def _validate_step_browser(step: dict[str, Any], browser: str, index: int) -> None:
    if "browser" not in step:
        return
    step_browser = _normalize_browser(step.get("browser"))
    if step_browser != browser:
        raise WorkflowError(
            "browser_mismatch",
            f"Step {index} browser '{step_browser}' does not match top-level browser '{browser}'.",
        )


def _handle_summary(driver: NativeBrowserDriver, step: dict[str, Any]) -> dict[str, Any]:
    saved_elements = list(getattr(driver, "current_elements", []))
    saved_info = list(getattr(driver, "current_elements_info", []))
    saved_truncated = bool(getattr(driver, "current_elements_truncated", False))
    try:
        data = driver.get_browser_summary(
            max_text_len=_coerce_int(step.get("max_text_len"), default=50, name="max_text_len")
        )
    finally:
        driver.current_elements = saved_elements
        driver.current_elements_info = saved_info
        driver.current_elements_truncated = saved_truncated
    return {"ok": True, "data": data}


def _handle_scroll(driver: NativeBrowserDriver, step: dict[str, Any]) -> dict[str, Any]:
    direction = _require_str(step.get("direction"), "direction").lower()
    amount = _coerce_int(step.get("amount"), default=500, name="amount")
    if direction == "down":
        driver.scroll_down(amount=amount)
    elif direction == "up":
        driver.scroll_up(amount=amount)
    elif direction == "page_down":
        driver.page_down()
    elif direction == "page_up":
        driver.page_up()
    elif direction == "top":
        driver.scroll_to_top()
    elif direction == "bottom":
        driver.scroll_to_bottom()
    else:
        raise WorkflowError("invalid_spec", f"Unsupported scroll direction: {direction}")
    return {"ok": True, "direction": direction, "amount": amount}


def _handle_tab(driver: NativeBrowserDriver, step: dict[str, Any]) -> dict[str, Any]:
    operation = _require_str(step.get("operation"), "operation").lower()
    if operation == "new":
        driver.new_tab()
    elif operation == "close":
        driver.close_tab()
    elif operation == "next":
        driver.next_tab()
    elif operation == "previous":
        driver.previous_tab()
    else:
        raise WorkflowError("invalid_spec", f"Unsupported tab operation: {operation}")
    return {"ok": True, "operation": operation}


def _handle_history(driver: NativeBrowserDriver, step: dict[str, Any]) -> dict[str, Any]:
    operation = _require_str(step.get("operation"), "operation").lower()
    if operation == "back":
        driver.back()
    elif operation == "forward":
        driver.forward()
    elif operation == "refresh":
        driver.refresh()
    else:
        raise WorkflowError("invalid_spec", f"Unsupported history operation: {operation}")
    return {"ok": True, "operation": operation}


def _handle_zoom(driver: NativeBrowserDriver, step: dict[str, Any]) -> dict[str, Any]:
    operation = _require_str(step.get("operation"), "operation").lower()
    if operation == "in":
        driver.zoom_in()
    elif operation == "out":
        driver.zoom_out()
    elif operation == "reset":
        driver.reset_zoom()
    else:
        raise WorkflowError("invalid_spec", f"Unsupported zoom operation: {operation}")
    return {"ok": True, "operation": operation}


def _handle_clipboard(driver: NativeBrowserDriver, step: dict[str, Any]) -> dict[str, Any]:
    operation = _require_str(step.get("operation"), "operation").lower()
    if operation == "copy_selected":
        result = driver.copy_selected_text_result()
        return {"ok": result.ok, "result": _result_payload(result)}
    if operation == "cut_text":
        result = driver.cut_text_result()
        return {"ok": result.ok, "result": _result_payload(result)}
    if operation == "paste":
        driver.paste_from_clipboard()
        return {"ok": True, "operation": operation}
    raise WorkflowError("invalid_spec", f"Unsupported clipboard operation: {operation}")


def _handle_click_at(driver: NativeBrowserDriver, step: dict[str, Any]) -> dict[str, Any]:
    x = _coerce_int(step.get("x"), name="x")
    y = _coerce_int(step.get("y"), name="y")
    button = str(step.get("button", "left")).lower()
    if button == "left":
        driver.click_at_position(x, y)
    elif button == "double":
        driver.double_click_at_position(x, y)
    elif button == "right":
        driver.right_click_at_position(x, y)
    else:
        raise WorkflowError("invalid_spec", f"Unsupported click button: {button}")
    return {"ok": True, "x": x, "y": y, "button": button}


def _handle_move_mouse(
    driver: NativeBrowserDriver,
    step: dict[str, Any],
    *,
    scan_ready: bool,
) -> dict[str, Any]:
    if "index" in step:
        _ensure_scan_state(scan_ready, "move_mouse")
        index = _coerce_int(step.get("index"), name="index")
        driver.move_mouse_to_element(index)
        return {"ok": True, "target": "element", "index": index}
    x = _coerce_int(step.get("x"), name="x")
    y = _coerce_int(step.get("y"), name="y")
    driver.move_mouse_to_position(x, y)
    return {"ok": True, "target": "position", "x": x, "y": y}


def _run_step(
    driver: NativeBrowserDriver,
    browser: str,
    step: dict[str, Any],
    index: int,
    artifact_dir: Path,
    artifacts: list[dict[str, Any]],
    *,
    scan_ready: bool,
) -> tuple[dict[str, Any], bool]:
    _validate_step_browser(step, browser, index)
    action = _require_str(step.get("action"), "action").lower()
    payload: dict[str, Any] = {"step_index": index, "action": action}

    if action == "summary":
        payload.update(_handle_summary(driver, step))
        return payload, scan_ready

    if action == "navigate":
        driver.navigate(
            _require_str(step.get("url"), "url"),
            timeout_s=_coerce_float(step.get("timeout_s"), default=5.0, name="timeout_s"),
            interval_s=_coerce_float(step.get("interval_s"), default=0.1, name="interval_s"),
        )
        payload.update({"ok": True, "url": step.get("url")})
        return payload, scan_ready

    if action == "wait":
        seconds = _coerce_float(step.get("seconds"), default=2.0, name="seconds")
        driver.wait_for_idle(seconds=seconds)
        payload.update({"ok": True, "seconds": seconds})
        return payload, scan_ready

    if action == "screenshot":
        fmt = str(step.get("fmt", "PNG")).upper()
        extension = ".png" if fmt == "PNG" else ".jpg"
        file_path = _resolve_output_path(
            step,
            artifact_dir,
            default_prefix=f"step-{index:02d}-screenshot",
            extension=extension,
        )
        driver.screenshot(
            file_path=str(file_path),
            prefer=str(step.get("prefer", "printwindow")),
            allow_fallback=_coerce_bool(step.get("allow_fallback"), default=True),
            prepare_window=_coerce_bool(step.get("prepare_window"), default=True),
            maximize_before=_coerce_bool(step.get("maximize_before"), default=True),
            foreground_before=_coerce_bool(step.get("foreground_before"), default=True),
            settle_ms=_coerce_int(step.get("settle_ms"), default=150, name="settle_ms"),
            fmt=fmt,
            quality=_coerce_int(step.get("quality"), default=90, name="quality"),
        )
        artifact = {"step_index": index, "action": action, "path": str(file_path), "kind": "image"}
        artifacts.append(artifact)
        payload.update({"ok": True, "fmt": fmt, "path": str(file_path)})
        return payload, scan_ready

    if action == "full_screenshot":
        fmt = str(step.get("fmt", "PNG")).upper()
        extension = ".png" if fmt == "PNG" else ".jpg"
        file_path = _resolve_output_path(
            step,
            artifact_dir,
            default_prefix=f"step-{index:02d}-full-screenshot",
            extension=extension,
        )
        driver.capture_full_screen(
            file_path=str(file_path),
            monitor=_coerce_int(step.get("monitor"), default=0, name="monitor"),
            fmt=fmt,
            quality=_coerce_int(step.get("quality"), default=90, name="quality"),
        )
        artifact = {"step_index": index, "action": action, "path": str(file_path), "kind": "image"}
        artifacts.append(artifact)
        payload.update({"ok": True, "fmt": fmt, "path": str(file_path)})
        return payload, scan_ready

    if action == "page_text":
        result = driver.select_all_and_get_text_result()
        payload.update(
            {
                "ok": result.ok,
                "result": _result_payload(result),
                "text": "" if result.data is None else str(result.data),
            }
        )
        return payload, scan_ready

    if action == "scan":
        update_mode = str(step.get("update_mode", "overwrite"))
        message = driver.scan_page_elements(
            control_type=step.get("control_type"),
            title=step.get("title"),
            max_elements=_coerce_int(step.get("max_elements"), default=500, name="max_elements"),
            foreground=_coerce_bool(step.get("foreground"), default=False),
            maximize=_coerce_bool(step.get("maximize"), default=False),
            settle_ms=_coerce_int(step.get("settle_ms"), default=0, name="settle_ms"),
            update_mode=update_mode,
        )
        payload.update({"ok": True, "message": message, **_elements_payload(driver)})
        return payload, scan_ready or update_mode != "preserve"

    if action == "filter":
        _ensure_scan_state(scan_ready, action)
        output = driver.filter_current_elements(
            class_names=step.get("class_names"),
            control_types=step.get("control_types"),
            name_regex=step.get("name_regex"),
            value_regex=step.get("value_regex"),
            only_visible=_coerce_bool(step.get("only_visible"), default=False),
            require_enabled=_coerce_bool(step.get("require_enabled"), default=False),
            min_width=step.get("min_width"),
            min_height=step.get("min_height"),
            only_focusable=_coerce_bool(step.get("only_focusable"), default=False),
            automation_id_regex=step.get("automation_id_regex"),
            omit_no_name=_coerce_bool(step.get("omit_no_name"), default=False),
            min_separator_count=_coerce_int(
                step.get("min_separator_count"),
                default=0,
                name="min_separator_count",
            ),
            update_mode=str(step.get("update_mode", "overwrite")),
            output=str(step.get("output", "simple")),
        )
        payload.update({"ok": True, "output": output, **_elements_payload(driver)})
        return payload, scan_ready

    if action == "get_index":
        _ensure_scan_state(scan_ready, action)
        indices = driver.get_index(
            class_names=step.get("class_names"),
            control_types=step.get("control_types"),
            name_regex=step.get("name_regex"),
            value_regex=step.get("value_regex"),
            only_visible=_coerce_bool(step.get("only_visible"), default=False),
            require_enabled=_coerce_bool(step.get("require_enabled"), default=False),
            min_width=step.get("min_width"),
            min_height=step.get("min_height"),
            only_focusable=_coerce_bool(step.get("only_focusable"), default=False),
            automation_id_regex=step.get("automation_id_regex"),
            omit_no_name=_coerce_bool(step.get("omit_no_name"), default=False),
            min_separator_count=_coerce_int(
                step.get("min_separator_count"),
                default=0,
                name="min_separator_count",
            ),
        )
        payload.update({"ok": True, "indices": indices})
        return payload, scan_ready

    if action == "click_index":
        _ensure_scan_state(scan_ready, action)
        result = driver.click_by_index_result(_coerce_int(step.get("index"), name="index"))
        payload.update({"ok": result.ok, "result": _result_payload(result)})
        return payload, scan_ready

    if action == "set_text":
        _ensure_scan_state(scan_ready, action)
        result = driver.set_edit_text_result(
            _coerce_int(step.get("index"), name="index"),
            _require_str(step.get("text"), "text"),
        )
        payload.update({"ok": result.ok, "result": _result_payload(result)})
        return payload, scan_ready

    if action == "type_text":
        text = _require_str(step.get("text"), "text")
        method = str(step.get("method", "paste"))
        driver.type_text(text, method=method)
        payload.update({"ok": True, "text": text, "method": method})
        return payload, scan_ready

    if action == "scroll":
        payload.update(_handle_scroll(driver, step))
        return payload, scan_ready

    if action == "tab":
        payload.update(_handle_tab(driver, step))
        return payload, scan_ready

    if action == "history":
        payload.update(_handle_history(driver, step))
        return payload, scan_ready

    if action == "zoom":
        payload.update(_handle_zoom(driver, step))
        return payload, scan_ready

    if action == "clipboard":
        payload.update(_handle_clipboard(driver, step))
        return payload, scan_ready

    if action == "click_at":
        payload.update(_handle_click_at(driver, step))
        return payload, scan_ready

    if action in {"move_mouse", "move_mouse_to_element", "move_mouse_to_position"}:
        mouse_step = dict(step)
        payload.update(_handle_move_mouse(driver, mouse_step, scan_ready=scan_ready))
        return payload, scan_ready

    if action == "url":
        payload.update({"ok": True, "url": driver.get_address_bar_url()})
        return payload, scan_ready

    if action == "title":
        payload.update({"ok": True, "title": driver.get_page_title()})
        return payload, scan_ready

    raise WorkflowError("invalid_spec", f"Unsupported action: {action}")


def _load_spec_from_args(args: argparse.Namespace) -> dict[str, Any]:
    raw_spec = args.spec_json
    if raw_spec is None:
        raw_spec = Path(args.spec_file).read_text(encoding="utf-8")
    try:
        spec = json.loads(raw_spec)
    except json.JSONDecodeError as exc:
        raise WorkflowError("invalid_json", f"Failed to parse workflow JSON: {exc}") from exc
    if not isinstance(spec, dict):
        raise WorkflowError("invalid_spec", "Workflow spec must be a JSON object.")
    return spec


def run_workflow(spec: dict[str, Any]) -> dict[str, Any]:
    browser = _normalize_browser(spec.get("browser"))
    connect_spec = _require_dict(spec.get("connect"), "connect")
    steps = _require_list(spec.get("steps"), "steps")
    artifact_dir = _artifact_dir(spec)
    driver = _connect_driver(browser, connect_spec)
    results: list[dict[str, Any]] = []
    artifacts: list[dict[str, Any]] = []
    scan_ready = False

    for index, raw_step in enumerate(steps):
        step = _require_dict(raw_step, f"steps[{index}]")
        result, scan_ready = _run_step(
            driver,
            browser,
            step,
            index,
            artifact_dir,
            artifacts,
            scan_ready=scan_ready,
        )
        results.append(result)

    return {
        "ok": True,
        "browser": browser,
        "window": _window_payload(driver),
        "artifact_dir": str(artifact_dir),
        "results": results,
        "artifacts": artifacts,
    }


def _emit_payload(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is None:
        print(text, end="")
        return
    buffer.write(text.encode("utf-8", errors="replace"))
    buffer.flush()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run NativeBrowserDriver workflows.",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--spec-json", help="Inline workflow JSON.")
    group.add_argument("--spec-file", help="Path to a workflow JSON file.")
    args = parser.parse_args()

    payload: dict[str, Any]
    exit_code = 0
    try:
        payload = run_workflow(_load_spec_from_args(args))
    except WorkflowError as exc:
        payload = _error_payload(exc.code, str(exc), exc.data)
        exit_code = 1
    except NativeBrowserError as exc:
        payload = _error_payload(exc.code, str(exc), exc.data)
        exit_code = 1
    except Exception as exc:  # pragma: no cover
        payload = _error_payload("internal_error", str(exc))
        exit_code = 1

    _emit_payload(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
