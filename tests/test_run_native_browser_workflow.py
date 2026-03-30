from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


SCRIPT_PATH = (
    Path(__file__).resolve().parents[1]
    / "skills"
    / "native-browser-usage"
    / "scripts"
    / "run_native_browser_workflow.py"
)
SPEC = importlib.util.spec_from_file_location("run_native_browser_workflow", SCRIPT_PATH)
MODULE = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
SPEC.loader.exec_module(MODULE)


class RunWorkflowTests(unittest.TestCase):
    def test_page_source_action_is_rejected_as_unsupported(self):
        spec = {
            "browser": "chrome",
            "connect": {"window_index": 0},
            "steps": [{"action": "page_source"}],
        }

        with patch.object(MODULE, "_connect_driver", return_value=object()):
            with self.assertRaises(MODULE.WorkflowError) as ctx:
                MODULE.run_workflow(spec)

        self.assertEqual(ctx.exception.code, "invalid_spec")
        self.assertEqual(str(ctx.exception), "Unsupported action: page_source")

    def test_find_text_action_is_rejected_as_unsupported(self):
        spec = {
            "browser": "chrome",
            "connect": {"window_index": 0},
            "steps": [{"action": "find_text", "text": "needle"}],
        }

        with patch.object(MODULE, "_connect_driver", return_value=object()):
            with self.assertRaises(MODULE.WorkflowError) as ctx:
                MODULE.run_workflow(spec)

        self.assertEqual(ctx.exception.code, "invalid_spec")
        self.assertEqual(str(ctx.exception), "Unsupported action: find_text")


if __name__ == "__main__":
    unittest.main()
