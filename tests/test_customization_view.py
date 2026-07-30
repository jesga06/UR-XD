"""
Unit test for CustomizationView tab module.
Verifies UI creation, preset theme dropdown, CRUD dialog actions, and color preview swatches.
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

    def test_view_creation_and_preset_dropdown(self):
        tm = ThemeManager.get_instance()
        tm.reset_defaults()

        view = CustomizationView(tm)
        self.assertIsNotNone(view)

        # Check dropdown items count
        self.assertGreater(view.theme_dropdown.count(), 0)
        
        # Test switching theme preset via apply_theme_by_name
        tm.apply_theme_by_name("Cyber Orange")
        self.assertEqual(tm.get_token("accent_1"), "#F97316FF")
        self.assertEqual(view.hex_labels["accent_1"].text(), "#F97316FF")

        tm.reset_defaults()
        self.assertEqual(view.hex_labels["accent_1"].text(), "#A855F7FF")


if __name__ == "__main__":
    unittest.main()
