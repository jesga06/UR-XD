# SECTION 2 PART A: EXHAUSTIVE FUNCTION SPECIFICATIONS

### MODULE: backend_base.py (src/backend_base.py)

================================================================================
FUNCTION SPECIFICATION: __init__
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def __init__(self)`
   - Source File / Module: `src/backend_base.py` / `BaseInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Main thread typically

2. OPERATIONAL PURPOSE
   - Primary Purpose: Initializes the abstract base input backend class, setting up the `callback` attribute to None.
   - Trigger Source: Initialization (Object instantiation)

3. INPUT PARAMETERS
   - `self`: The instance of the class.

4. STATE MUTATION & SIDE EFFECTS
   - Sets `self.callback = None`

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None

7. TIMING, LATENCY & RATE LIMITING
   - Immediate execution.

================================================================================
FUNCTION SPECIFICATION: set_callback
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def set_callback(self, callback: Callable[[ControllerState], None])`
   - Source File / Module: `src/backend_base.py` / `BaseInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe if called before polling starts.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Sets the callback function to receive normalized `ControllerState` updates.
   - Trigger Source: Initialization or configuration step by parent controller.

3. INPUT PARAMETERS
   - `self`: The instance of the class.
   - `callback`: `Callable[[ControllerState], None]` - A function that takes a `ControllerState` and returns `None`.

4. STATE MUTATION & SIDE EFFECTS
   - Mutates `self.callback` to the provided `callback` function.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None natively; type errors if called improperly.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate execution.

================================================================================
FUNCTION SPECIFICATION: initialize
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def initialize(self) -> bool`
   - Source File / Module: `src/backend_base.py` / `BaseInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Main thread usually

2. OPERATIONAL PURPOSE
   - Primary Purpose: Initialize the backend and scan for devices. Returns True if a device is ready.
   - Trigger Source: Initialization step

3. INPUT PARAMETERS
   - `self`: The instance of the class.

4. STATE MUTATION & SIDE EFFECTS
   - None in base class.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `bool` - Expected to return True if successful, False otherwise.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Raises `NotImplementedError`: This is an abstract method.

7. TIMING, LATENCY & RATE LIMITING
   - N/A

================================================================================
FUNCTION SPECIFICATION: shutdown
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def shutdown(self)`
   - Source File / Module: `src/backend_base.py` / `BaseInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Main thread

2. OPERATIONAL PURPOSE
   - Primary Purpose: Release resources and disconnect.
   - Trigger Source: User action (closing app) or backend teardown.

3. INPUT PARAMETERS
   - `self`: The instance of the class.

4. STATE MUTATION & SIDE EFFECTS
   - None in base class.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Raises `NotImplementedError`: This is an abstract method.

7. TIMING, LATENCY & RATE LIMITING
   - N/A

================================================================================
FUNCTION SPECIFICATION: poll
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def poll(self)`
   - Source File / Module: `src/backend_base.py` / `BaseInputBackend`
   - Execution Context: Synchronous / Blocking
   - Threading / Safety: Should be run in a dedicated thread.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Synchronous or asynchronous polling loop. Depending on the backend, this might block in a thread or be called periodically.
   - Trigger Source: Backend event (polling thread started).

3. INPUT PARAMETERS
   - `self`: The instance of the class.

4. STATE MUTATION & SIDE EFFECTS
   - None in base class.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Raises `NotImplementedError`: This is an abstract method.

7. TIMING, LATENCY & RATE LIMITING
   - N/A

================================================================================
FUNCTION SPECIFICATION: get_capabilities
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def get_capabilities(self) -> dict`
   - Source File / Module: `src/backend_base.py` / `BaseInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Return flags indicating supported features (e.g., {'vibration': True, 'analog_triggers': True}).
   - Trigger Source: Backend Initialization / Query.

3. INPUT PARAMETERS
   - `self`: The instance of the class.

4. STATE MUTATION & SIDE EFFECTS
   - None in base class.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `dict`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Raises `NotImplementedError`: This is an abstract method.

7. TIMING, LATENCY & RATE LIMITING
   - N/A

================================================================================
FUNCTION SPECIFICATION: set_vibration
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def set_vibration(self, left_motor: float, right_motor: float)`
   - Source File / Module: `src/backend_base.py` / `BaseInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Set rumble intensities.
   - Trigger Source: Backend Event / Game request.

3. INPUT PARAMETERS
   - `self`: The instance of the class.
   - `left_motor`: `float` - Range 0.0 to 1.0 representing left motor speed.
   - `right_motor`: `float` - Range 0.0 to 1.0 representing right motor speed.

4. STATE MUTATION & SIDE EFFECTS
   - None in base class.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Raises `NotImplementedError`: This is an abstract method.

7. TIMING, LATENCY & RATE LIMITING
   - N/A

================================================================================
FUNCTION SPECIFICATION: get_connection_state
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def get_connection_state(self) -> bool`
   - Source File / Module: `src/backend_base.py` / `BaseInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Check if the device is currently connected and active.
   - Trigger Source: Periodic query.

3. INPUT PARAMETERS
   - `self`: The instance of the class.

4. STATE MUTATION & SIDE EFFECTS
   - None in base class.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `bool` - True if connected.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Raises `NotImplementedError`: This is an abstract method.

7. TIMING, LATENCY & RATE LIMITING
   - N/A

### MODULE: backend_dinput.py (src/backend_dinput.py)

================================================================================
FUNCTION SPECIFICATION: __init__
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def __init__(self, hid_map_path: str, vid: int, pid: int, req_ifaces: list = None)`
   - Source File / Module: `src/backend_dinput.py` / `DInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Main thread

2. OPERATIONAL PURPOSE
   - Primary Purpose: Initializes the DInput backend state and configuration variables.
   - Trigger Source: Object instantiation.

3. INPUT PARAMETERS
   - `self`: The instance.
   - `hid_map_path`: `str` - Path to the JSON configuration describing the HID layout.
   - `vid`: `int` - Target Vendor ID.
   - `pid`: `int` - Target Product ID.
   - `req_ifaces`: `list` (optional) - Target interface numbers.

4. STATE MUTATION & SIDE EFFECTS
   - Calls `super().__init__()`.
   - Mutates `self.hid_map_path`, `self.target_vid`, `self.target_pid`, `self.req_ifaces`, `self.readers`, `self.decoder`, `self.is_running`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None locally.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate.

================================================================================
FUNCTION SPECIFICATION: get_capabilities
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def get_capabilities(self) -> dict`
   - Source File / Module: `src/backend_dinput.py` / `DInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Returns capabilities supported by DInput backend.
   - Trigger Source: Explicit query.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - None.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `dict` - `{'vibration': False, 'analog_triggers': True, 'guide_button': True, 'extra_buttons': True}`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate.

================================================================================
FUNCTION SPECIFICATION: initialize
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def initialize(self) -> bool`
   - Source File / Module: `src/backend_dinput.py` / `DInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Main thread

2. OPERATIONAL PURPOSE
   - Primary Purpose: Loads Decoder, enumerates HID devices, filters by VID/PID and requested interfaces, and connects HIDReader instances.
   - Trigger Source: Initialization routine.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Initializes `self.decoder`.
   - Modifies `self.readers` list by appending connected `HIDReader` instances.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `bool` - `True` if at least one device reader connected, `False` otherwise.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Catches `Exception`, logs it, and returns `False`.

7. TIMING, LATENCY & RATE LIMITING
   - Blocks while enumerating and connecting to HID devices. Might take a few milliseconds.

================================================================================
FUNCTION SPECIFICATION: get_connection_state
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def get_connection_state(self) -> bool`
   - Source File / Module: `src/backend_dinput.py` / `DInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Check if we have active HID readers.
   - Trigger Source: Polling query.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - None.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `bool` - `True` if `len(self.readers) > 0`, `False` otherwise.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate.

================================================================================
FUNCTION SPECIFICATION: shutdown
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def shutdown(self)`
   - Source File / Module: `src/backend_dinput.py` / `DInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Must be called to tear down safely.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Stops polling loop and disconnects all HID readers.
   - Trigger Source: Application shutdown or backend switch.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Sets `self.is_running = False`.
   - Calls `stop()` on all readers in `self.readers`.
   - Clears `self.readers`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None locally.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate to flag, threads take moments to exit.

================================================================================
FUNCTION SPECIFICATION: set_vibration
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def set_vibration(self, left_motor: float, right_motor: float)`
   - Source File / Module: `src/backend_dinput.py` / `DInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Set vibration, but acts as a no-op since DInput doesn't support it here.
   - Trigger Source: Game event.

3. INPUT PARAMETERS
   - `self`: Instance.
   - `left_motor`: `float`
   - `right_motor`: `float`

4. STATE MUTATION & SIDE EFFECTS
   - None.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate.

================================================================================
FUNCTION SPECIFICATION: poll
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def poll(self)`
   - Source File / Module: `src/backend_dinput.py` / `DInputBackend`
   - Execution Context: Blocking / Event-driven inner threads
   - Threading / Safety: Blocks current thread.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Starts HID readers on daemon threads, sets up data handling callback to decode packets, and blocks until shutdown.
   - Trigger Source: Application start polling.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Sets `self.is_running = True`.
   - Mutates `callback` of each reader.
   - Spawns threading.Thread for each reader.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None explicitly thrown; logs warning if no readers.

7. TIMING, LATENCY & RATE LIMITING
   - Sleeps for 1.0 second intervals while `self.is_running`.

### MODULE: backend_xinput.py (src/backend_xinput.py)

================================================================================
FUNCTION SPECIFICATION: __init__
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def __init__(self)`
   - Source File / Module: `src/backend_xinput.py` / `XInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Main thread

2. OPERATIONAL PURPOSE
   - Primary Purpose: Loads XInput DLL and initializes state vars.
   - Trigger Source: Object instantiation.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Calls `super().__init__()`.
   - Modifies `self.connected_slot`, `self.target_slot`, `self.is_running`, `self._thread`, `self.poll_rate_hz`, `self.last_packet_number`.
   - Calls `_load_xinput()`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None explicitly raised.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate.

================================================================================
FUNCTION SPECIFICATION: _load_xinput
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def _load_xinput(self)`
   - Source File / Module: `src/backend_xinput.py` / `XInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Main thread

2. OPERATIONAL PURPOSE
   - Primary Purpose: Iterates possible XInput DLL names and loads the first valid one using ctypes. Binds C functions.
   - Trigger Source: Initialization.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Mutates `self.xinput`, `self.XInputGetState`, `self.XInputGetStateEx`, `self.XInputSetState`.
   - Loads a C dynamic library into memory.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Silently catches generic `Exception` when failing to load a specific DLL. Logs error if none loaded.
   - Catches `AttributeError` if `XInputGetStateEx` (ordinal 100) is absent.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate.

================================================================================
FUNCTION SPECIFICATION: get_capabilities
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def get_capabilities(self) -> dict`
   - Source File / Module: `src/backend_xinput.py` / `XInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Returns capabilities. `guide_button` is True only if `XInputGetStateEx` is loaded.
   - Trigger Source: Explicit query.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - None.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `dict` - `{'vibration': True, 'analog_triggers': True, 'guide_button': bool, 'extra_buttons': False}`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate.

================================================================================
FUNCTION SPECIFICATION: initialize
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def initialize(self) -> bool`
   - Source File / Module: `src/backend_xinput.py` / `XInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Polls controller slots 0-3 via XInput to find an active controller. Attempts target_slot first.
   - Trigger Source: Backend startup or reconnection loop.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Modifies `self.connected_slot` and `self.target_slot`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `bool` - `True` if controller found, `False` otherwise.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Very low latency C API call.

================================================================================
FUNCTION SPECIFICATION: get_connection_state
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def get_connection_state(self) -> bool`
   - Source File / Module: `src/backend_xinput.py` / `XInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Checks if the currently assigned `connected_slot` yields a success return code from `XInputGetState`.
   - Trigger Source: Polling loop or query.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - None.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `bool`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Extremely fast C API check.

================================================================================
FUNCTION SPECIFICATION: shutdown
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def shutdown(self)`
   - Source File / Module: `src/backend_xinput.py` / `XInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Safely flags thread stop.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Stop polling loop, join thread, zero out vibration.
   - Trigger Source: App teardown.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Mutates `self.is_running = False`.
   - Blocks to join `self._thread` up to 1.0s.
   - Modifies device state (vibration to 0).

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Up to 1.0s wait latency.

================================================================================
FUNCTION SPECIFICATION: set_vibration
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def set_vibration(self, left_motor: float, right_motor: float)`
   - Source File / Module: `src/backend_xinput.py` / `XInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Translates 0.0-1.0 floats to 0-65535 integers and sends via `XInputSetState`.
   - Trigger Source: Application request.

3. INPUT PARAMETERS
   - `self`: Instance.
   - `left_motor`: `float` - Range [0.0, 1.0]
   - `right_motor`: `float` - Range [0.0, 1.0]

4. STATE MUTATION & SIDE EFFECTS
   - Modifies hardware state directly via DLL.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Fails silently if `connected_slot < 0` or no API pointer.

7. TIMING, LATENCY & RATE LIMITING
   - Fast execution; hardware might rate limit actual physical updates.

================================================================================
FUNCTION SPECIFICATION: _normalize_axis
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def _normalize_axis(self, value)`
   - Source File / Module: `src/backend_xinput.py` / `XInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Normalizes raw 16-bit signed integer [-32768, 32767] to float [-1.0, 1.0], implementing a center snap/deadzone of +/- 128.
   - Trigger Source: Polling decoding.

3. INPUT PARAMETERS
   - `self`: Instance.
   - `value`: `int` - raw axis value.

4. STATE MUTATION & SIDE EFFECTS
   - None.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `float` - Normalized value.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate computation.

================================================================================
FUNCTION SPECIFICATION: poll
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def poll(self)`
   - Source File / Module: `src/backend_xinput.py` / `XInputBackend`
   - Execution Context: Blocking loop
   - Threading / Safety: Expected to run on a background thread.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Polls controller at `poll_rate_hz` (500Hz). Fetches state, normalizes everything to `ControllerState`, calls `callback`, handles disconnections / retries.
   - Trigger Source: `start_polling_thread`

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Sets `self.is_running = True`.
   - Iteratively mutates local `state` struct.
   - Disconnects controller `self.connected_slot = -1` on 20 consecutive errors.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Handles connection loss gracefully.
   - If `XInputGetStateEx` fails, falls back to `XInputGetState`.

7. TIMING, LATENCY & RATE LIMITING
   - Sleeps precise intervals to maintain 500Hz loop. Reconnects attempt every 1.0s.

================================================================================
FUNCTION SPECIFICATION: start_polling_thread
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def start_polling_thread(self)`
   - Source File / Module: `src/backend_xinput.py` / `XInputBackend`
   - Execution Context: Synchronous
   - Threading / Safety: Spawns new thread.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Starts the `poll` method in a background daemon thread.
   - Trigger Source: System setup.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Instantiates and starts `self._thread`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None natively handled.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate thread dispatch.

### MODULE: decoder.py (src/decoder.py)

================================================================================
FUNCTION SPECIFICATION: __init__
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def __init__(self, hid_map_path: str)`
   - Source File / Module: `src/decoder.py` / `Decoder`
   - Execution Context: Synchronous
   - Threading / Safety: Main thread

2. OPERATIONAL PURPOSE
   - Primary Purpose: Loads JSON HID map file from path to configure reporting schema. Sets up base `ControllerState`.
   - Trigger Source: Object instantiation.

3. INPUT PARAMETERS
   - `self`: Instance.
   - `hid_map_path`: `str` - Path to JSON file.

4. STATE MUTATION & SIDE EFFECTS
   - Parses JSON from disk. Mutates `profile`, `reports_config`, `has_report_ids`, `use_length_as_id`, `state`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Catches `json.JSONDecodeError` and logs error.
   - Catches `Exception` and logs error.
   - Ignores completely if file not found, logging a warning.

7. TIMING, LATENCY & RATE LIMITING
   - Blocking disk I/O on init.

================================================================================
FUNCTION SPECIFICATION: decode
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def decode(self, report: RawHIDReport) -> ControllerState`
   - Source File / Module: `src/decoder.py` / `Decoder`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe relative to one data stream.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Processes raw byte payloads of a HID report based on the configured JSON rules. Updates and returns the persistent `ControllerState`. Extracts buttons (bitmasks), axes (normalization/deadzone/inversion), triggers, and hats.
   - Trigger Source: HID event callback.

3. INPUT PARAMETERS
   - `self`: Instance.
   - `report`: `RawHIDReport` - The raw payload wrapper.

4. STATE MUTATION & SIDE EFFECTS
   - Mutates `self.state` in-place retaining previous state where bytes haven't changed. Calls `_set_state`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `ControllerState` - Current processed controller layout.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Avoids `IndexError` by bounds checking `byte_idx + length > len(data)`.
   - Ignores unsupported lengths.

7. TIMING, LATENCY & RATE LIMITING
   - Extremely fast computation.

================================================================================
FUNCTION SPECIFICATION: _set_state
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def _set_state(self, key: str, value: Any) -> None`
   - Source File / Module: `src/decoder.py` / `Decoder`
   - Execution Context: Synchronous
   - Threading / Safety: Part of decoding pipeline.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Routes decoded values to either the standard `ControllerState` properties via `setattr`, or into the `extra_inputs` dict if arbitrary.
   - Trigger Source: `decode` method.

3. INPUT PARAMETERS
   - `self`: Instance.
   - `key`: `str` - Name of the input.
   - `value`: `Any` - The decoded boolean or float value.

4. STATE MUTATION & SIDE EFFECTS
   - Mutates fields on `self.state` or `self.state.extra_inputs`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate.

### MODULE: hid_reader.py (src/hid_reader.py)

================================================================================
FUNCTION SPECIFICATION: __init__
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def __init__(self, device_path=None, auto_reconnect=True, interface_number=-1)`
   - Source File / Module: `src/hid_reader.py` / `HIDReader`
   - Execution Context: Synchronous
   - Threading / Safety: Main thread

2. OPERATIONAL PURPOSE
   - Primary Purpose: Setup configuration variables for hidapi interface reading.
   - Trigger Source: Object instantiation.

3. INPUT PARAMETERS
   - `self`: Instance.
   - `device_path`: Optional device path string from hid.enumerate().
   - `auto_reconnect`: `bool` - Reconnect on loss.
   - `interface_number`: `int` - Interface.

4. STATE MUTATION & SIDE EFFECTS
   - Mutates instance attributes.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate.

================================================================================
FUNCTION SPECIFICATION: get_all_devices
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def get_all_devices()`
   - Source File / Module: `src/hid_reader.py` / `HIDReader`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe static method.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Wraps `hid.enumerate()` to return list of connected devices.
   - Trigger Source: System query.

3. INPUT PARAMETERS
   - None.

4. STATE MUTATION & SIDE EFFECTS
   - Reads system device tree.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `list` of `dict` detailing HID devices.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Bubble-up errors from hidapi C module.

7. TIMING, LATENCY & RATE LIMITING
   - System dependent polling time.

================================================================================
FUNCTION SPECIFICATION: connect
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def connect(self)`
   - Source File / Module: `src/hid_reader.py` / `HIDReader`
   - Execution Context: Synchronous
   - Threading / Safety: Blocking

2. OPERATIONAL PURPOSE
   - Primary Purpose: Opens the HID device pointer via `hid.device().open_path()`, sets it to non-blocking.
   - Trigger Source: Explicit connect call.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Allocates `self.device`.
   - Modifies `self._last_product_name` and `self._connected_time`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `bool` - `True` if successful, `False` on failure.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Catches `Exception` on connection, sets device to None, returns `False`.
   - Catches `Exception` gracefully when getting product string.

7. TIMING, LATENCY & RATE LIMITING
   - Might block briefly depending on OS hid interface speed.

================================================================================
FUNCTION SPECIFICATION: set_callback
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def set_callback(self, callback)`
   - Source File / Module: `src/hid_reader.py` / `HIDReader`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe

2. OPERATIONAL PURPOSE
   - Primary Purpose: Assigns the function to be invoked on receiving a raw packet.
   - Trigger Source: Config step.

3. INPUT PARAMETERS
   - `self`: Instance.
   - `callback`: Function expecting `RawHIDReport`.

4. STATE MUTATION & SIDE EFFECTS
   - Mutates `self.callback`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate.

================================================================================
FUNCTION SPECIFICATION: start
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def start(self)`
   - Source File / Module: `src/hid_reader.py` / `HIDReader`
   - Execution Context: Blocking loop
   - Threading / Safety: Expected to run on dedicated thread.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Infinite loop polling `self.device.read(1024)`. Packages raw bytes into `RawHIDReport` and dispatches to callback. Checks for exceptions to handle disconnects.
   - Trigger Source: App thread start.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Mutates `self._running = True`.
   - Can invoke `_handle_disconnect`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Handles `OSError`: Trigger disconnect logic. Avoids reconnecting immediately if failed right away (OS permissions block).
   - Handles `ValueError`: Exits if device pointer closed.

7. TIMING, LATENCY & RATE LIMITING
   - Uses `time.sleep(0.001)` to reduce CPU load since socket is non-blocking. High polling rate ~1000Hz.

================================================================================
FUNCTION SPECIFICATION: send_output_report
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def send_output_report(self, data: list[int])`
   - Source File / Module: `src/hid_reader.py` / `HIDReader`
   - Execution Context: Synchronous
   - Threading / Safety: Thread-safe typically, writes to HID.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Pushes raw byte report downstream to device.
   - Trigger Source: Explicit app call (e.g., rumble request).

3. INPUT PARAMETERS
   - `self`: Instance.
   - `data`: `list[int]` - Payload bytes.

4. STATE MUTATION & SIDE EFFECTS
   - Writes directly to hardware bus.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `bool` - True on success.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Returns False if bytes_written is -1.
   - Catches `Exception`, logs, and returns False.

7. TIMING, LATENCY & RATE LIMITING
   - Quick write, bounded by USB speed.

================================================================================
FUNCTION SPECIFICATION: _handle_disconnect
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def _handle_disconnect(self)`
   - Source File / Module: `src/hid_reader.py` / `HIDReader`
   - Execution Context: Blocking
   - Threading / Safety: Runs within the start loop thread.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Loops for 20 seconds calling `hid.enumerate()` trying to re-find and reconnect to the lost device via product string.
   - Trigger Source: `OSError` in read loop.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Closes old `self.device`.
   - Updates `self.device_path`.
   - Re-instantiates `self.device` via `connect()`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `bool` - True if recovered, False if timed out.

6. COMPLETE ERROR & EXCEPTION MATRIX
   - Hides close exceptions.

7. TIMING, LATENCY & RATE LIMITING
   - Blocking up to 20 seconds. Polls system tree every 1.0s.

================================================================================
FUNCTION SPECIFICATION: stop
================================================================================
1. IDENTIFIER & SIGNATURE
   - Full Signature: `def stop(self)`
   - Source File / Module: `src/hid_reader.py` / `HIDReader`
   - Execution Context: Synchronous
   - Threading / Safety: Safely breaks start loop.

2. OPERATIONAL PURPOSE
   - Primary Purpose: Sets running flag to false and safely closes the HID handle.
   - Trigger Source: Shutdown event.

3. INPUT PARAMETERS
   - `self`: Instance.

4. STATE MUTATION & SIDE EFFECTS
   - Mutates `self._running = False`.
   - Closes and nullifies `self.device`.

5. RETURN VALUE & PAYLOAD INTERPRETATION
   - Return Value: `None`

6. COMPLETE ERROR & EXCEPTION MATRIX
   - None explicitly managed.

7. TIMING, LATENCY & RATE LIMITING
   - Immediate flag switch. File handle release might take microseconds.
