---
name: native-browser-scan
description: Scan browser elements in a live Chrome or Edge window with this repository's NativeBrowserDriver.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob
---

Use `skills/native-browser-usage/scripts/run_native_browser_command.py scan`.

Parse `$ARGUMENTS` as `key=value` pairs. Example:

`browser=edge window_index=0 control_type=Button only_visible=true max_elements=200`

Rules:

- `browser` is required. Never default it.
- `window_index` defaults to `0` when omitted. Use `launch=true` to start a new browser instead.
- Prefer `.\.venv\Scripts\python.exe` when it exists; otherwise use `python`.
- Return the indexed scan result and make it clear when a filter changed the visible indexes.
- Recommend `/native-browser-click` or `/native-browser-set-text` for follow-up actions instead of trusting stale indexes.
