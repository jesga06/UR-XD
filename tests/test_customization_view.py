"""
Unit test for CustomizationView tab module.
Verifies UI creation, color preview swatches, and reset actions.
"""

import sys
import os
import unittest

from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_v2.services.theme_manager import ThemeManager
from gui_v2.views.customization_view import CustomizationView


class TestCustomizationView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def test_view_creation_and_token_refresh(self):
        tm = ThemeManager.get_instance()
        tm.reset_defaults()

        view = CustomizationView(tm)
        self.assertIsNotNone(view)

        self.assertEqual(view.hex_labels["accent_1"].text(), "#A855F7FF")
        self.assertEqual(view.hex_labels["accent_2"].text(), "#00F5A0FF")
        self.assertEqual(view.hex_labels["background"].text(), "#0C0914FF")

        # Set token and check updated text
        tm.set_token("accent_1", "#123456FF")
        self.assertEqual(view.hex_labels["accent_1"].text(), "#123456FF")

        tm.reset_defaults()
        self.assertEqual(view.hex_labels["accent_1"].text(), "#A855F7FF")


if __name__ == "__main__":
    unittest.main()
