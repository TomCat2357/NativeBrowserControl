---
name: native-browser-connect
description: Connect to or launch a Chrome or Edge window with the bundled direct runner and return its initial summary.
---

# Native Browser Connect

Use the absolute path to `skills/native-browser-usage/scripts/run_native_browser_command.py connect`, resolved from this skill's installed plugin root. In a repository checkout, the relative path in the examples is valid; never resolve it from an unrelated cwd.
This is a one-shot command: it connects to the selected window (or launches a
new browser) and returns a summary. Later commands connect again, so no MCP
session or cross-process state is required.

Rules:

- `browser` is required and must be `chrome` or `edge`.
- Use `window_index` for an existing window, or `launch=true` for a new one.
- If the runner returns `dependency_missing`, run `uv sync --project <project_root>`
  and use the returned `recommended_runner` (`uv run --project ...`) for the retry.

Examples:

```powershell
.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_command.py connect --browser chrome --window-index 0
.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_command.py connect --browser edge --launch
```
