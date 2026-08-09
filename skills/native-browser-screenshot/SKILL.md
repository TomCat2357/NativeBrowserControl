---
name: native-browser-screenshot
description: Capture a screenshot from a live Chrome or Edge window with this repository's NativeBrowserDriver. Use when the user wants a window screenshot or full-screen capture saved from the current browser state.
---

# Native Browser Screenshot

Use `mcp__native-browser-control__driver_screenshot` for the browser window, or
`mcp__native-browser-control__driver_capture_full_screen` for the full screen, after creating
or selecting a session with `mcp__native-browser-control__launch_chrome`,
`mcp__native-browser-control__launch_edge`, or `mcp__native-browser-control__connect_browser`.

The repository-checkout skill under `.agents/skills/` may use the direct runner, but an
installed plugin must not resolve `skills/...` from the user's current working directory.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge window_index=0 fmt=PNG`

Rules:

- `browser` is required unless `session_id` already identifies the browser. Never default it.
- `window_index` is used with `connect_browser`; use `launch_chrome` or `launch_edge` for a new browser.
- Use `full=true` for full-screen capture; otherwise capture the browser window.
- After running, report the saved artifact path.

Supported arguments:

- `browser`
- `window_index`
- `launch`
- `retries`
- `start_delay`
- `full`
- `fmt`
- `quality`
- `file_path`
- `monitor`
