---
name: native-browser-click
description: Click an element in a live Chrome or Edge window with this repository's NativeBrowserDriver. Use when the user wants to click by current scan index or by filters such as control type, regex, or automation id.
---

# Native Browser Click

Use `mcp__native-browser-control__driver_click_by_index` after creating or selecting a session.
For matcher fields, call `mcp__native-browser-control__driver_scan_page_elements`, then
`mcp__native-browser-control__driver_filter_current_elements`, read the filtered indexes with
`mcp__native-browser-control__driver_get_current_elements_list`, and click the selected index.
Create or select a session with `mcp__native-browser-control__launch_chrome`,
`mcp__native-browser-control__launch_edge`, or `mcp__native-browser-control__connect_browser`.

The repository-checkout skill under `.agents/skills/` may use the direct runner, but an
installed plugin must not resolve `skills/...` from the user's current working directory.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge name_regex=^(検索|Search)$ control_type=Button only_visible=true`

Rules:

- `browser` is required unless `session_id` already identifies the browser. Never default it.
- `window_index` is used with `connect_browser`; use `launch_chrome` or `launch_edge` for a new browser.
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
