import sys
import os
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
import hidhide_helper

class TestHidHideHelper(unittest.TestCase):
    """
    Unit tests for hidhide_helper module functions.
    """

    def test_cli_path_resolution(self):
        cli_path = hidhide_helper.get_hidhide_cli_path()
        self.assertIsInstance(cli_path, str)
        if cli_path:
            self.assertTrue(os.path.exists(cli_path))
            self.assertTrue(cli_path.endswith("HidHideCLI.exe"))

    def test_is_hidhide_installed_bool(self):
        installed = hidhide_helper.is_hidhide_installed()
        self.assertIsInstance(installed, bool)

    def test_python_exe_resolution(self):
        python_exe = os.path.abspath(sys.executable)
        self.assertTrue(os.path.exists(python_exe))
        self.assertTrue(python_exe.lower().endswith("python.exe"))

    def test_get_hidhide_status_structure(self):
        status = hidhide_helper.get_hidhide_status()
        self.assertIsInstance(status, dict)
        self.assertIn("installed", status)
        self.assertIn("app_registered", status)
        self.assertIn("cloak_active", status)
        self.assertIn("dev_list", status)
        self.assertIn("python_exe", status)

if __name__ == "__main__":
    unittest.main()
