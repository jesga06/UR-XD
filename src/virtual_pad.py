"""
Virtual XInput Controller Interface (virtual_pad.py)
Uses vgamepad (communicating with the ViGEmBus Windows driver) to simulate
a virtual Xbox 360 controller. It forwards normal gamepad inputs and blocks
standard buttons if they have been custom-remapped to key/mouse events.
"""
import vgamepad as vg
from decoder import ControllerState
import math_utils
import logging

logger = logging.getLogger('virtual_pad')

BUTTON_MAP = {
    'a': vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
    'b': vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
    'x': vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
    'y': vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
    'lb': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
    'rb': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
    'select': vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
    'start': vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
    'home': vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE,
    'l3': vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
    'r3': vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
    'dpad_up': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
    'dpad_down': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN,
    'dpad_left': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT,
    'dpad_right': vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT,
}


class VirtualPad:
    """
    Simulates a virtual Xbox 360 gamepad based on parsed ControllerState.
    Controls analog stick mapping, digital button mapping, triggers, and D-pad.
    Blocks standard inputs when remapped to keys/mouse to avoid duplicate presses in-game.
    """

    def __init__(self, config=None):
        try:
            self.gamepad = vg.VX360Gamepad()
            print("Virtual Xbox 360 controller created successfully.")
            logger.info("Virtual Xbox 360 controller created successfully.")
        except Exception as e:
            msg = f"Failed to create virtual gamepad: {e}\nIs ViGEmBus installed?"
            print(msg)
            logger.error(msg)
            raise

        self.home_mapping = 'guide'
        self.blocked_buttons = set()
        self.macro_pressed_buttons = set()
        self.rumble_callback = None
        self.haptic_engine = None
        
        # Register for force feedback notifications
        try:
            self.gamepad.register_notification(self._vgamepad_notification_handler)
        except Exception as e:
            print(f"Warning: Could not register vgamepad notifications: {e}")
            logger.warning(f"Could not register vgamepad notifications: {e}", exc_info=True)

        # Always load default attributes (and apply config if provided)
        self.reload_config(config)

    def set_rumble_callback(self, callback):
        """callback(left_motor: int, right_motor: int) -> 0-255"""
        self.rumble_callback = callback

    def set_haptic_engine(self, engine):
        self.haptic_engine = engine

    def set_vibration(self, lm: int, rm: int):
        if self.rumble_callback:
            # Scale 0-65535 to 0-255
            self.rumble_callback(int(lm / 257), int(rm / 257))

    def _vgamepad_notification_handler(self, client, target, large_motor, small_motor, led_number, user_data):
        if self.haptic_engine and getattr(self.haptic_engine, 'is_hijacked', False):
            return # Ignore in-game rumble while shift haptic pattern is executing
        if self.rumble_callback:
            # large_motor and small_motor are 0-255
            self.rumble_callback(large_motor, small_motor)

    def reload_config(self, config=None):
        if logger:
            logger.debug("[ENTER] virtual_pad reload_config()")
        self.home_mapping = 'guide'
        self.blocked_buttons.clear()
        self.macro_pressed_buttons.clear()

        self.digital_lt = False
        self.digital_rt = False
        self.lt_inner = 0.05
        self.lt_adz = 0.0
        self.lt_curve = 'linear'
        self.lt_power = 2.0
        self.lt_rest_dz = 0.0
        self.lt_sens = 1.0
        self.lt_custom = ''

        self.rt_inner = 0.05
        self.rt_adz = 0.0
        self.rt_curve = 'linear'
        self.rt_power = 2.0
        self.rt_rest_dz = 0.0
        self.rt_sens = 1.0
        self.rt_custom = ''

        self.ls_inner = 0.05
        self.ls_adz = 0.0
        self.ls_curve = 'linear'
        self.ls_power = 2.0
        self.ls_rest_dz = 0.0
        self.ls_sens = 1.0
        self.ls_warp = 0.0
        self.ls_custom = ''
        self.ls_circ_mode = 'disabled'
        self.ls_circ_cx = 0.0
        self.ls_circ_cy = 0.0
        self.ls_circ_bounds = None

        self.rs_inner = 0.05
        self.rs_adz = 0.0
        self.rs_curve = 'linear'
        self.rs_power = 2.0
        self.rs_rest_dz = 0.0
        self.rs_sens = 1.0
        self.rs_warp = 0.0
        self.rs_custom = ''
        self.rs_circ_mode = 'disabled'
        self.rs_circ_cx = 0.0
        self.rs_circ_cy = 0.0
        self.rs_circ_bounds = None

        if not config:
            return

        if config.has_section('settings'):
            if config.has_option('settings', 'digital_lt'):
                self.digital_lt = config.get(
                    'settings', 'digital_lt').lower() == 'true'
            if config.has_option('settings', 'digital_rt'):
                self.digital_rt = config.get(
                    'settings', 'digital_rt').lower() == 'true'

        if config.has_section('trigger_left'):
            self.lt_inner = config.getfloat('trigger_left', 'deadzone', fallback=self.lt_inner)
            self.lt_adz = config.getfloat('trigger_left', 'anti_deadzone', fallback=self.lt_adz)
            self.lt_curve = config.get('trigger_left', 'curve', fallback=self.lt_curve)
            self.lt_power = config.getfloat('trigger_left', 'exp_factor', fallback=self.lt_power)
            self.lt_rest_dz = config.getfloat('trigger_left', 'rest_deadzone', fallback=0.0)
            self.lt_sens = config.getfloat('trigger_left', 'sensitivity', fallback=1.0)
            self.lt_custom = config.get('trigger_left', 'custom_eq', fallback='')

        if config.has_section('trigger_right'):
            self.rt_inner = config.getfloat('trigger_right', 'deadzone', fallback=self.rt_inner)
            self.rt_adz = config.getfloat('trigger_right', 'anti_deadzone', fallback=self.rt_adz)
            self.rt_curve = config.get('trigger_right', 'curve', fallback=self.rt_curve)
            self.rt_power = config.getfloat('trigger_right', 'exp_factor', fallback=self.rt_power)
            self.rt_rest_dz = config.getfloat('trigger_right', 'rest_deadzone', fallback=0.0)
            self.rt_sens = config.getfloat('trigger_right', 'sensitivity', fallback=1.0)
            self.rt_custom = config.get('trigger_right', 'custom_eq', fallback='')

        if config.has_section('analog_left') or config.has_section('Stick_Left'):
            sec = 'analog_left' if config.has_section('analog_left') else 'Stick_Left'
            self.ls_inner = config.getfloat(sec, 'deadzone', fallback=self.ls_inner)
            self.ls_adz = config.getfloat(sec, 'anti_deadzone', fallback=0.0)
            self.ls_curve = config.get(sec, 'curve', fallback=self.ls_curve)
            self.ls_power = config.getfloat(sec, 'exp_factor', fallback=self.ls_power)
            self.ls_rest_dz = config.getfloat(sec, 'rest_deadzone', fallback=0.0)
            self.ls_sens = config.getfloat(sec, 'sensitivity', fallback=1.0)
            self.ls_warp = config.getfloat(sec, 'warp_threshold', fallback=config.getfloat(sec, 'warped_stick_threshold', fallback=0.0))
            self.ls_custom = config.get(sec, 'custom_eq', fallback=config.get(sec, 'custom_curve', fallback=''))
            self.ls_circ_mode = config.get(sec, 'circularity_mode', fallback='disabled').lower()
            self.ls_circ_cx = config.getfloat(sec, 'circularity_center_x', fallback=0.0)
            self.ls_circ_cy = config.getfloat(sec, 'circularity_center_y', fallback=0.0)
            bounds_str = config.get(sec, 'circularity_bounds', fallback='')
            self.ls_circ_bounds = [float(x) for x in bounds_str.split(',')] if bounds_str and len(bounds_str.split(',')) == 360 else None

        if config.has_section('analog_right') or config.has_section('Stick_Right'):
            sec = 'analog_right' if config.has_section('analog_right') else 'Stick_Right'
            self.rs_inner = config.getfloat(sec, 'deadzone', fallback=self.rs_inner)
            self.rs_adz = config.getfloat(sec, 'anti_deadzone', fallback=0.0)
            self.rs_curve = config.get(sec, 'curve', fallback=self.rs_curve)
            self.rs_power = config.getfloat(sec, 'exp_factor', fallback=self.rs_power)
            self.rs_rest_dz = config.getfloat(sec, 'rest_deadzone', fallback=0.0)
            self.rs_sens = config.getfloat(sec, 'sensitivity', fallback=1.0)
            self.rs_warp = config.getfloat(sec, 'warp_threshold', fallback=config.getfloat(sec, 'warped_stick_threshold', fallback=0.0))
            self.rs_custom = config.get(sec, 'custom_eq', fallback=config.get(sec, 'custom_curve', fallback=''))
            self.rs_circ_mode = config.get(sec, 'circularity_mode', fallback='disabled').lower()
            self.rs_circ_cx = config.getfloat(sec, 'circularity_center_x', fallback=0.0)
            self.rs_circ_cy = config.getfloat(sec, 'circularity_center_y', fallback=0.0)
            bounds_str = config.get(sec, 'circularity_bounds', fallback='')
            self.rs_circ_bounds = [float(x) for x in bounds_str.split(',')] if bounds_str and len(bounds_str.split(',')) == 360 else None


        # Load block preferences (default to block if mapped, i.e. True)
        self.layer_blocked_buttons = {'layer_base': set()}
        block_prefs = {}
        raw_bx = {}
        if config.has_section('block_xinput'):
            for key, val in config.items('block_xinput'):
                raw_bx[key.lower()] = val
        elif hasattr(config, 'data') and 'block_xinput' in config.data:
            bx_data = config.data.get('block_xinput', {})
            if isinstance(bx_data, dict):
                for key, val in bx_data.items():
                    raw_bx[key.lower()] = val

        for key, val in raw_bx.items():
            if isinstance(val, bool):
                block_prefs[key] = val
            else:
                block_prefs[key] = str(val).lower() != 'false'

        valid_buttons = ['a', 'b', 'x', 'y', 'lb', 'rb', 'lt', 'rt', 'select',
                         'start', 'l3', 'r3', 'dpad_up', 'dpad_down', 'dpad_left', 'dpad_right', 'ls', 'rs', 'home']

        base_blocked = set()
        for key, should_block in block_prefs.items():
            if should_block and key in valid_buttons:
                base_blocked.add(key)
                self.blocked_buttons.add(key)

        for section_name in ['layer_base', 'extra_buttons']:
            if config.has_section(section_name):
                for key, val in config.items(section_name):
                    key_lower = key.lower()
                    if key_lower == 'home' and val:
                        self.home_mapping = val.lower()

                    if key_lower in valid_buttons and key_lower not in block_prefs:
                        # Default to block remapped inputs if no explicit block setting exists
                        base_blocked.add(key_lower)
                        self.blocked_buttons.add(key_lower)

        self.layer_blocked_buttons['layer_base'] = base_blocked

        # Check multi-shift layers block preferences
        if hasattr(config, 'get_shift_layers'):
            shift_layers_data = config.get_shift_layers()
        elif hasattr(config, 'data') and 'shift_layers' in config.data:
            shift_layers_data = config.data.get('shift_layers', [])
        else:
            shift_layers_data = []

        for s_layer in shift_layers_data:
            if not isinstance(s_layer, dict):
                continue
            s_id = s_layer.get('id', 'shift_1')
            s_mappings = s_layer.get('mappings', {})
            s_block = s_layer.get('block_xinput', {})
            s_blocked = set()

            s_block_prefs = {}
            if isinstance(s_block, dict):
                for key, val in s_block.items():
                    key_lower = key.lower()
                    if key_lower in valid_buttons:
                        b_val = val if isinstance(val, bool) else str(val).lower() != 'false'
                        s_block_prefs[key_lower] = b_val
                        if b_val:
                            s_blocked.add(key_lower)
                            self.blocked_buttons.add(key_lower)

            if isinstance(s_mappings, dict):
                for key, val in s_mappings.items():
                    key_lower = key.lower()
                    if key_lower in valid_buttons and key_lower not in s_block_prefs:
                        s_blocked.add(key_lower)
                        self.blocked_buttons.add(key_lower)

            self.layer_blocked_buttons[s_id] = s_blocked


    def destroy(self):
        """Safely resets and unregisters virtual gamepad resources."""
        try:
            if hasattr(self, 'gamepad') and self.gamepad:
                self.gamepad.reset()
                self.gamepad.update()
                logger.info("Virtual gamepad safely destroyed.")
        except Exception as e:
            if logger:
                logger.error(f"Error destroying virtual pad: {e}")

    def process(self, state: ControllerState, paused: bool = False):
        """
        Translates normalized float ControllerState values into vgamepad commands.
        Clamps values, handles deadzones, inverts Y axis as needed, and respects blocked inputs.
        If paused is True, physical inputs pass directly through without remapping or button blocking.
        """
        if not self.gamepad:
            return

        # Determine active layer blocks & consumed shift buttons
        mapper_ref = getattr(self, 'mapper', None)
        active_layer_id = getattr(mapper_ref, 'active_layer', 'layer_base') if mapper_ref else 'layer_base'
        consumed = getattr(mapper_ref, 'consumed_shift_buttons', set()) if mapper_ref else set()
        active_layer_blocks = getattr(self, 'layer_blocked_buttons', {}).get(active_layer_id, self.blocked_buttons)

        # Triggers
        if paused:
            lt_val = state.lt
            rt_val = state.rt
        else:
            lt_val = math_utils.process_trigger(
                state.lt, self.lt_inner, self.lt_adz, self.lt_curve, self.lt_power,
                getattr(self, 'lt_rest_dz', 0.0), getattr(self, 'lt_sens', 1.0), getattr(self, 'lt_custom', '')
            )
            rt_val = math_utils.process_trigger(
                state.rt, self.rt_inner, self.rt_adz, self.rt_curve, self.rt_power,
                getattr(self, 'rt_rest_dz', 0.0), getattr(self, 'rt_sens', 1.0), getattr(self, 'rt_custom', '')
            )

        if getattr(self, 'digital_lt', False):
            lt_val = 1.0 if lt_val > 0 else 0.0
        if getattr(self, 'digital_rt', False):
            rt_val = 1.0 if rt_val > 0 else 0.0

        is_lt_blocked = ('lt' in consumed) or ('lt' in active_layer_blocks)
        if not paused and is_lt_blocked:
            self.gamepad.left_trigger_float(value_float=0.0)
        elif not paused and 'lt' in self.macro_pressed_buttons:
            self.gamepad.left_trigger_float(value_float=1.0)
        else:
            self.gamepad.left_trigger_float(value_float=lt_val)

        is_rt_blocked = ('rt' in consumed) or ('rt' in active_layer_blocks)
        if not paused and is_rt_blocked:
            self.gamepad.right_trigger_float(value_float=0.0)
        elif not paused and 'rt' in self.macro_pressed_buttons:
            self.gamepad.right_trigger_float(value_float=1.0)
        else:
            self.gamepad.right_trigger_float(value_float=rt_val)

        # Sticks (Standard ControllerState polarity: positive UP)
        lx_val = state.lx
        ly_val = state.ly
        rx_val = state.rx
        ry_val = state.ry
        is_ls_blocked = ('ls' in consumed) or ('ls' in active_layer_blocks)
        if is_ls_blocked or ('ls' in self.blocked_buttons):
            lx_val, ly_val = 0.0, 0.0
        else:
            # 1. Apply Warped Stick Correction
            lx_val, ly_val = math_utils.apply_warped_stick_correction(lx_val, ly_val, getattr(self, 'ls_warp', 0.0))

            # 2. Circularity Correction & Process Analog Stick
            if getattr(self, 'ls_circ_mode', 'disabled') == 'before':
                lx_val, ly_val = math_utils.apply_circularity_correction(lx_val, ly_val, getattr(self, 'ls_circ_cx', 0.0), getattr(self, 'ls_circ_cy', 0.0), getattr(self, 'ls_circ_bounds', None))
                lx_val, ly_val = math_utils.process_analog_stick(lx_val, ly_val, self.ls_inner, self.ls_adz, self.ls_curve, self.ls_power, getattr(self, 'ls_rest_dz', 0.0), getattr(self, 'ls_sens', 1.0), getattr(self, 'ls_custom', ''))
            elif getattr(self, 'ls_circ_mode', 'disabled') == 'after':
                lx_val, ly_val = math_utils.process_analog_stick(lx_val, ly_val, self.ls_inner, self.ls_adz, self.ls_curve, self.ls_power, getattr(self, 'ls_rest_dz', 0.0), getattr(self, 'ls_sens', 1.0), getattr(self, 'ls_custom', ''))
                lx_val, ly_val = math_utils.apply_circularity_correction(lx_val, ly_val, getattr(self, 'ls_circ_cx', 0.0), getattr(self, 'ls_circ_cy', 0.0), getattr(self, 'ls_circ_bounds', None))
            else:
                lx_val, ly_val = math_utils.process_analog_stick(lx_val, ly_val, self.ls_inner, self.ls_adz, self.ls_curve, self.ls_power, getattr(self, 'ls_rest_dz', 0.0), getattr(self, 'ls_sens', 1.0), getattr(self, 'ls_custom', ''))

        is_rs_blocked = ('rs' in consumed) or ('rs' in active_layer_blocks)
        if is_rs_blocked or ('rs' in self.blocked_buttons):
            rx_val, ry_val = 0.0, 0.0
        else:
            # 1. Apply Warped Stick Correction
            rx_val, ry_val = math_utils.apply_warped_stick_correction(rx_val, ry_val, getattr(self, 'rs_warp', 0.0))

            # 2. Circularity Correction & Process Analog Stick
            if getattr(self, 'rs_circ_mode', 'disabled') == 'before':
                rx_val, ry_val = math_utils.apply_circularity_correction(rx_val, ry_val, getattr(self, 'rs_circ_cx', 0.0), getattr(self, 'rs_circ_cy', 0.0), getattr(self, 'rs_circ_bounds', None))
                rx_val, ry_val = math_utils.process_analog_stick(rx_val, ry_val, self.rs_inner, self.rs_adz, self.rs_curve, self.rs_power, getattr(self, 'rs_rest_dz', 0.0), getattr(self, 'rs_sens', 1.0), getattr(self, 'rs_custom', ''))
            elif getattr(self, 'rs_circ_mode', 'disabled') == 'after':
                rx_val, ry_val = math_utils.process_analog_stick(rx_val, ry_val, self.rs_inner, self.rs_adz, self.rs_curve, self.rs_power, getattr(self, 'rs_rest_dz', 0.0), getattr(self, 'rs_sens', 1.0), getattr(self, 'rs_custom', ''))
                rx_val, ry_val = math_utils.apply_circularity_correction(rx_val, ry_val, getattr(self, 'rs_circ_cx', 0.0), getattr(self, 'rs_circ_cy', 0.0), getattr(self, 'rs_circ_bounds', None))
            else:
                rx_val, ry_val = math_utils.process_analog_stick(rx_val, ry_val, self.rs_inner, self.rs_adz, self.rs_curve, self.rs_power, getattr(self, 'rs_rest_dz', 0.0), getattr(self, 'rs_sens', 1.0), getattr(self, 'rs_custom', ''))

        # Joysticks: Scale float (-1.0 to 1.0) to XInput int (-32768 to 32767)
        lx_int = math_utils.clamp_int(int(lx_val * 32767), -32768, 32767)
        ly_int = math_utils.clamp_int(int(ly_val * 32767), -32768, 32767)
        rx_int = math_utils.clamp_int(int(rx_val * 32767), -32768, 32767)
        ry_int = math_utils.clamp_int(int(ry_val * 32767), -32768, 32767)

        self.gamepad.left_joystick(x_value=lx_int, y_value=ly_int)
        self.gamepad.right_joystick(x_value=rx_int, y_value=ry_int)

        # Helper function for pressing or releasing standard buttons
        def handle_btn(btn_name, state_val, xusb_btn):
            is_blocked = (btn_name in consumed) or (btn_name in active_layer_blocks)
            active = (state_val and not is_blocked) or (btn_name in self.macro_pressed_buttons)
            if active:
                self.gamepad.press_button(button=xusb_btn)
            else:
                self.gamepad.release_button(button=xusb_btn)

        # Buttons
        handle_btn('a', state.a, vg.XUSB_BUTTON.XUSB_GAMEPAD_A)
        handle_btn('b', state.b, vg.XUSB_BUTTON.XUSB_GAMEPAD_B)
        handle_btn('x', state.x, vg.XUSB_BUTTON.XUSB_GAMEPAD_X)
        handle_btn('y', state.y, vg.XUSB_BUTTON.XUSB_GAMEPAD_Y)
        handle_btn('lb', state.lb, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER)
        handle_btn('rb', state.rb, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER)
        handle_btn('select', state.select, vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK)
        handle_btn('start', state.start, vg.XUSB_BUTTON.XUSB_GAMEPAD_START)

        # Home button logic is special since it defaults to guide mapping
        is_home_blocked = ('home' in consumed) or ('home' in active_layer_blocks)
        if self.home_mapping == 'guide':
            if ('home' in self.macro_pressed_buttons) or (state.home and not is_home_blocked):
                self.gamepad.press_button(
                    button=vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE)
            else:
                self.gamepad.release_button(
                    button=vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE)
        else:
            if 'home' in self.macro_pressed_buttons:
                self.gamepad.press_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE)
            else:
                self.gamepad.release_button(button=vg.XUSB_BUTTON.XUSB_GAMEPAD_GUIDE)

        handle_btn('l3', state.l3, vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB)
        handle_btn('r3', state.r3, vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB)

        # D-Pad
        handle_btn(
            'dpad_up',
            state.dpad_up,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP)
        handle_btn(
            'dpad_down',
            state.dpad_down,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_DOWN)
        handle_btn(
            'dpad_left',
            state.dpad_left,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_LEFT)
        handle_btn(
            'dpad_right',
            state.dpad_right,
            vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_RIGHT)

        self.gamepad.update()

    def press_gamepad_button(self, btn_name):
        btn = btn_name.lower().replace('gamepad:', '').strip()
        self.macro_pressed_buttons.add(btn)
        if btn == 'lt':
            self.gamepad.left_trigger_float(value_float=1.0)
            self.gamepad.update()
        elif btn == 'rt':
            self.gamepad.right_trigger_float(value_float=1.0)
            self.gamepad.update()
        elif btn in BUTTON_MAP:
            self.gamepad.press_button(button=BUTTON_MAP[btn])
            self.gamepad.update()

    def release_gamepad_button(self, btn_name):
        btn = btn_name.lower().replace('gamepad:', '').strip()
        self.macro_pressed_buttons.discard(btn)
        if btn == 'lt':
            self.gamepad.left_trigger_float(value_float=0.0)
            self.gamepad.update()
        elif btn == 'rt':
            self.gamepad.right_trigger_float(value_float=0.0)
            self.gamepad.update()
        elif btn in BUTTON_MAP:
            self.gamepad.release_button(button=BUTTON_MAP[btn])
            self.gamepad.update()
