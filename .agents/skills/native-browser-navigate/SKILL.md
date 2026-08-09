---
name: native-browser-navigate
description: Navigate a live Chrome or Edge tab with this repository's NativeBrowserDriver. Use when the user wants to open a URL in the current browser window before another browser action.
---

# Native Browser Navigate

Use `skills/native-browser-usage/scripts/run_native_browser_command.py navigate`.
Resolve the runner from the repository root; do not resolve this path from an unrelated cwd.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge window_index=0 url=https://example.com wait_seconds=2`

Rules:

- `browser` and `url` are required. Never default the browser.
- `window_index` defaults to `0` when omitted. Use `launch=true` to start a new browser instead.
- Prefer `.\.venv\Scripts\python.exe` when it exists; otherwise use `python`.
- After running, report the target URL and whether the navigation completed.

Supported arguments:

- `browser`
- `window_index`
- `launch`
- `retries`
- `start_delay`
- `url`
- `wait_seconds`
