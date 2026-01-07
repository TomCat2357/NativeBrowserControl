"""Utility helpers for routing script output."""

from __future__ import annotations

import argparse
import io
import logging
import sys
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
from typing import Any, Callable, Iterable, Literal

OutputTarget = Literal["stdout", "stderr", "silent"]


@dataclass
class WorkflowResult:
    """ワークフローの実行結果を格納する統一形式"""
    exit_code: int
    summary: dict[str, Any]
    log: str = ""


class _OutputTee(io.TextIOBase):
    def __init__(self, *targets: io.StringIO) -> None:
        self._targets = targets

    def write(self, text: str) -> int:
        for target in self._targets:
            target.write(text)
        return len(text)

    def flush(self) -> None:
        for target in self._targets:
            target.flush()


def _emit(target: OutputTarget, text: str) -> None:
    if not text:
        return
    if target == "stdout":
        sys.stdout.write(text)
    elif target == "stderr":
        sys.stderr.write(text)


def add_output_argument(parser: argparse.ArgumentParser, *, default: OutputTarget = "stdout") -> None:
    """Attach common output arguments to the given parser.

    ``--output`` sets both stdout/stderr together. ``--stdout`` and ``--stderr``
    override each stream individually.
    """

    parser.add_argument(
        "--output",
        choices=["stdout", "stderr", "silent"],
        default=default,
        help="stdout/stderrの出力先を一括指定します (stdout / stderr / silent)",
    )
    parser.add_argument(
        "--stdout",
        choices=["stdout", "stderr", "silent"],
        default=None,
        help="標準出力の出力先を指定します (未指定時は--output)",
    )
    parser.add_argument(
        "--stderr",
        choices=["stdout", "stderr", "silent"],
        default=None,
        help="標準エラーの出力先を指定します (未指定時は--output)",
    )


def resolve_output_targets(
    output: OutputTarget,
    *,
    stdout_target: OutputTarget | None = None,
    stderr_target: OutputTarget | None = None,
) -> tuple[OutputTarget, OutputTarget]:
    """Resolve stdout/stderr targets using per-stream overrides."""

    return stdout_target or output, stderr_target or output


def route_output(
    func: Callable[[], None],
    target: OutputTarget = "stdout",
    *,
    stderr_target: OutputTarget | None = None,
) -> str:
    """Capture ``func`` output and optionally write it to the selected target(s)."""

    stdout_target = target
    if stderr_target is None:
        stderr_target = stdout_target

    combined = io.StringIO()
    stdout_buffer = io.StringIO()
    stderr_buffer = io.StringIO()
    stdout_tee = _OutputTee(combined, stdout_buffer)
    stderr_tee = _OutputTee(combined, stderr_buffer)

    with redirect_stdout(stdout_tee), redirect_stderr(stderr_tee):
        func()

    combined_content = combined.getvalue()
    stdout_content = stdout_buffer.getvalue()
    stderr_content = stderr_buffer.getvalue()

    if stdout_target == stderr_target:
        _emit(stdout_target, combined_content)
    else:
        _emit(stdout_target, stdout_content)
        _emit(stderr_target, stderr_content)
    return combined_content


def emit_lines(target: OutputTarget, lines: Iterable[str]) -> str:
    """Emit pre-rendered lines to the requested output target."""

    text = "\n".join(lines)
    if target != "silent":
        _emit(target, text + ("" if text.endswith("\n") else "\n"))
    return text


def setup_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """ワークフロー用のロガーを設定する。

    Args:
        name: ロガー名（通常は__name__）
        level: ログレベル（デフォルト: INFO）

    Returns:
        設定されたロガー
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 既存のハンドラをクリア（重複防止）
    logger.handlers.clear()

    # コンソールハンドラを追加
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    # フォーマッタを設定
    formatter = logging.Formatter('%(message)s')
    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.propagate = False

    return logger


def add_logging_argument(parser: argparse.ArgumentParser) -> None:
    """ログレベル設定引数をパーサーに追加する。

    Args:
        parser: ArgumentParserインスタンス
    """
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="INFO",
        help="ログレベルを指定します (DEBUG / INFO / WARNING / ERROR)",
    )
