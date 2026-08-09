---
name: native-browser-summary
description: Get a live Chrome or Edge browser summary from this repository's NativeBrowserDriver. Use when the user wants the current title, URL, or a quick browser state check before taking the next action.
---

# Native Browser Summary

Use the MCP tools exposed by this plugin. Start or connect a session with
`mcp__native-browser-control__launch_chrome`, `mcp__native-browser-control__launch_edge`,
or `mcp__native-browser-control__connect_browser`, then call
`mcp__native-browser-control__driver_get_browser_summary` with `browser` or `session_id`.

The repository-checkout skill under `.agents/skills/` may use the direct runner, but an
installed plugin must not resolve `skills/...` from the user's current working directory.

Interpret inline `key=value` arguments near the skill mention. Example:

`browser=chrome window_index=0 max_text_len=80`

Rules:

- `browser` is required unless `session_id` already identifies the browser. Never default it.
- `window_index` is used with `connect_browser`; use `launch_chrome` or `launch_edge` for a new browser.
- Run the command and report the returned summary fields concisely.

Supported arguments:

- `browser`
- `window_index`
- `launch`
- `retries`
- `start_delay`
- `max_text_len`
