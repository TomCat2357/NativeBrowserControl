#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = Path(__file__).resolve().parents[3]

for path in (SCRIPT_DIR, REPO_ROOT):
    text = str(path)
    if text not in sys.path:
        sys.path.insert(0, text)

from run_native_browser_workflow import (  # noqa: E402
    NativeBrowserError,
    WorkflowError,
    run_workflow,
)


class CommandSpecError(Exception):
    def __init__(self, message: str, data: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.data = data or {}


def _emit_payload(payload: dict[str, Any]) -> None:
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    buffer = getattr(sys.stdout, "buffer", None)
    if buffer is None:
        print(text, end="")
        return
    buffer.write(text.encode("utf-8", errors="replace"))
    buffer.flush()


def _error_payload(code: str, message: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"ok": False, "error": {"code": code, "message": message}}
    if data:
        payload["error"]["data"] = data
    return payload


def _command_error_data(exc: WorkflowError) -> dict[str, Any] | None:
    data = dict(exc.data) if isinstance(exc.data, dict) else None
    if exc.code != "dependency_missing" or data is None:
        return data

    project_root = data.get("project_root")
    if project_root:
        command_runner = (SCRIPT_DIR / "run_native_browser_command.py").resolve()
        data["recommended_runner"] = (
            f'uv run --project "{project_root}" python "{command_runner}"'
        )
    return data


def _csv_list(raw: str | None) -> list[str] | None:
    if raw is None:
        return None
    items = [item.strip() for item in raw.split(",")]
    values = [item for item in items if item]
    return values or None


def _merge_control_types(args: argparse.Namespace) -> list[str] | None:
    values: list[str] = []
    if getattr(args, "control_type", None):
        values.append(str(args.control_type))
    csv_values = _csv_list(getattr(args, "control_types", None))
    if csv_values:
        for value in csv_values:
            if value not in values:
                values.append(value)
    return values or None


def _build_connect_spec(args: argparse.Namespace) -> dict[str, Any]:
    if args.launch and args.window_index is not None:
        raise CommandSpecError(
            "`--launch` and `--window-index` cannot be used together.",
            {"fields": ["launch", "window_index"]},
        )

    spec: dict[str, Any] = {"retries": args.retries}
    if args.launch:
        spec["launch"] = True
        spec["start_delay"] = args.start_delay
        return spec

    spec["window_index"] = 0 if args.window_index is None else args.window_index
    if args.require_visible:
        spec["require_visible"] = True
    if args.exclude_minimized:
        spec["exclude_minimized"] = True
    return spec


def _build_scan_step(args: argparse.Namespace) -> dict[str, Any]:
    step: dict[str, Any] = {
        "action": "scan",
        "max_elements": args.max_elements,
    }
    if args.control_type:
        step["control_type"] = args.control_type
    if getattr(args, "title", None):
        step["title"] = args.title
    return step


def _build_filter_step(args: argparse.Namespace) -> dict[str, Any] | None:
    step: dict[str, Any] = {
        "action": "filter",
        "update_mode": "overwrite",
        "output": "simple",
    }

    control_types = _merge_control_types(args)
    if control_types:
        step["control_types"] = control_types

    class_names = _csv_list(getattr(args, "class_names", None))
    if class_names:
        step["class_names"] = class_names

    if getattr(args, "name_regex", None):
        step["name_regex"] = args.name_regex
    if getattr(args, "automation_id_regex", None):
        step["automation_id_regex"] = args.automation_id_regex
    if args.only_visible:
        step["only_visible"] = True
    if args.require_enabled:
        step["require_enabled"] = True
    if args.only_focusable:
        step["only_focusable"] = True
    if args.min_width is not None:
        step["min_width"] = args.min_width
    if args.min_height is not None:
        step["min_height"] = args.min_height
    if args.omit_no_name:
        step["omit_no_name"] = True
    if args.min_separator_count:
        step["min_separator_count"] = args.min_separator_count

    return None if len(step) == 3 else step


def _has_target(args: argparse.Namespace) -> bool:
    return getattr(args, "index", None) is not None or _build_filter_step(args) is not None


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run agent-friendly NativeBrowserDriver commands.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    def add_common_options(command: argparse.ArgumentParser) -> None:
        command.add_argument("--browser", required=True, choices=("chrome", "edge"))
        command.add_argument("--window-index", type=int)
        command.add_argument("--launch", action="store_true")
        command.add_argument("--retries", type=int, default=3)
        command.add_argument("--start-delay", type=float, default=1.0)
        command.add_argument("--require-visible", action="store_true")
        command.add_argument("--exclude-minimized", action="store_true")
        command.add_argument("--artifact-dir")

    def add_scan_like_options(command: argparse.ArgumentParser) -> None:
        command.add_argument("--control-type")
        command.add_argument("--title")
        command.add_argument("--max-elements", type=int, default=200)

    def add_match_options(command: argparse.ArgumentParser) -> None:
        command.add_argument("--control-types")
        command.add_argument("--class-names")
        command.add_argument("--name-regex")
        command.add_argument("--automation-id-regex")
        command.add_argument("--only-visible", action="store_true")
        command.add_argument("--require-enabled", action="store_true")
        command.add_argument("--only-focusable", action="store_true")
        command.add_argument("--min-width", type=int)
        command.add_argument("--min-height", type=int)
        command.add_argument("--omit-no-name", action="store_true")
        command.add_argument("--min-separator-count", type=int, default=0)

    connect = subparsers.add_parser(
        "connect",
        help="Connect to a browser window and return its summary.",
    )
    add_common_options(connect)
    connect.add_argument("--max-text-len", type=int, default=50)

    summary = subparsers.add_parser("summary", help="Get a browser summary.")
    add_common_options(summary)
    summary.add_argument("--max-text-len", type=int, default=50)

    navigate = subparsers.add_parser("navigate", help="Navigate the current tab.")
    add_common_options(navigate)
    navigate.add_argument("--url", required=True)
    navigate.add_argument("--timeout-s", type=float)
    navigate.add_argument("--interval-s", type=float)
    navigate.add_argument("--wait-seconds", type=float)

    scan = subparsers.add_parser("scan", help="Scan elements and optionally filter them.")
    add_common_options(scan)
    add_scan_like_options(scan)
    add_match_options(scan)

    click = subparsers.add_parser("click", help="Click by raw scan index or first filtered match.")
    add_common_options(click)
    add_scan_like_options(click)
    add_match_options(click)
    click.add_argument("--index", type=int)

    set_text = subparsers.add_parser(
        "set-text",
        help="Set text by raw scan index or first filtered match.",
    )
    add_common_options(set_text)
    add_scan_like_options(set_text)
    add_match_options(set_text)
    set_text.add_argument("--index", type=int)
    set_text.add_argument("--text", required=True)

    screenshot = subparsers.add_parser("screenshot", help="Take a screenshot.")
    add_common_options(screenshot)
    screenshot.add_argument("--full", action="store_true")
    screenshot.add_argument("--fmt", default="PNG", choices=("PNG", "JPEG"))
    screenshot.add_argument("--quality", type=int, default=90)
    screenshot.add_argument("--file-path")
    screenshot.add_argument("--monitor", type=int, default=0)

    return parser


def build_spec(args: argparse.Namespace) -> dict[str, Any]:
    connect = _build_connect_spec(args)
    steps: list[dict[str, Any]]

    if args.command in {"connect", "summary"}:
        steps = [{"action": "summary", "max_text_len": args.max_text_len}]
    elif args.command == "navigate":
        steps = [{"action": "navigate", "url": args.url}]
        if args.timeout_s is not None:
            steps[0]["timeout_s"] = args.timeout_s
        if args.interval_s is not None:
            steps[0]["interval_s"] = args.interval_s
        if args.wait_seconds is not None:
            steps.append({"action": "wait", "seconds": args.wait_seconds})
    elif args.command == "scan":
        steps = [_build_scan_step(args)]
        filter_step = _build_filter_step(args)
        if filter_step is not None:
            steps.append(filter_step)
    elif args.command == "click":
        if not _has_target(args):
            raise CommandSpecError(
                "`click` requires `--index` or at least one filter argument.",
                {"fields": ["index", "control_type", "control_types", "class_names", "name_regex"]},
            )
        steps = [_build_scan_step(args)]
        filter_step = _build_filter_step(args)
        target_index = args.index if args.index is not None else 0
        if filter_step is not None:
            steps.append(filter_step)
        steps.append({"action": "click_index", "index": target_index})
    elif args.command == "set-text":
        if not _has_target(args):
            raise CommandSpecError(
                "`set-text` requires `--index` or at least one filter argument.",
                {"fields": ["index", "control_type", "control_types", "class_names", "name_regex"]},
            )
        steps = [_build_scan_step(args)]
        filter_step = _build_filter_step(args)
        target_index = args.index if args.index is not None else 0
        if filter_step is not None:
            steps.append(filter_step)
        steps.append({"action": "set_text", "index": target_index, "text": args.text})
    elif args.command == "screenshot":
        step: dict[str, Any] = {
            "action": "full_screenshot" if args.full else "screenshot",
            "fmt": args.fmt,
            "quality": args.quality,
        }
        if args.file_path:
            step["file_path"] = args.file_path
        if args.full:
            step["monitor"] = args.monitor
        steps = [step]
    else:  # pragma: no cover
        raise CommandSpecError(f"Unsupported command: {args.command}")

    spec: dict[str, Any] = {
        "browser": args.browser,
        "connect": connect,
        "steps": steps,
    }
    if args.artifact_dir:
        spec["artifact_dir"] = args.artifact_dir
    return spec


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    payload: dict[str, Any]
    exit_code = 0
    try:
        payload = run_workflow(build_spec(args))
    except CommandSpecError as exc:
        payload = _error_payload("invalid_command", str(exc), exc.data)
        exit_code = 1
    except WorkflowError as exc:
        payload = _error_payload(exc.code, str(exc), _command_error_data(exc))
        exit_code = 1
    except NativeBrowserError as exc:
        payload = _error_payload(exc.code, str(exc), getattr(exc, "data", None))
        exit_code = 1
    except Exception as exc:  # pragma: no cover
        payload = _error_payload("internal_error", str(exc))
        exit_code = 1

    _emit_payload(payload)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
