---
name: native-browser-screenshot
description: Capture a screenshot from a live Chrome or Edge window with the bundled direct runner. Use when the user wants a window screenshot or full-screen capture saved from the current browser state.
---

# Native Browser Screenshot

Use `skills/native-browser-usage/scripts/run_native_browser_command.py screenshot`.
Use `full=true` for the full screen; otherwise it captures the browser window.
When this skill is installed as a plugin, resolve this script from the plugin root as an absolute path; do not resolve `skills/...` from cwd.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge window_index=0 fmt=PNG`

Rules:

- `browser` is required. Never default it.
- `window_index` selects an existing window; use `launch=true` to start a new browser.
- This direct runner is the supported path when MCP tools are unavailable or show no tools.
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
