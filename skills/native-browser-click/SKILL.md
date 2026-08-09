---
name: native-browser-click
description: Click an element in a live Chrome or Edge window with the bundled direct runner. Use when the user wants to click by current scan index or by filters such as control type, regex, or automation id.
---

# Native Browser Click

Use `skills/native-browser-usage/scripts/run_native_browser_command.py click`.
The command re-scans and filters in the same invocation when matcher fields are supplied.
When this skill is installed as a plugin, resolve this script from the plugin root as an absolute path; do not resolve `skills/...` from cwd.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge name_regex=^(検索|Search)$ control_type=Button only_visible=true`

Rules:

- `browser` is required. Never default it.
- `window_index` selects an existing window; use `launch=true` to start a new browser.
- This direct runner is the supported path when MCP tools are unavailable or show no tools.
- Require either `index` or at least one matcher such as `name_regex`, `automation_id_regex`, `control_type`, `control_types`, or `class_names`.
- When matcher fields are present, the command re-scans, filters, and clicks the filtered `index`. If `index` is omitted, it clicks the first filtered match (`0`).
- Prefer matcher fields over raw indexes when the user does not insist on an index.

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
