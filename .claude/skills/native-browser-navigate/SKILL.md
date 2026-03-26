---
name: native-browser-navigate
description: Navigate a live Chrome or Edge tab with this repository's NativeBrowserDriver.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob
---

Use `skills/native-browser-usage/scripts/run_native_browser_command.py navigate`.

Parse `$ARGUMENTS` as `key=value` pairs. Example:

`browser=edge window_index=0 url=https://example.com wait_seconds=2`

Rules:

- `browser` and `url` are required. Never default the browser.
- `window_index` defaults to `0` when omitted. Use `launch=true` to start a new browser instead.
- Prefer `.\.venv\Scripts\python.exe` when it exists; otherwise use `python`.
- Run the command and report the navigation result.
