---
name: native-browser-set-text
description: Set text in an Edit control inside a live Chrome or Edge window with this repository's NativeBrowserDriver. Use when the user wants to fill a field by current scan index or by filters such as control type, regex, or automation id.
---

# Native Browser Set Text

Use `skills/native-browser-usage/scripts/run_native_browser_command.py set-text`.
Resolve the runner from the repository root; do not resolve this path from an unrelated cwd.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=chrome control_type=Edit name_regex=search text=NativeBrowserDriver`

Rules:

- `browser` and `text` are required. Never default the browser.
- `window_index` defaults to `0` when omitted. Use `launch=true` to start a new browser instead.
- Require either `index` or at least one matcher such as `name_regex`, `automation_id_regex`, `control_type`, `control_types`, or `class_names`.
- When matcher fields are present, the command re-scans, filters, and applies `index` within the filtered result. If `index` is omitted, it writes to the first filtered match (`0`).
- Prefer matcher fields over raw indexes when the user does not insist on an index.
- Prefer `.\.venv\Scripts\python.exe` when it exists; otherwise use `python`.

Supported arguments:

- `browser`
- `window_index`
- `launch`
- `retries`
- `start_delay`
- `index`
- `text`
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
