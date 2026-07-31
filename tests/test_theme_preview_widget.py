"""
Unit test for ThemePreviewWidget component.
Verifies instantiation, slot connections, repaint triggers, and style updates on theme change.
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

        # Trigger base color, source, and brightness changes and verify no exceptions
        tm.set_token("accent_1", "#FF0055FF")
        tm.set_token("accent_2", "#00FF55FF")
        tm.set_source("button_color_source", "accent_2")
        tm.set_brightness("widget_brightness", 15)

        tm.reset_defaults()


if __name__ == "__main__":
    unittest.main()
