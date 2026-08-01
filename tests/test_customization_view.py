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

        # Test Widget Background Source Combo
        view.wbg_src_combo.setCurrentIndex(1)  # Accent #1
        self.assertEqual(tm.sources["widget_bg_source"], "accent_1")
        self.assertNotEqual(tm.get_token("widget_bg"), tm.get_token("window_bg"))

        # Test Outline Color Source Combo
        view.out_src_combo.setCurrentIndex(1)  # Accent #2
        self.assertEqual(tm.sources["outline_source"], "accent_2")

        # Test Graph Axes Source Combo
        view.ga_src_combo.setCurrentIndex(2)  # Accent #2
        self.assertEqual(tm.sources["graph_axis_source"], "accent_2")

        # Test Widget Brightness Slider
        view.widget_brightness_slider.setValue(20)
        self.assertEqual(tm.brightness["widget_brightness"], 20)
        self.assertEqual(view.widget_brightness_label.text(), "20%")

        # Test Graph Axes Brightness Slider (0% to 100%)
        view.graph_axis_brightness_slider.setValue(80)
        self.assertEqual(tm.brightness["graph_axis_brightness"], 80)
        self.assertEqual(view.graph_axis_brightness_label.text(), "80%")

        tm.reset_defaults()

    def test_sandbox_editing_and_collision_guards(self):
        tm = ThemeManager.get_instance()
        tm.reset_defaults()

        view = CustomizationView(tm)

        # 1. Edit a control and verify dropdown marks Custom Theme*
        view.widget_brightness_slider.setValue(15)
        self.assertEqual(view.theme_dropdown.currentIndex(), 0)
        self.assertEqual(view.theme_dropdown.itemData(0), "Custom Theme")

        # 2. Test Discard Edits
        view.discard_edits()
        self.assertEqual(tm.brightness["widget_brightness"], 0)

        # 3. Test Apply App-Wide
        view.widget_brightness_slider.setValue(10)
        view.apply_app_wide()
        self.assertEqual(tm.committed_brightness["widget_brightness"], 10)

        # 4. Test theme_exists collision detector
        exists, is_preset, path = tm.theme_exists("Neon Purple")
        self.assertTrue(exists)
        self.assertTrue(is_preset)

        exists_user, is_preset_user, _ = tm.theme_exists("NonExistentThemeXYZ")
        self.assertFalse(exists_user)

        tm.reset_defaults()


if __name__ == "__main__":
    unittest.main()


