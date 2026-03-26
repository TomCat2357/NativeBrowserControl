---
name: native-browser-screenshot
description: Capture a screenshot from a live Chrome or Edge window with this repository's NativeBrowserDriver.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob
---

Use `skills/native-browser-usage/scripts/run_native_browser_command.py screenshot`.

Parse `$ARGUMENTS` as `key=value` pairs. Example:

`browser=edge window_index=0 fmt=PNG`

Rules:

- `browser` is required. Never default it.
- `window_index` defaults to `0` when omitted. Use `launch=true` to start a new browser instead.
- Use `full=true` for full-screen capture; otherwise capture the browser window.
- Prefer `.\.venv\Scripts\python.exe` when it exists; otherwise use `python`.
- After running, report the saved artifact path.
