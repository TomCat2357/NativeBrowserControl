---
name: native-browser-navigate
description: Navigate a live Chrome or Edge tab with the bundled direct runner. Use when the user wants to open a URL in the current browser window before another browser action.
---

# Native Browser Navigate

Use `skills/native-browser-usage/scripts/run_native_browser_command.py navigate`.
When this skill is installed as a plugin, resolve this script from the plugin root as an absolute path; do not resolve `skills/...` from cwd.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge window_index=0 url=https://example.com timeout_s=5`

Rules:

- `browser` and `url` are required. Never default the browser.
- `window_index` selects an existing window; use `launch=true` to start a new browser.
- This direct runner is the supported path when MCP tools are unavailable or show no tools.
- `timeout_s` and `interval_s` are passed to the driver; `wait_seconds` adds a separate idle wait.
- After running, report the target URL and whether the navigation completed.

Supported arguments:

- `browser`
- `window_index`
- `launch`
- `retries`
- `start_delay`
- `url`
- `timeout_s`
- `interval_s`

If an additional wait is needed after navigation, pass `wait_seconds` to the command.
