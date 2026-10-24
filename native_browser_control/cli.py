"""`native-browser-control` コマンドの入口。

MCP サーバーは任意機能 (`pip install "native-browser-control[mcp]"`) のため、
`mcp` 未導入時は server を import せずに導入方法を案内する。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

from native_browser_control import __version__

MCP_SERVER_NAME = "native-browser-control"
MCP_MISSING_MESSAGE = (
    "MCP サーバー機能は未インストールです。利用する場合は "
    '`pip install "native-browser-control[mcp]"` または `uv sync --extra mcp` を実行してください。'
)


def mcp_available() -> bool:
    return importlib.util.find_spec("mcp") is not None


def build_mcp_config(python_executable: str | None = None) -> dict:
    """現在の Python 環境のサーバーを起動する .mcp.json 定義を返す。"""
    return {
        "mcpServers": {
            MCP_SERVER_NAME: {
                "command": python_executable or sys.executable,
                "args": ["-m", "native_browser_control.cli"],
            }
        }
    }


def write_mcp_config(path: Path, *, force: bool = False) -> Path:
    path = path.resolve()
    if path.exists() and not force:
        raise FileExistsError(f"{path} は既に存在します。上書きする場合は --force を指定してください。")
    path.write_text(json.dumps(build_mcp_config(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="native-browser-control",
        description="Native Browser Control MCP Server (要 [mcp] extra)",
    )
    parser.add_argument("--version", action="version", version=f"native-browser-control {__version__}")
    parser.add_argument(
        "--write-mcp-config",
        nargs="?",
        const=".mcp.json",
        metavar="PATH",
        help="この Python 環境のサーバーを起動する .mcp.json を書き出して終了する (既定: ./.mcp.json)",
    )
    parser.add_argument("--force", action="store_true", help="--write-mcp-config で既存ファイルを上書きする")
    args = parser.parse_args(argv)

    if not mcp_available():
        print(MCP_MISSING_MESSAGE, file=sys.stderr)
        return 1

    if args.write_mcp_config is not None:
        try:
            written = write_mcp_config(Path(args.write_mcp_config), force=args.force)
        except FileExistsError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        print(f"wrote {written}")
        return 0

    from native_browser_control.server import main as server_main

    server_main([])
    return 0


if __name__ == "__main__":
    sys.exit(main())
