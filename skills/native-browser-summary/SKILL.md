---
name: native-browser-summary
description: Get a live Chrome or Edge browser summary with the bundled direct runner. Use when the user wants the current title, URL, or a quick browser state check before taking the next action.
---

# Native Browser Summary

Use `skills/native-browser-usage/scripts/run_native_browser_command.py summary`.
Use `connect` instead when the intent is explicitly to connect and return the initial summary.
When this skill is installed as a plugin, resolve this script from the plugin root as an absolute path; do not resolve `skills/...` from cwd.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=chrome window_index=0 max_text_len=80`

Rules:

- `browser` is required. Never default it.
- `window_index` selects an existing window; use `launch=true` to start a new browser.
- This direct runner is the supported path when MCP tools are unavailable or show no tools.
- Run the command and report the returned summary fields concisely.

Supported arguments:

- `browser`
- `window_index`
- `launch`
- `retries`
- `start_delay`
- `max_text_len`
