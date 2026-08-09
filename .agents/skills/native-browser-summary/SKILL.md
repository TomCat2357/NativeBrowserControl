---
name: native-browser-summary
description: Get a live Chrome or Edge browser summary from this repository's NativeBrowserDriver. Use when the user wants the current title, URL, or a quick browser state check before taking the next action.
---

# Native Browser Summary

Use `skills/native-browser-usage/scripts/run_native_browser_command.py summary`.
Resolve the runner from the repository root; do not resolve this path from an unrelated cwd.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=chrome window_index=0 max_text_len=80`

Rules:

- `browser` is required. Never default it.
- `window_index` defaults to `0` when omitted. Use `launch=true` to start a new browser instead.
- Prefer `.\.venv\Scripts\python.exe` when it exists; otherwise use `python`.
- Run the command and report the returned summary fields concisely.

Supported arguments:

- `browser`
- `window_index`
- `launch`
- `retries`
- `start_delay`
- `max_text_len`
