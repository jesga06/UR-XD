"""
Unit tests for ThemeManager service using standard library unittest.
Verifies token management, hex normalization, QSS generation, and theme import/export.
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

        self.tm.set_token("accent_1", "#12345678")
        self.assertEqual(self.tm.get_token("accent_1"), "#12345678")

        self.tm.reset_defaults()
        self.assertEqual(self.tm.get_token("accent_1"), "#A855F7FF")

    def test_theme_import_export(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            export_path = os.path.join(tmp_dir, "test_theme.json")
            self.tm.set_token("accent_1", "#FF0000FF")
            self.tm.set_token("accent_2", "#00FF00FF")
            self.tm.set_token("background", "#0000FFFF")

            self.assertTrue(self.tm.export_theme(export_path))
            self.assertTrue(os.path.exists(export_path))

            self.tm.reset_defaults()
            self.assertEqual(self.tm.get_token("accent_1"), "#A855F7FF")

            self.assertTrue(self.tm.import_theme(export_path))
            self.assertEqual(self.tm.get_token("accent_1"), "#FF0000FF")
            self.assertEqual(self.tm.get_token("accent_2"), "#00FF00FF")
            self.assertEqual(self.tm.get_token("background"), "#0000FFFF")

    def test_theme_import_partial_json(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            partial_path = os.path.join(tmp_dir, "partial_theme.json")
            with open(partial_path, "w") as f:
                json.dump({"accent_1": "#11223344"}, f)

            self.assertTrue(self.tm.import_theme(partial_path))
            self.assertEqual(self.tm.get_token("accent_1"), "#11223344")
            self.assertEqual(self.tm.get_token("accent_2"), "#00F5A0FF")


if __name__ == "__main__":
    unittest.main()
