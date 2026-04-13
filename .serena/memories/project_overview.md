# NativeBrowserControl overview

- Purpose: Windows UI Automation (pywinauto/pywin32) project to control Chrome/Edge without Selenium.
- Tech stack: Python >=3.11, pywinauto, pywin32, mss, pillow, regex; packaged with setuptools/uv.
- Recommended workflow: skill scripts in `skills/native-browser-usage/` calling `native_browser_control.driver` directly.
- Code structure: `native_browser_control/` with `driver.py` and package `__init__.py`; other directories: `skills/`, `.agents/skills/`, `.claude/skills/`, `codex-prompts/`.
- Platform: Windows-only (UI Automation) and requires Chrome/Edge installed.
