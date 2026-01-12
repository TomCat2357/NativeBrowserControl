# Code style and conventions

- Language: Python (>=3.13).
- Style observed: module-level docstrings in Japanese; type hints used (`dict[str, Any] | None`, etc.).
- JSON serialization uses `ensure_ascii=False` for Japanese messages.
- Comments are concise and in Japanese; constants like `__version__` defined at module scope.
- No explicit formatter/linter config found; follow existing style in `native_browser_control/core/*.py`.
