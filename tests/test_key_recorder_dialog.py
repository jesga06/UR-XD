import unittest
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QKeyEvent
import pynput
from pynput import keyboard

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui_v2.dialogs.key_recorder_dialog import KeyRecorderDialog

class TestKeyRecorderDialog(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_initialization_and_clear(self):
        dlg = KeyRecorderDialog("a")
        self.assertEqual(dlg._result, "")
        self.assertEqual(dlg._recorded_keys, [])
        
        # Simulate recording some keys
        dlg._add_recorded_key("ctrl")
        dlg._add_recorded_key("alt")
        dlg._add_recorded_key("a")
        self.assertEqual(dlg._recorded_keys, ["ctrl", "alt", "a"])
        self.assertEqual(dlg._result, "keyboard:ctrl+alt+a")
        
        # Test clear
        dlg._clear()
        self.assertEqual(dlg._result, "")
        self.assertEqual(dlg._recorded_keys, [])
        dlg._stop_listeners()
        dlg.close()

    def test_pynput_key_conversion(self):
        dlg = KeyRecorderDialog("a")
        # Modifiers
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.ctrl_l), 'ctrl')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.ctrl_r), 'ctrl')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.alt_l), 'alt')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.alt_r), 'alt')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.shift_l), 'shift')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.cmd), 'win')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.space), 'space')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.enter), 'enter')
        
        # Standard KeyCode 'a'
        k_a = keyboard.KeyCode.from_char('a')
        self.assertEqual(dlg._pynput_key_to_str(k_a), 'a')
        
        # Uppercase 'A' -> 'a'
        k_A = keyboard.KeyCode.from_char('A')
        self.assertEqual(dlg._pynput_key_to_str(k_A), 'a')
        
        # Control character \x01 (Ctrl+A) -> 'a'
        k_ctrl_a = keyboard.KeyCode(vk=65, char='\x01')
        self.assertEqual(dlg._pynput_key_to_str(k_ctrl_a), 'a')
        
        # KeyCode with char=None (Alt+A or special VK)
        k_alt_a = keyboard.KeyCode(vk=65, char=None)
        self.assertEqual(dlg._pynput_key_to_str(k_alt_a), 'a')
        
        dlg._stop_listeners()
        dlg.close()

    def test_gamepad_telemetry_edge_detection(self):
        dlg = KeyRecorderDialog("a") # Target is button 'a'
        
        # Frame 1: Button 'x' is unpressed
        t1 = {"b": False, "x": False}
        dlg.update_telemetry(t1)
        self.assertEqual(dlg._result, "")
        
        # Frame 2: Button 'x' is pressed (rising edge)
        t2 = {"b": False, "x": True}
        dlg.update_telemetry(t2)
        self.assertEqual(dlg._result, "gamepad:x")
        
        # Frame 3: User pressed keyboard key while button 'x' is STILL held
        dlg._add_recorded_key("ctrl")
        dlg._add_recorded_key("c")
        self.assertEqual(dlg._result, "keyboard:ctrl+c")
        
        # Frame 4: Telemetry arrives again with 'x' still True -> should NOT overwrite keyboard combo!
        dlg.update_telemetry(t2)
        self.assertEqual(dlg._result, "keyboard:ctrl+c")
        
        # Frame 5: Button 'y' is newly pressed -> rising edge overwrites
        t5 = {"b": False, "x": True, "y": True}
        dlg.update_telemetry(t5)
        self.assertEqual(dlg._result, "gamepad:y")
        self.assertEqual(dlg._recorded_keys, [])
        
        dlg._stop_listeners()
        dlg.close()

    def test_quick_mouse_button(self):
        dlg = KeyRecorderDialog("a")
        dlg._add_recorded_key("ctrl")
        self.assertEqual(dlg._result, "keyboard:ctrl")
        
        # Setting result to mouse click clears recorded keys
        dlg._set_result("mouse:left")
        self.assertEqual(dlg._result, "mouse:left")
        self.assertEqual(dlg._recorded_keys, [])
        
        dlg._stop_listeners()
        dlg.close()

if __name__ == "__main__":
    unittest.main()
