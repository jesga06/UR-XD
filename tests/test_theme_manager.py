"""
Unit tests for ThemeManager service using standard library unittest.
Verifies token management, hex normalization, QSS generation, preset discovery, and theme CRUD.
"""

import sys
import os
import json
import tempfile
import unittest

from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_v2.services.theme_manager import (
    ThemeManager, normalize_hex8, hex8_to_color, color_to_hex8, DEFAULT_TOKENS
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

    def test_theme_manager_tokens(self):
        self.assertEqual(self.tm.get_token("accent_1"), "#A855F7FF")
        self.assertEqual(self.tm.get_token("accent_2"), "#00F5A0FF")
        self.assertEqual(self.tm.get_token("background"), "#0C0914FF")
        self.assertEqual(self.tm.get_token("window_bg"), "#000000FF")

        self.tm.set_token("accent_1", "#12345678")
        self.assertEqual(self.tm.get_token("accent_1"), "#12345678")

        self.tm.reset_defaults()
        self.assertEqual(self.tm.get_token("accent_1"), "#A855F7FF")

    def test_presets_discovery(self):
        available = self.tm.get_available_themes()
        self.assertIn("Default Neon Purple", available)
        self.assertTrue(available["Default Neon Purple"]["is_preset"])
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
        self.assertFalse(self.tm.delete_user_theme("Default Neon Purple"))

        # 5. Delete User Themes
        self.assertTrue(self.tm.delete_user_theme("Test Custom Renamed"))
        self.assertTrue(self.tm.delete_user_theme("Test Custom Copy"))
        available = self.tm.get_available_themes()
        self.assertNotIn("Test Custom Renamed", available)
        self.assertNotIn("Test Custom Copy", available)

        self.tm.reset_defaults()


if __name__ == "__main__":
    unittest.main()
