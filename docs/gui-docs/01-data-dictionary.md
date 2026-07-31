# SECTION 1: GLOBAL DATA DICTIONARY & ENUMS

### ControllerState
- **Source File:** `src/decoder.py`
- **Python Type:** `dataclass`

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| a | `bool` | No | `True` / `False` | `False` | Mapped to Face Button A UI indicator |
| b | `bool` | No | `True` / `False` | `False` | Mapped to Face Button B UI indicator |
| x | `bool` | No | `True` / `False` | `False` | Mapped to Face Button X UI indicator |
| y | `bool` | No | `True` / `False` | `False` | Mapped to Face Button Y UI indicator |
| lb | `bool` | No | `True` / `False` | `False` | Mapped to Left Bumper UI indicator |
| rb | `bool` | No | `True` / `False` | `False` | Mapped to Right Bumper UI indicator |
| select | `bool` | No | `True` / `False` | `False` | Mapped to Select/Back UI indicator |
| start | `bool` | No | `True` / `False` | `False` | Mapped to Start UI indicator |
| home | `bool` | No | `True` / `False` | `False` | Mapped to Home/Guide UI indicator |
| l3 | `bool` | No | `True` / `False` | `False` | Mapped to L3/Left Stick Click UI indicator |
| r3 | `bool` | No | `True` / `False` | `False` | Mapped to R3/Right Stick Click UI indicator |
| dpad_up | `bool` | No | `True` / `False` | `False` | Mapped to D-pad Up UI indicator |
| dpad_down | `bool` | No | `True` / `False` | `False` | Mapped to D-pad Down UI indicator |
| dpad_left | `bool` | No | `True` / `False` | `False` | Mapped to D-pad Left UI indicator |
| dpad_right | `bool` | No | `True` / `False` | `False` | Mapped to D-pad Right UI indicator |
| lx | `float` | No | `[-1.0, 1.0]`, negative=left, positive=right | `0.0` | Left Stick X-axis visualizer |
| ly | `float` | No | `[-1.0, 1.0]`, negative=down, positive=up | `0.0` | Left Stick Y-axis visualizer |
| rx | `float` | No | `[-1.0, 1.0]`, negative=left, positive=right | `0.0` | Right Stick X-axis visualizer |
| ry | `float` | No | `[-1.0, 1.0]`, negative=down, positive=up | `0.0` | Right Stick Y-axis visualizer |
| lt | `float` | No | `[0.0, 1.0]`, 0.0=released, 1.0=fully pressed | `0.0` | Left Trigger analog visualizer |
| rt | `float` | No | `[0.0, 1.0]`, 0.0=released, 1.0=fully pressed | `0.0` | Right Trigger analog visualizer |
| extra_inputs | `Dict[str, Any]` | No | Values can be `bool` or `float` | `{}` | Extra dynamic UI inputs if configured |

### RawHIDReport
- **Source File:** `src/hid_reader.py`
- **Python Type:** `dataclass` (aliased as `HIDReport`)

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| report_id | `int` | No | `0-255` | None | N/A (Internal) |
| payload | `List[int]` | No | Each element `0-255`, max length 1024 | None | N/A (Internal raw hex view if applicable) |
| timestamp | `float` | No | `time.perf_counter()` value in seconds | None | Latency/Time graphs |
| interface_number | `int` | No | USB interface endpoint index | `-1` | N/A (Internal) |
| data | `property` | No | Alias for `payload` | None | N/A (Internal) |

### XINPUT_GAMEPAD
- **Source File:** `src/backend_xinput.py`
- **Python Type:** `ctypes.Structure`

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| wButtons | `c_ushort` (WORD) | No | `0x0000-0xFFFF` | None | Raw hex readout in debug view |
| bLeftTrigger | `c_ubyte` (BYTE) | No | `0-255` | None | Raw trigger value in debug view |
| bRightTrigger | `c_ubyte` (BYTE) | No | `0-255` | None | Raw trigger value in debug view |
| sThumbLX | `c_short` (SHORT) | No | `-32768` to `32767` | None | Raw axis value in debug view |
| sThumbLY | `c_short` (SHORT) | No | `-32768` to `32767` | None | Raw axis value in debug view |
| sThumbRX | `c_short` (SHORT) | No | `-32768` to `32767` | None | Raw axis value in debug view |
| sThumbRY | `c_short` (SHORT) | No | `-32768` to `32767` | None | Raw axis value in debug view |

### XINPUT_STATE
- **Source File:** `src/backend_xinput.py`
- **Python Type:** `ctypes.Structure`

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| dwPacketNumber | `c_uint` (DWORD) | No | `0` to `2^32-1` | None | Packet counter in debug view |
| Gamepad | `XINPUT_GAMEPAD` | No | Valid `XINPUT_GAMEPAD` struct | None | N/A (Nested struct) |

### XINPUT_VIBRATION
- **Source File:** `src/backend_xinput.py`
- **Python Type:** `ctypes.Structure`

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| wLeftMotorSpeed | `c_ushort` (WORD) | No | `0-65535` | None | Motor intensity slider |
| wRightMotorSpeed | `c_ushort` (WORD) | No | `0-65535` | None | Motor intensity slider |

### XInput Button Constants
- **Source File:** `src/backend_xinput.py`
- **Python Type:** `int` (Constants)

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| XINPUT_GAMEPAD_DPAD_UP | `int` | No | `0x0001` | `0x0001` | Internal bitmask mapping |
| XINPUT_GAMEPAD_DPAD_DOWN | `int` | No | `0x0002` | `0x0002` | Internal bitmask mapping |
| XINPUT_GAMEPAD_DPAD_LEFT | `int` | No | `0x0004` | `0x0004` | Internal bitmask mapping |
| XINPUT_GAMEPAD_DPAD_RIGHT | `int` | No | `0x0008` | `0x0008` | Internal bitmask mapping |
| XINPUT_GAMEPAD_START | `int` | No | `0x0010` | `0x0010` | Internal bitmask mapping |
| XINPUT_GAMEPAD_BACK | `int` | No | `0x0020` | `0x0020` | Internal bitmask mapping |
| XINPUT_GAMEPAD_LEFT_THUMB | `int` | No | `0x0040` | `0x0040` | Internal bitmask mapping |
| XINPUT_GAMEPAD_RIGHT_THUMB | `int` | No | `0x0080` | `0x0080` | Internal bitmask mapping |
| XINPUT_GAMEPAD_LEFT_SHOULDER | `int` | No | `0x0100` | `0x0100` | Internal bitmask mapping |
| XINPUT_GAMEPAD_RIGHT_SHOULDER | `int` | No | `0x0200` | `0x0200` | Internal bitmask mapping |
| XINPUT_GAMEPAD_GUIDE | `int` | No | `0x0400` | `0x0400` | Internal bitmask mapping |
| XINPUT_GAMEPAD_A | `int` | No | `0x1000` | `0x1000` | Internal bitmask mapping |
| XINPUT_GAMEPAD_B | `int` | No | `0x2000` | `0x2000` | Internal bitmask mapping |
| XINPUT_GAMEPAD_X | `int` | No | `0x4000` | `0x4000` | Internal bitmask mapping |
| XINPUT_GAMEPAD_Y | `int` | No | `0x8000` | `0x8000` | Internal bitmask mapping |

### BUTTON_MAP
- **Source File:** `src/virtual_pad.py`
- **Python Type:** `dict`

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| [button_name_string] | `int` | No | Maps string (e.g., 'a', 'lb') to vgamepad `XUSB_BUTTON` enum | None | Used to translate UI mappings to vgamepad calls |

### ControllerConfig (Default Schema)
- **Source File:** `src/config_manager.py`
- **Python Type:** `dict` (JSON schema)

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| settings | `dict` | No | Arbitrary top-level settings | `{}` | Profile settings UI |
| extra_buttons | `dict` | No | Button mappings | `{}` | Profile remapping UI |
| block_xinput | `dict` | No | Map button_name to bool string | `{}` | Button blocker UI |
| shift_layer | `dict` | No | Main shift layer dict | `{}` | Shift layer settings tab |
| shift_mappings | `dict` | No | Mappings for primary shift layer | `{}` | Shift layer remap UI |
| shift_block_xinput | `dict` | No | Blocker for primary shift layer | `{}` | Shift layer blocker UI |
| shift_layers | `list` | No | Array of Shift Layer Schemas | `[]` | Multiple shift layers UI |
| chords | `dict` | No | Macros/Chords definitions | `{}` | Chords UI |
| hardware_chords | `dict` | No | Hardware level chords | `{}` | Chords UI |
| backend | `dict` | No | Backend specific config | `{}` | Backend settings UI |
| analog | `dict` | No | Base analog overrides | `{}` | Analog settings UI |
| analog_left / analog_right / trigger_left / trigger_right | `dict` | No | Contains: `deadzone`, `anti_deadzone`, `curve`, `exp_factor` (all strings) | `deadzone='0.05'`, `anti_deadzone='0.0'`, `curve='linear'`, `exp_factor='2.0'` | Deadzone/Curve configuration panels |

### Shift Layer Schema
- **Source File:** `src/config_manager.py`
- **Python Type:** `dict`

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| id | `str` | No | Unique identifier (e.g., 'shift_1') | None | Shift layer list internal ID |
| name | `str` | No | Display name | None | Shift layer list display name |
| trigger_button | `str` | Yes | Empty or valid button name | None | Shift layer trigger dropdown |
| modifier_button | `str` | Yes | Empty or valid button name | None | Shift layer modifier dropdown |
| mode | `str` | No | `'hold'` or `'toggle'` | None | Mode radio button/dropdown |
| haptic_profile | `str` | Yes | Haptic DSL string or empty | None | Haptic profile entry field |
| mappings | `dict` | No | Map button_name to action_string | None | Remap grid within layer |
| block_xinput | `dict` | No | Map button_name to `'true'`/`'false'` | None | Blocker grid within layer |

### Haptic Event Schema
- **Source File:** `src/haptic_engine.py`
- **Python Type:** `dict` (parsed from string)

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| motor | `str` | No | `'LM'` or `'RM'` | None | Haptic visualizer motor axis |
| intensity | `float` | No | `[0.0, 1.0]` | None | Haptic visualizer amplitude |
| start_s | `float` | No | `>= 0.0` | None | Haptic visualizer timeline start |
| duration_s | `float` | No | `>= 0.01` | None | Haptic visualizer block width |
| end_s | `float` | No | `start_s + duration_s` | None | Haptic visualizer timeline end |

### LatencyMonitor Stats Schema
- **Source File:** `src/utilities_backend.py`
- **Python Type:** `dict`

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| polling_rate_hz | `float` | No | `>= 0.0` (1 decimal precision) | None | Polling Rate display label |
| avg_process_ms | `float` | No | `>= 0.0` (3 decimals precision) | None | Average Latency display label |
| max_process_ms | `float` | No | `>= 0.0` (3 decimals precision) | None | Maximum Latency display label |

### config.ini Schema
- **Source File:** `config.ini` (Global)
- **Python Type:** `dict` / `configparser`

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| community.db_last_updated | `float` | No | Unix timestamp | None | Last update status text |
| community.db_update_interval_days | `float` | No | `>= 0.0` | `7.0` | Update frequency setting |
| controller.last_device | `str` | Yes | Device identifier | None | Dropdown auto-selection |
| controller.last_profile | `str` | Yes | Path to JSON | None | Profile list auto-selection |
| backend.mode | `str` | No | `'xinput'`, `'dinput'`, `'auto'` | None | Backend mode dropdown |
| UI.appearance | `str` | No | `'Dark'`, `'Light'` | None | Application Appearance toggle |
| UI.theme | `str` | No | `'blue'`, `'green'`, `'orange'`, `'purple'`, `'red'`, `'white'`, `'yellow'` | None | Theme selector dropdown |
| UI.last_tab | `int` | No | `0-5` | None | Tab bar active index |
| UI.geometry | `str` | No | Hex string | None | Main window position |
| Stick_Left.circularity_center_x | `float` | No | Offset value | None | Circularity calibrator UI |
| Stick_Left.circularity_center_y | `float` | No | Offset value | None | Circularity calibrator UI |
| Stick_Left.circularity_bounds | `str` | No | 360 comma-separated floats | None | Circularity calibrator UI |
| Stick_Left.circularity_mode | `str` | No | `'disabled'`, `'before'`, `'after'` | None | Circularity mode dropdown |

### Curve Type Enum
- **Source File:** `src/curves.py`
- **Python Type:** `str` (Implicit Enum)

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| curve_type | `str` | No | `'linear'`, `'exponential'`, `'relaxed'`, `'aggressive'`, `'cubic'`, `'sigmoid'`, `'bezier'`, `'dotted'`, `'custom'` | None | Curve selector dropdown menu |

### Controller Layout Enum
- **Source File:** `src/calibration.py`
- **Python Type:** `str` (Implicit Enum)

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| layout | `str` | No | `'xbox'`, `'playstation'`, `'nintendo'` | None | Button prompt style selector |

### Circularity Mode Enum
- **Source File:** `config.ini`
- **Python Type:** `str` (Implicit Enum)

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| circularity_mode | `str` | No | `'disabled'`, `'before'`, `'after'` | None | Circularity mode dropdown |

### Backend Mode Enum
- **Source File:** `config.ini`
- **Python Type:** `str` (Implicit Enum)

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| mode | `str` | No | `'xinput'`, `'dinput'`, `'auto'` | None | Backend selection dropdown |

### Theme JSON Schema
- **Source File:** `src/themes/*.json`
- **Python Type:** `dict`

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| [color_properties] | `list` | No | Array of `[light_color_hex, dark_color_hex]` | None | Applied to CTk widgets (e.g. `fg_color`, `text_color`, `border_color`, etc.) |
| corner_radius | `int` | No | `>= 0` | None | Widget corner rounding |
| border_width | `int` | No | `>= 0` | None | Widget border thickness |
| button_length | `int` | No | `>= 0` | None | Specific dimension constraint |
| [font_properties] | `dict` | No | OS-specific font configurations | None | Application fonts |

### _SAFE_MATH_DICT
- **Source File:** `src/curves.py`
- **Python Type:** `Dict[str, Any]`

| Field Name | Data Type | Nullable | Valid Range / Constraints | Default Value | GUI Mapping |
| --- | --- | --- | --- | --- | --- |
| [math_functions] | `function` | No | Filtered Python `math` module (no dunders) (e.g., `sin`, `cos`, `tan`, `sqrt`, `log`, `exp`, `pi`, `e`) | None | Available context for custom curve text box evaluation |
