"""
Tests for RemappingView dual-block controls (Standard Block & Shift Block),
auto-blocking, double-input warnings, and shift layer home-button warnings.
"""

import unittest
from PySide6.QtWidgets import QApplication
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
                    "mappings": {},
                    "block_xinput": {}
                },
                {
                    "id": "layer_1",
                    "name": "Second Shift Layer",
                    "trigger_button": "rb",
                    "modifier_button": "",
                    "mode": "toggle",
                    "mappings": {},
                    "block_xinput": {}
                }
            ]
        }
        self.view = RemappingView(self.config)

    def tearDown(self):
        self.view.close()

    def test_independent_standard_and_shift_block_states(self):
        # Button 'a' initially unmapped and unblocked for both
        self.assertFalse(self.view._get_base_block_state("a"))
        self.assertFalse(self.view._get_shift_block_state("a"))
        
        # Enable base block only
        self.view._on_std_block_changed("a", True)
        self.assertTrue(self.view._get_base_block_state("a"))
        self.assertFalse(self.view._get_shift_block_state("a"))
        
        # Enable shift block only on active layer
        self.view._on_shift_block_changed("a", True)
        self.assertTrue(self.view._get_base_block_state("a"))
        self.assertTrue(self.view._get_shift_block_state("a"))
        
        # Uncheck standard block -> shift block remains True
        self.view._on_std_block_changed("a", False)
        self.assertFalse(self.view._get_base_block_state("a"))
        self.assertTrue(self.view._get_shift_block_state("a"))

    def test_auto_block_activation_standard_mapping(self):
        self.assertFalse(self.view._get_base_block_state("a"))
        self.view._on_std_mapping_changed("a", "keyboard:space")
        self.assertTrue(self.view._get_base_block_state("a"))
        self.assertTrue(RemappingView._has_shown_block_warning)

    def test_auto_block_activation_shift_mapping(self):
        self.assertFalse(self.view._get_shift_block_state("a"))
        self.view._on_shift_mapping_changed("a", "keyboard:c")
        self.assertTrue(self.view._get_shift_block_state("a"))
        self.assertTrue(RemappingView._has_shown_block_warning)

    def test_shift_layer_switch_updates_shift_block(self):
        # Layer 0: block button 'a'
        self.view._on_shift_block_changed("a", True)
        self.assertTrue(self.view._get_shift_block_state("a"))
        
        # Switch to Layer 1
        self.view.layer_selector.setCurrentIndex(1)
        self.assertFalse(self.view._get_shift_block_state("a"))
        
        # Enable block on Layer 1
        self.view._on_shift_block_changed("a", True)
        self.assertTrue(self.view._get_shift_block_state("a"))
        
        # Switch back to Layer 0
        self.view.layer_selector.setCurrentIndex(0)
        self.assertTrue(self.view._get_shift_block_state("a"))

    def test_home_hold_warning_detection(self):
        layer = self.view._active_layer()
        layer["trigger_button"] = "home"
        layer["mode"] = "hold"
        self.assertTrue(self.view._is_home_hold_warning_condition())

if __name__ == "__main__":
    unittest.main()
