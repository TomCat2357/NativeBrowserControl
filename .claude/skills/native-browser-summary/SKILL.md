---
name: native-browser-summary
description: Get a live Chrome or Edge browser summary from this repository's NativeBrowserDriver.
disable-model-invocation: true
allowed-tools: Bash, Read, Grep, Glob
---

Use `skills/native-browser-usage/scripts/run_native_browser_command.py summary`.

Parse `$ARGUMENTS` as `key=value` pairs. Example:

`browser=chrome window_index=0 max_text_len=80`

Rules:

- `browser` is required. Never default it.
- `window_index` defaults to `0` when omitted. Use `launch=true` to start a new browser instead.
- Prefer `.\.venv\Scripts\python.exe` when it exists; otherwise use `python`.
- Run the command and summarize the returned browser state.
