from __future__ import annotations

import importlib.util
import io
import json
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "native-browser-usage"
    / "scripts"
    / "run_native_browser_command.py"
)
SPEC = importlib.util.spec_from_file_location("run_native_browser_command", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class BuildSpecTests(unittest.TestCase):
    def test_navigate_preserves_timeout_and_interval(self):
        parser = MODULE.build_parser()
        args = parser.parse_args(
            [
                "navigate",
                "--browser",
                "edge",
                "--url",
                "https://example.com",
                "--timeout-s",
                "8",
                "--interval-s",
                "0.25",
            ]
        )

        spec = MODULE.build_spec(args)

        self.assertEqual(spec["steps"][0]["timeout_s"], 8.0)
        self.assertEqual(spec["steps"][0]["interval_s"], 0.25)

    def test_connect_builds_summary_workflow(self):
        parser = MODULE.build_parser()
        args = parser.parse_args(
            ["connect", "--browser", "chrome", "--launch", "--max-text-len", "80"]
        )

        spec = MODULE.build_spec(args)

        self.assertEqual(spec["connect"]["launch"], True)
        self.assertEqual(spec["steps"], [{"action": "summary", "max_text_len": 80}])

    def test_scan_with_filter_builds_scan_then_filter(self):
        parser = MODULE.build_parser()
        args = parser.parse_args(
            [
                "scan",
                "--browser",
                "edge",
                "--control-type",
                "Button",
                "--name-regex",
                "Search",
                "--only-visible",
            ]
        )

        spec = MODULE.build_spec(args)

        self.assertEqual(spec["connect"]["window_index"], 0)
        self.assertEqual(spec["steps"][0]["action"], "scan")
        self.assertEqual(spec["steps"][0]["control_type"], "Button")
        self.assertEqual(spec["steps"][1]["action"], "filter")
        self.assertEqual(spec["steps"][1]["control_types"], ["Button"])
        self.assertTrue(spec["steps"][1]["only_visible"])

    def test_click_with_filtered_match_defaults_to_first_result(self):
        parser = MODULE.build_parser()
        args = parser.parse_args(
            [
                "click",
                "--browser",
                "chrome",
                "--control-types",
                "Button,Link",
                "--name-regex",
                "Submit",
            ]
        )

        spec = MODULE.build_spec(args)

        self.assertEqual([step["action"] for step in spec["steps"]], ["scan", "filter", "click_index"])
        self.assertEqual(spec["steps"][1]["control_types"], ["Button", "Link"])
        self.assertEqual(spec["steps"][2]["index"], 0)

    def test_set_text_with_explicit_index_skips_filter(self):
        parser = MODULE.build_parser()
        args = parser.parse_args(
            [
                "set-text",
                "--browser",
                "edge",
                "--index",
                "3",
                "--text",
                "hello",
            ]
        )

        spec = MODULE.build_spec(args)

        self.assertEqual([step["action"] for step in spec["steps"]], ["scan", "set_text"])
        self.assertEqual(spec["steps"][1]["index"], 3)
        self.assertEqual(spec["steps"][1]["text"], "hello")

    def test_click_requires_target(self):
        parser = MODULE.build_parser()
        args = parser.parse_args(["click", "--browser", "chrome"])

        with self.assertRaises(MODULE.CommandSpecError):
            MODULE.build_spec(args)


class MainTests(unittest.TestCase):
    def test_dependency_error_recommends_command_runner(self):
        output = io.StringIO()
        error = MODULE.WorkflowError(
            "dependency_missing",
            "missing",
            {"project_root": r"C:\repo", "recommended_runner": "workflow"},
        )

        with patch.object(MODULE, "run_workflow", side_effect=error):
            with patch("sys.stdout", output):
                exit_code = MODULE.main(["summary", "--browser", "chrome"])

        self.assertEqual(exit_code, 1)
        emitted = json.loads(output.getvalue())
        self.assertIn("run_native_browser_command.py", emitted["error"]["data"]["recommended_runner"])

    def test_main_emits_runner_payload(self):
        output = io.StringIO()
        payload = {"ok": True, "results": [{"action": "summary"}]}

        with patch.object(MODULE, "run_workflow", return_value=payload):
            with patch("sys.stdout", output):
                exit_code = MODULE.main(["summary", "--browser", "chrome"])

        self.assertEqual(exit_code, 0)
        emitted = json.loads(output.getvalue())
        self.assertEqual(emitted, payload)


if __name__ == "__main__":
    unittest.main()
