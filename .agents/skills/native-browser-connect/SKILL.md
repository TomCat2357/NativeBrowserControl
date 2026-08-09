---
name: native-browser-connect
description: Connect to or launch Chrome or Edge with the repository's direct runner and return its initial summary.
---

Use the absolute path to `skills/native-browser-usage/scripts/run_native_browser_command.py connect`, resolved from this skill's installed plugin root. In a repository checkout, the relative path in the example is valid; never resolve it from an unrelated cwd.

Rules:

- `browser` is required; never default it.
- Use `window_index` for an existing window or `launch=true` for a new browser.
- This is a one-shot connection and summary; later commands connect again.
- If the runner returns `dependency_missing`, run `uv sync --project <project_root>` and retry with the returned `recommended_runner`.

Example:

`$native-browser-connect browser=chrome launch=true max_text_len=80`
