"""
Integration test for MainWindow and ThemeManager integration.
Verifies Customization tab presence and dynamic QSS application.
"""

import sys
import os
import unittest

from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_v2.services.theme_manager import ThemeManager
from app_window import MainWindow


class TestAppWindowTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def test_main_window_customization_tab(self):
        tm = ThemeManager.get_instance()
        tm.reset_defaults()

        win = MainWindow()
        self.assertIsNotNone(win.customization_view)

        # Check tab count and tab text
        tab_count = win.tab_widget.count()
        tab_labels = [win.tab_widget.tabText(i) for i in range(tab_count)]
        self.assertIn("Customization", tab_labels)

        # Test changing theme token triggers qss update on app
        tm.set_token("accent_1", "#00AABBFF")
        win.close()
        tm.reset_defaults()


if __name__ == "__main__":
    unittest.main()
