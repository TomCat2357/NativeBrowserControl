"""Utility helpers for routing script output."""

from __future__ import annotations

import argparse
import io
import sys
from contextlib import redirect_stderr, redirect_stdout
from typing import Callable, Iterable, Literal

OutputTarget = Literal["stdout", "stderr", "silent"]


def add_output_argument(parser: argparse.ArgumentParser, *, default: OutputTarget = "stdout") -> None:
    """Attach a common ``--output`` argument to the given parser.

    The value controls where captured output is sent:
    - ``stdout`` (default): write to standard output
    - ``stderr``: write to standard error
    - ``silent``: do not emit, only return captured text
    """

    parser.add_argument(
        "--output",
        choices=["stdout", "stderr", "silent"],
        default=default,
        help="出力先を選択します (stdout / stderr / silent)",
    )


def route_output(func: Callable[[], None], target: OutputTarget = "stdout") -> str:
    """Capture ``func`` output and optionally write it to the selected target."""

    buffer = io.StringIO()
    with redirect_stdout(buffer), redirect_stderr(buffer):
        func()

    content = buffer.getvalue()
    if target == "stdout":
        sys.stdout.write(content)
    elif target == "stderr":
        sys.stderr.write(content)
    return content


def emit_lines(target: OutputTarget, lines: Iterable[str]) -> str:
    """Emit pre-rendered lines to the requested output target."""

    text = "\n".join(lines)
    if target == "stdout":
        sys.stdout.write(text + ("" if text.endswith("\n") else "\n"))
    elif target == "stderr":
        sys.stderr.write(text + ("" if text.endswith("\n") else "\n"))
    return text
