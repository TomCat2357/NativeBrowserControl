---
name: native-browser-scan
description: Scan browser elements in a live Chrome or Edge window with the bundled direct runner. Use when the user wants an indexed list of buttons, edits, links, or other UIA elements before interacting with the page.
---

# Native Browser Scan

Use `skills/native-browser-usage/scripts/run_native_browser_command.py scan`.
The command performs scan and filter in one invocation when matcher fields are supplied.
When this skill is installed as a plugin, resolve this script from the plugin root as an absolute path; do not resolve `skills/...` from cwd.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge window_index=0 control_type=Button only_visible=true max_elements=200`

Rules:

- `browser` is required. Never default it.
- `window_index` selects an existing window; use `launch=true` to start a new browser.
- This direct runner is the supported path when MCP tools are unavailable or show no tools.
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
