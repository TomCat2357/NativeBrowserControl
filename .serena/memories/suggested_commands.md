# Suggested commands (Windows PowerShell)

## Setup
- `python -m venv .venv`
- `.\.venv\Scripts\activate`
- `pip install -e .`

## Workflows
- `.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_workflow.py --spec-file .\workflow.json`
- `.\.venv\Scripts\python.exe .\skills\native-browser-usage\scripts\run_native_browser_command.py summary --browser chrome --window-index 0`
