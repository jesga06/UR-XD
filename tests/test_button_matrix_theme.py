"""
Unit test for ButtonMatrix dynamic theme token integration.
Verifies that ButtonPill and ButtonMatrix update styles dynamically on theme_changed.
"""

import sys
import os
import unittest

from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_v2.services.theme_manager import ThemeManager
from button_matrix import ButtonPill, ButtonMatrix


class TestButtonMatrixTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def test_button_pill_theme_update(self):
        tm = ThemeManager.get_instance()
        tm.reset_defaults()

        pill = ButtonPill("a", "A")
        self.assertIsNotNone(pill)

        # Trigger active state and token change
        pill.set_active(True)
        tm.set_token("accent_1", "#FF0000FF")
        self.assertIn("rgba(255, 0, 0", pill.styleSheet())

        pill.set_active(False)
        tm.set_source("widget_bg_source", "window_bg")
        tm.set_token("background", "#00FF00FF")
        self.assertTrue("rgba(0, 38, 0" in pill.styleSheet() or "rgba(0, 255, 0" in pill.styleSheet())

        tm.reset_defaults()


if __name__ == "__main__":
    unittest.main()
