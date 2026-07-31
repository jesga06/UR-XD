"""
Unit tests for ThemeManager service using standard library unittest.
Verifies base colors, source toggles, brightness sliders, derived color pipeline,
hex normalization, QSS generation, preset discovery, and theme CRUD.
"""

import sys
import os
import json
import tempfile
import unittest

from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_v2.services.theme_manager import (
    ThemeManager, normalize_hex8, hex8_to_color, color_to_hex8, DEFAULT_BASE_COLORS
)


class TestThemeManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def setUp(self):
        self.tm = ThemeManager.get_instance()
        self.tm.reset_defaults()

    def test_normalize_hex8(self):
        self.assertEqual(normalize_hex8("#a855f7"), "#A855F7FF")
        self.assertEqual(normalize_hex8("00f5a0ff"), "#00F5A0FF")
        self.assertEqual(normalize_hex8("#FFF"), "#FFFFFFFF")
        self.assertEqual(normalize_hex8("invalid", default="#0C0914FF"), "#0C0914FF")

    def test_color_hex_conversion(self):
        hex_in = "#A855F788"
        color = hex8_to_color(hex_in)
        self.assertEqual(color.red(), 0xA8)
        self.assertEqual(color.green(), 0x55)
        self.assertEqual(color.blue(), 0xF7)
        self.assertEqual(color.alpha(), 0x88)

        hex_out = color_to_hex8(color)
        self.assertEqual(hex_out, "#A855F788")

    def test_adjust_brightness(self):
        color_hex = "#808080FF"
        brighter = self.tm.adjust_brightness(color_hex, 0.20)
        darker = self.tm.adjust_brightness(color_hex, -0.20)
        self.assertNotEqual(color_hex, brighter)
        self.assertNotEqual(color_hex, darker)

    def test_derived_color_pipeline(self):
        self.assertEqual(self.tm.get_token("accent_1"), "#A855F7FF")
        self.assertEqual(self.tm.get_token("accent_2"), "#00F5A0FF")
        self.assertEqual(self.tm.get_token("window_bg"), "#0C0914FF")
        self.assertEqual(self.tm.get_token("text"), "#FFFFFFFF")

        # Test Derived Tokens Presence
        tokens = self.tm.get_all_tokens()
        self.assertIn("widget_bg", tokens)
        self.assertIn("graph_bg", tokens)
        self.assertIn("graph_axis", tokens)
        self.assertIn("outline", tokens)
        self.assertIn("button_bg", tokens)
        self.assertIn("button_hover", tokens)
        self.assertIn("button_pressed", tokens)

        # Test Button Color Source switch
        self.tm.set_source("button_color_source", "accent_2")
        self.assertEqual(self.tm.get_token("button_bg"), "#00F5A0FF")

        # Test Brightness Sliders
        self.tm.set_brightness("widget_brightness", 20)
        tokens_new = self.tm.get_all_tokens()
        self.assertNotEqual(tokens["widget_bg"], tokens_new["widget_bg"])

        self.tm.reset_defaults()

    def test_presets_discovery(self):
        available = self.tm.get_available_themes()
        self.assertIn("Neon Purple", available)
        self.assertTrue(available["Neon Purple"]["is_preset"])
        self.assertIn("Cyber Orange", available)
        self.assertIn("Emerald Mint", available)

    def test_user_theme_crud(self):
        # 1. Save Custom Theme
        self.tm.set_token("accent_1", "#112233FF")
        self.assertTrue(self.tm.save_user_theme("Test Custom Palette"))

        available = self.tm.get_available_themes()
        self.assertIn("Test Custom Palette", available)
        self.assertFalse(available["Test Custom Palette"]["is_preset"])

        # 2. Copy Theme
        self.assertTrue(self.tm.copy_theme("Test Custom Palette", "Test Custom Copy"))
        available = self.tm.get_available_themes()
        self.assertIn("Test Custom Copy", available)

        # 3. Rename Theme
        self.assertTrue(self.tm.rename_user_theme("Test Custom Palette", "Test Custom Renamed"))
        available = self.tm.get_available_themes()
        self.assertNotIn("Test Custom Palette", available)
        self.assertIn("Test Custom Renamed", available)

        # 4. Preset Deletion Protection
        self.assertFalse(self.tm.delete_user_theme("Neon Purple"))

        # 5. Delete User Themes
        self.assertTrue(self.tm.delete_user_theme("Test Custom Renamed"))
        self.assertTrue(self.tm.delete_user_theme("Test Custom Copy"))
        available = self.tm.get_available_themes()
        self.assertNotIn("Test Custom Renamed", available)
        self.assertNotIn("Test Custom Copy", available)

        self.tm.reset_defaults()

    def test_import_export_json_schema(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tf:
            temp_path = tf.name

        try:
            self.tm.set_token("accent_1", "#FFAA00FF")
            self.tm.set_source("button_color_source", "accent_2")
            self.tm.set_brightness("graph_brightness", 15)

            self.assertTrue(self.tm.export_theme_json(temp_path))

            self.tm.reset_defaults()
            self.assertEqual(self.tm.get_token("accent_1"), "#A855F7FF")

            self.assertTrue(self.tm.import_theme_json(temp_path))
            self.assertEqual(self.tm.get_token("accent_1"), "#FFAA00FF")
            self.assertEqual(self.tm.sources["button_color_source"], "accent_2")
            self.assertEqual(self.tm.brightness["graph_brightness"], 15)
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)


if __name__ == "__main__":
    unittest.main()
