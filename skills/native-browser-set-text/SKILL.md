---
name: native-browser-set-text
description: Set text in an Edit control inside a live Chrome or Edge window with this repository's NativeBrowserDriver. Use when the user wants to fill a field by current scan index or by filters such as control type, regex, or automation id.
---

# Native Browser Set Text

Use `mcp__native-browser-control__driver_set_edit_text` after creating or selecting a session.
For matcher fields, call `mcp__native-browser-control__driver_scan_page_elements`, then
`mcp__native-browser-control__driver_filter_current_elements`, read the filtered indexes with
`mcp__native-browser-control__driver_get_current_elements_list`, and pass the selected index
and `text` to `driver_set_edit_text`.
Create or select a session with `mcp__native-browser-control__launch_chrome`,
`mcp__native-browser-control__launch_edge`, or `mcp__native-browser-control__connect_browser`.

The repository-checkout skill under `.agents/skills/` may use the direct runner, but an
installed plugin must not resolve `skills/...` from the user's current working directory.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=chrome control_type=Edit name_regex=search text=NativeBrowserDriver`

Rules:

- `browser` and `text` are required unless `session_id` already identifies the browser. Never default the browser.
- `window_index` is used with `connect_browser`; use `launch_chrome` or `launch_edge` for a new browser.
- Require either `index` or at least one matcher such as `name_regex`, `automation_id_regex`, `control_type`, `control_types`, or `class_names`.
- When matcher fields are present, the command re-scans, filters, and applies `index` within the filtered result. If `index` is omitted, it writes to the first filtered match (`0`).
- Prefer matcher fields over raw indexes when the user does not insist on an index.

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
