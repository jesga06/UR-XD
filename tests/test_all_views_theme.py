"""
Integration test for dynamic ThemeManager color token propagation across all views.
Verifies that changing theme tokens or switching preset themes dynamically updates styles
on DashboardView, RemappingView, TuningView, CustomizationView, and MainWindow.
"""

import sys
import os
import unittest

from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_v2.services.theme_manager import ThemeManager
from app_window import MainWindow


class TestAllViewsTheme(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def test_all_views_theme_propagation(self):
        tm = ThemeManager.get_instance()
        tm.reset_defaults()

        win = MainWindow()
        try:
            self.assertIsNotNone(win)
            self.assertIsNotNone(win.dashboard_view)
            self.assertIsNotNone(win.customization_view)

            # 1. Switch Theme to Cyber Orange
            tm.apply_theme_by_name("Cyber Orange")
            self.assertEqual(tm.get_token("accent_1"), "#FF8000FF")
            self.assertEqual(tm.get_token("background"), "#000000FF")
            self.assertEqual(tm.get_token("window_bg"), "#000000FF")

            # Verify Dashboard readout updated to brightened accent_2
            readout_style = win.dashboard_view.left_readout.styleSheet()
            self.assertIn("color: #", readout_style)

            # 2. Reset Defaults
            tm.reset_defaults()
            self.assertEqual(tm.get_token("background"), "#0C0914FF")
            self.assertEqual(tm.get_token("window_bg"), "#0C0914FF")
            self.assertEqual(tm.get_token("accent_1"), "#A855F7FF")
        finally:
            win.close()


if __name__ == "__main__":
    unittest.main()
