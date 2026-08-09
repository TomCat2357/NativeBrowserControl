---
name: native-browser-screenshot
description: Capture a screenshot from a live Chrome or Edge window with this repository's NativeBrowserDriver. Use when the user wants a window screenshot or full-screen capture saved from the current browser state.
---

# Native Browser Screenshot

Use `skills/native-browser-usage/scripts/run_native_browser_command.py screenshot`.
Resolve the runner from the repository root; do not resolve this path from an unrelated cwd.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=edge window_index=0 fmt=PNG`

Rules:

- `browser` is required. Never default it.
- `window_index` defaults to `0` when omitted. Use `launch=true` to start a new browser instead.
- Use `full=true` for full-screen capture; otherwise capture the browser window.
- Prefer `.\.venv\Scripts\python.exe` when it exists; otherwise use `python`.
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
- `artifact_dir`
