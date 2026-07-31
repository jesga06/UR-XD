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

    def test_pynput_key_conversion_modifiers_and_chars(self):
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

    def test_media_keys_conversion(self):
        dlg = KeyRecorderDialog("a")
        # Pynput Key enum media keys
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.media_volume_up), 'media_volume_up')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.media_volume_down), 'media_volume_down')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.media_volume_mute), 'media_volume_mute')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.media_play_pause), 'media_play_pause')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.media_next), 'media_next')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.Key.media_previous), 'media_previous')
        
        # VK codes for media keys (Windows hardware events)
        self.assertEqual(dlg._pynput_key_to_str(keyboard.KeyCode(vk=175)), 'media_volume_up')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.KeyCode(vk=174)), 'media_volume_down')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.KeyCode(vk=173)), 'media_volume_mute')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.KeyCode(vk=179)), 'media_play_pause')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.KeyCode(vk=176)), 'media_next')
        self.assertEqual(dlg._pynput_key_to_str(keyboard.KeyCode(vk=177)), 'media_previous')
        
        dlg._stop_listeners()
        dlg.close()

    def test_shift_modifier_and_symbols(self):
        dlg = KeyRecorderDialog("a")
        dlg._recorded_keys = ['shift']
        
        # When shift is held and '!' (Shift+1) arrives, map '!' back to '1'
        k_exclam = keyboard.KeyCode(char='!', vk=49)
        self.assertEqual(dlg._pynput_key_to_str(k_exclam), '1')
        
        # Qt Key_Backtab (Shift+Tab)
        evt_backtab = QKeyEvent(QKeyEvent.KeyPress, Qt.Key_Backtab, Qt.ShiftModifier)
        dlg.keyPressEvent(evt_backtab)
        self.assertIn('shift', dlg._recorded_keys)
        self.assertIn('tab', dlg._recorded_keys)
        self.assertEqual(dlg._result, 'keyboard:shift+tab')
        
        dlg._stop_listeners()
        dlg.close()

    def test_gamepad_telemetry_edge_detection(self):
        dlg = KeyRecorderDialog("a")
        
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

    def test_default_button_name_and_get_recorded_key(self):
        dlg = KeyRecorderDialog()
        self.assertEqual(dlg.button_name, "Input")
        self.assertEqual(dlg.get_recorded_key(), "")
        
        dlg._add_recorded_key("a")
        self.assertEqual(dlg.get_recorded_key(), "keyboard:a")
        
        dlg._stop_listeners()
        dlg.close()

if __name__ == "__main__":
    unittest.main()
