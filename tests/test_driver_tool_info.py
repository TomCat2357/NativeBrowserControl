import unittest

from native_browser_control import driver


class ToolInfoTests(unittest.TestCase):
    def test_removed_ctrl_based_methods_are_not_exposed(self):
        methods = driver.NativeBrowserDriver.tool_info()["methods"]

        self.assertNotIn("find_text_on_page", methods)
        self.assertNotIn("get_page_source", methods)


if __name__ == "__main__":
    unittest.main()
