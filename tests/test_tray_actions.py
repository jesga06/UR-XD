import unittest
from unittest.mock import MagicMock, patch
from decoder import ControllerState
from mapper import Mapper
from virtual_pad import VirtualPad


class TestTrayActions(unittest.TestCase):
    def setUp(self):
        self.config_mock = MagicMock()
        self.config_mock.has_section.return_value = False
        self.config_mock.data = {}

    @patch('mapper.MouseController')
    @patch('mapper.KeyboardController')
    def test_mapper_reset(self, mock_kbd, mock_mouse):
        mapper = Mapper(self.config_mock)
        mapper.active_holds = {'a': 'keyboard:a', 'b': 'mouse:left'}
        mapper.wasd_state = {'w': True, 'a': False, 's': False, 'd': False}
        mapper.active_scrolls = {'scroll_up': {}}
        mapper.pending_inputs = {'x': {}}

        mapper.reset()

        self.assertEqual(len(mapper.active_holds), 0)
        self.assertEqual(len(mapper.active_scrolls), 0)
        self.assertEqual(len(mapper.pending_inputs), 0)
        self.assertFalse(mapper.wasd_state['w'])

    @patch('vgamepad.VX360Gamepad')
    def test_virtual_pad_pause_passthrough(self, mock_vx360):
        import vgamepad as vg
        vpad = VirtualPad(self.config_mock)
        vpad.blocked_buttons = {'a', 'b', 'lt'}

        state = ControllerState()
        state.a = True
        state.lt = 0.8

        # When paused is True, blocked_buttons are ignored and state passes directly
        vpad.process(state, paused=True)

        vpad.gamepad.press_button.assert_called_with(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        vpad.gamepad.left_trigger_float.assert_called_with(value_float=0.8)

    @patch('vgamepad.VX360Gamepad')
    def test_virtual_pad_destroy(self, mock_vx360):
        vpad = VirtualPad(self.config_mock)
        vpad.destroy()
        vpad.gamepad.reset.assert_called_once()
        vpad.gamepad.update.assert_called()


if __name__ == '__main__':
    unittest.main()
