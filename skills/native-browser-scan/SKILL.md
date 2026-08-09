---
name: native-browser-scan
description: Scan browser elements in a live Chrome or Edge window with this repository's NativeBrowserDriver. Use when the user wants an indexed list of buttons, edits, links, or other UIA elements before interacting with the page.
---

# Native Browser Scan

Use `mcp__native-browser-control__driver_scan_page_elements`, followed by
`mcp__native-browser-control__driver_get_current_elements_list`. If matcher fields are
needed, call `mcp__native-browser-control__driver_filter_current_elements` between them.
Create or select a session with `mcp__native-browser-control__launch_chrome`,
`mcp__native-browser-control__launch_edge`, or `mcp__native-browser-control__connect_browser`.

The repository-checkout skill under `.agents/skills/` may use the direct runner, but an
installed plugin must not resolve `skills/...` from the user's current working directory.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge window_index=0 control_type=Button only_visible=true max_elements=200`

Rules:

- `browser` is required unless `session_id` already identifies the browser. Never default it.
- `window_index` is used with `connect_browser`; use `launch_chrome` or `launch_edge` for a new browser.
- Return the indexed scan output. If a filter was supplied, make it clear that the indexes belong to the filtered result, not an earlier scan.
- Recommend `$native-browser-click` or `$native-browser-set-text` for follow-up actions instead of relying on stale indexes.

Supported arguments:

- `browser`
- `window_index`
- `launch`
- `retries`
- `start_delay`
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
