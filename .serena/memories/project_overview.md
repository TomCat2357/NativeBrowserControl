# NativeBrowserControl overview

- Purpose: Windows UI Automation (pywinauto/pywin32) MCP server to control Chrome/Edge without Selenium via stdio.
- Tech stack: Python >=3.13, mcp, pywinauto, pywin32, mss, pillow; packaged with setuptools/uv.
- Entry point: `native-browser-control` -> `native_browser_control.core.server:main`.
- Usage modes: Claude Code plugin or direct CLI.
- Code structure (actual repo): `native_browser_control/` with `core/` (driver + server) and package `__init__.py`; other directories: `commands/`, `skills/`, `docs/`, `.claude-plugin/`.
- Platform: Windows-only (UI Automation) and requires Chrome/Edge installed.
