---
name: native-browser-click
description: Click an element in a live Chrome or Edge window with this repository's NativeBrowserDriver. Use when the user wants to click by current scan index or by filters such as control type, regex, or automation id.
---

# Native Browser Click

Use `skills/native-browser-usage/scripts/run_native_browser_command.py click`.
Resolve the runner from the repository root; do not resolve this path from an unrelated cwd.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge name_regex=^(検索|Search)$ control_type=Button only_visible=true`

Rules:

- `browser` is required. Never default it.
- `window_index` defaults to `0` when omitted. Use `launch=true` to start a new browser instead.
- Require either `index` or at least one matcher such as `name_regex`, `automation_id_regex`, `control_type`, `control_types`, or `class_names`.
- When matcher fields are present, the command re-scans, filters, and clicks the filtered `index`. If `index` is omitted, it clicks the first filtered match (`0`).
- Prefer matcher fields over raw indexes when the user does not insist on an index.
- Prefer `.\.venv\Scripts\python.exe` when it exists; otherwise use `python`.

Supported arguments:

- `browser`
- `window_index`
- `launch`
- `retries`
- `start_delay`
- `index`
- `control_type`
- `control_types`
- `class_names`
- `title`
- `name_regex`
- `automation_id_regex`
- `max_elements`
- `only_visible`
- `require_enabled`
- `only_focusable`
- `min_width`
- `min_height`
- `omit_no_name`
- `min_separator_count`
