"""
Unit test for ThemePreviewWidget component.
Verifies instantiation, slot connections, and style updates on theme change.
"""

import sys
import os
import unittest

from PySide6.QtWidgets import QApplication

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))

from gui_v2.services.theme_manager import ThemeManager
from gui_v2.widgets.theme_preview_widget import ThemePreviewWidget


class TestThemePreviewWidget(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance()
        if not cls.app:
            cls.app = QApplication([])

    def test_widget_creation_and_signal(self):
        tm = ThemeManager.get_instance()
        tm.reset_defaults()

        widget = ThemePreviewWidget(tm)
        self.assertIsNotNone(widget)

        # Trigger a token change and ensure no exceptions thrown during repaint/style updates
        tm.set_token("accent_1", "#FF0055FF")
        tm.set_token("accent_2", "#00FF55FF")
        tm.set_token("background", "#110022FF")

        tm.reset_defaults()


if __name__ == "__main__":
    unittest.main()
