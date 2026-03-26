---
name: native-browser-usage
description: Command suite for this repository's NativeBrowserDriver workflows. Use when the user wants to inspect, navigate, click, edit text, or capture screenshots in a live Chrome or Edge window from this repo.
---

# Native Browser Usage

Use the focused skills when the intent is clear:

- `$native-browser-summary`
- `$native-browser-navigate`
- `$native-browser-scan`
- `$native-browser-click`
- `$native-browser-set-text`
- `$native-browser-screenshot`

Shared rules:

- `browser` is always required. Never default it.
- `window_index` defaults to `0` when omitted. Use `launch=true` to start a new browser instead.
- `click` and `set-text` should re-scan inside the same invocation. Do not trust indexes from an earlier run unless the user explicitly insists.
- The shared runner is `skills/native-browser-usage/scripts/run_native_browser_command.py`.
- Prefer `.\.venv\Scripts\python.exe` when it exists; otherwise use `python`.

Example:

`$native-browser-scan browser=edge window_index=0 control_type=Button only_visible=true`
