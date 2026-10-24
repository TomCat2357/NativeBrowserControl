import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from native_browser_control import cli


class CliTests(unittest.TestCase):
    def test_without_mcp_reports_extra_and_writes_nothing(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / ".mcp.json"
            with mock.patch.object(cli, "mcp_available", return_value=False):
                code = cli.main(["--write-mcp-config", str(target)])

            self.assertEqual(code, 1)
            self.assertFalse(target.exists())

    def test_write_mcp_config_uses_current_python(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / ".mcp.json"
            with mock.patch.object(cli, "mcp_available", return_value=True):
                code = cli.main(["--write-mcp-config", str(target)])

            self.assertEqual(code, 0)
            server = json.loads(target.read_text(encoding="utf-8"))["mcpServers"]["native-browser-control"]
            self.assertEqual(server["command"], cli.sys.executable)
            self.assertEqual(server["args"], ["-m", "native_browser_control.cli"])

    def test_write_mcp_config_refuses_overwrite_without_force(self):
        with tempfile.TemporaryDirectory() as tmp:
            target = Path(tmp) / ".mcp.json"
            target.write_text("{}", encoding="utf-8")
            with mock.patch.object(cli, "mcp_available", return_value=True):
                self.assertEqual(cli.main(["--write-mcp-config", str(target)]), 1)
                self.assertEqual(target.read_text(encoding="utf-8"), "{}")
                self.assertEqual(cli.main(["--write-mcp-config", str(target), "--force"]), 0)


if __name__ == "__main__":
    unittest.main()
