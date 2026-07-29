"""
Tests for RemappingView auto-blocking, double-input warnings, and shift layer home-button warnings.
"""

import unittest
from PySide6.QtWidgets import QApplication, QMessageBox
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from config_manager import ControllerConfig
from gui_v2.views.remapping_view import RemappingView

class TestRemappingView(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        RemappingView._has_shown_block_warning = False
        self.config = ControllerConfig()
        self.config.data = {
            "layer_base": {},
            "block_xinput": {},
            "shift_layers": [
                {
                    "id": "layer_0",
                    "name": "Default Shift Layer",
                    "trigger_button": "lb",
                    "modifier_button": "",
                    "mode": "hold",
                    "mappings": {}
                }
            ]
        }
        self.view = RemappingView(self.config)

    def tearDown(self):
        self.view.close()

    def test_auto_block_activation_on_mapping(self):
        # Button 'a' initially unmapped and unblocked
        self.assertFalse(self.view._get_block_state("a"))
        
        # Simulating user mapping button 'a'
        self.view._on_std_mapping_changed("a", "keyboard:space")
        
        # Verify block is auto-enabled
        self.assertTrue(self.view._get_block_state("a"))
        
        # Verify warning flag was set
        self.assertTrue(RemappingView._has_shown_block_warning)

    def test_home_hold_warning_detection(self):
        # Change trigger button to 'home' and mode to 'hold'
        layer = self.view._active_layer()
        layer["trigger_button"] = "home"
        layer["mode"] = "hold"
        
        # Check warning condition helper
        self.assertTrue(self.view._is_home_hold_warning_condition())

if __name__ == "__main__":
    unittest.main()
