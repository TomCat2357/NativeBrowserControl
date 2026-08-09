---
name: native-browser-navigate
description: Navigate a live Chrome or Edge tab with this repository's NativeBrowserDriver. Use when the user wants to open a URL in the current browser window before another browser action.
---

# Native Browser Navigate

Use `mcp__native-browser-control__driver_navigate` after creating or selecting a session with
`mcp__native-browser-control__launch_chrome`, `mcp__native-browser-control__launch_edge`,
or `mcp__native-browser-control__connect_browser`.

The repository-checkout skill under `.agents/skills/` may use the direct runner, but an
installed plugin must not resolve `skills/...` from the user's current working directory.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge window_index=0 url=https://example.com timeout_s=5`

Rules:

- `browser` and `url` are required unless `session_id` already identifies the browser. Never default the browser.
- `window_index` is used with `connect_browser`; use `launch_chrome` or `launch_edge` for a new browser.
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

If an additional wait is needed after navigation, call
`mcp__native-browser-control__driver_wait_for_idle` with `seconds`.
