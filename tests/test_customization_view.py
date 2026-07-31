"""
Unit test for CustomizationView tab module.
Verifies UI creation, preset theme dropdown, source toggles, brightness sliders, and color preview swatches.
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
        self.assertEqual(tm.get_token("accent_1"), "#FF8000FF")
        self.assertEqual(view.hex_labels["accent_1"].text(), "#FF8000FF")

        tm.reset_defaults()
        self.assertEqual(view.hex_labels["accent_1"].text(), "#A855F7FF")

    def test_toggles_and_sliders_interaction(self):
        tm = ThemeManager.get_instance()
        tm.reset_defaults()

        view = CustomizationView(tm)

        # Test Button Source Combo
        view.btn_src_combo.setCurrentIndex(1)  # Accent #2
        self.assertEqual(tm.sources["button_color_source"], "accent_2")
        self.assertEqual(tm.get_token("button_bg"), "#00F5A0FF")

        # Test Widget Brightness Slider
        view.widget_brightness_slider.setValue(20)
        self.assertEqual(tm.brightness["widget_brightness"], 20)
        self.assertEqual(view.widget_brightness_label.text(), "+20%")

        tm.reset_defaults()


if __name__ == "__main__":
    unittest.main()
