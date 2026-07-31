# SECTION 2 PART C: EXHAUSTIVE FUNCTION SPECIFICATIONS

This section details the exhaustive zero-ambiguity backend specifications for GUI developers for the listed modules, adhering strictly to a 7-part template for every function.

## MODULE: virtual_pad.py (src/virtual_pad.py)

**Globals:**
- `BUTTON_MAP`: Dictionary mapping string names (e.g., 'a', 'lb') to `vgamepad.XUSB_BUTTON` enums.

### Class: VirtualPad

#### 1. Name
`VirtualPad.__init__`
#### 2. Purpose
Initializes a new instance of the VirtualPad class, creating a virtual Xbox 360 controller using `vgamepad`, setting up mappings and state variables, and registering the haptic feedback handler.
#### 3. Parameters
- `config` (ConfigParser or None): Configuration object containing initial settings. Default is `None`.
#### 4. Returns
- `None`
#### 5. Exceptions
- `Exception`: Raises any exception encountered when initializing `vg.VX360Gamepad()`. Logs an error before raising.
#### 6. Side Effects
- Instantiates a virtual ViGEmBus Xbox 360 controller device at the OS level.
- Modifies instance state: `home_mapping`, `blocked_buttons`, `macro_pressed_buttons`, `rumble_callback`, `haptic_engine`.
#### 7. Implementation Details
Registers `_vgamepad_notification_handler` for ViGEmBus force feedback notifications. Calls `reload_config(config)` immediately to apply attributes.

---

#### 1. Name
`VirtualPad.set_rumble_callback`
#### 2. Purpose
Sets a callback function to handle standard rumble events sent from the game to the virtual controller.
#### 3. Parameters
- `callback` (Callable): Function with signature `callback(left_motor: int, right_motor: int)` where values are 0-255.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Mutates `self.rumble_callback`.
#### 7. Implementation Details
Simple setter for the rumble callback.

---

#### 1. Name
`VirtualPad.set_haptic_engine`
#### 2. Purpose
Sets the haptic engine instance used for executing custom vibration profiles and hijacking rumble.
#### 3. Parameters
- `engine` (HapticEngine): The haptic engine instance.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Mutates `self.haptic_engine`.
#### 7. Implementation Details
Provides a reference to the haptic engine for use in the notification handler.

---

#### 1. Name
`VirtualPad.set_vibration`
#### 2. Purpose
Manually dispatches a vibration event, scaling the values from 0-65535 down to 0-255 for the internal rumble callback.
#### 3. Parameters
- `lm` (int): Left motor intensity, range 0 to 65535.
- `rm` (int): Right motor intensity, range 0 to 65535.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Triggers the registered `self.rumble_callback` if present.
#### 7. Implementation Details
Divides `lm` and `rm` by 257 (scaling to 0-255) and passes integers to the callback.

---

#### 1. Name
`VirtualPad._vgamepad_notification_handler`
#### 2. Purpose
Internal callback triggered by `vgamepad` when the OS/game sends a force feedback (rumble) request.
#### 3. Parameters
- `client` (Any): The vgamepad client.
- `target` (Any): The target device.
- `large_motor` (int): Left motor intensity (0-255).
- `small_motor` (int): Right motor intensity (0-255).
- `led_number` (int): The LED index.
- `user_data` (Any): Custom user data pointer.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Triggers `self.rumble_callback` with `large_motor` and `small_motor`.
#### 7. Implementation Details
If `self.haptic_engine.is_hijacked` is `True`, it returns immediately, dropping the game's rumble request to prioritize custom haptic profiles.

---

#### 1. Name
`VirtualPad.reload_config`
#### 2. Purpose
Reapplies configurations, deadzones, curves, and maps blocked buttons based on a provided configuration object.
#### 3. Parameters
- `config` (Any or None): The configuration object containing sections like 'trigger_left', 'analog_left', 'shift_layers'.
#### 4. Returns
- `None`
#### 5. Exceptions
- None explicitly raised, may throw `ValueError` if configuration types are invalid.
#### 6. Side Effects
- Resets and populates `self.blocked_buttons` and `self.macro_pressed_buttons`.
- Sets instance attributes for trigger and analog curves, deadzones, and sensitivities.
#### 7. Implementation Details
Iterates through specific configuration sections to parse parameters. Automatically populates `blocked_buttons` with inputs remapped to key/mouse functions across all layers to prevent dual-input overlap.

---

#### 1. Name
`VirtualPad.process`
#### 2. Purpose
Translates standard `ControllerState` values into `vgamepad` API calls, applying blocking, curves, circularity, and deadzones.
#### 3. Parameters
- `state` (ControllerState): The normalized state of the physical controller.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Updates the OS-level state of the virtual Xbox 360 controller.
#### 7. Implementation Details
Converts float inputs (-1.0 to 1.0) into XInput integers (-32768 to 32767). Pre-processes triggers and sticks using `math_utils`. Applies `ls_circ_mode` / `rs_circ_mode` either 'before' or 'after' deadzone logic. Uses a helper function `handle_btn` to evaluate if a button is blocked, physically pressed, or macro-pressed before syncing to ViGEmBus. Calls `self.gamepad.update()` at the end.

---

#### 1. Name
`VirtualPad.press_gamepad_button`
#### 2. Purpose
Simulates a macro-driven button press on the virtual controller.
#### 3. Parameters
- `btn_name` (str): Name of the button to press (e.g., 'a', 'lt', 'gamepad:b').
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Modifies `self.macro_pressed_buttons`.
- Immediately updates virtual controller state and calls `self.gamepad.update()`.
#### 7. Implementation Details
Strips 'gamepad:' prefix, lowercases, adds to `macro_pressed_buttons`. Hardcodes 'lt' and 'rt' to float 1.0, and maps others via `BUTTON_MAP`.

---

#### 1. Name
`VirtualPad.release_gamepad_button`
#### 2. Purpose
Simulates a macro-driven button release on the virtual controller.
#### 3. Parameters
- `btn_name` (str): Name of the button to release.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Modifies `self.macro_pressed_buttons`.
- Immediately updates virtual controller state and calls `self.gamepad.update()`.
#### 7. Implementation Details
Removes the button from `macro_pressed_buttons` and sets the corresponding `vgamepad` property to 0.0 or unpressed.


## MODULE: mapper.py (src/mapper.py)

### Class: Mapper

#### 1. Name
`Mapper.__init__`
#### 2. Purpose
Initializes the input mapper engine, creating pynput controllers and starting the high-frequency mouse interpolation thread.
#### 3. Parameters
- `config` (Any): Configuration object to load initial mappings and layer settings.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Spawns a daemon thread `_mouse_interpolation_loop` running at ~250Hz.
- Initializes OS-level `pynput.mouse.Controller` and `pynput.keyboard.Controller`.
#### 7. Implementation Details
Sets up empty structures for active layers, chords, shift layers, held buttons, and WASD tracking. Calls `reload_config(config)`.

---

#### 1. Name
`Mapper.set_haptic_engine`
#### 2. Purpose
Injects a reference to the haptic engine for executing vibration feedback on layer transitions.
#### 3. Parameters
- `engine` (HapticEngine): The instantiated haptic engine.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Mutates `self.haptic_engine`.
#### 7. Implementation Details
Standard dependency injection.

---

#### 1. Name
`Mapper.reload_config`
#### 2. Purpose
Rebuilds the layer mappings, chords, and shift definitions from the provided config object.
#### 3. Parameters
- `config` (Any): Configuration object.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Overwrites `self.mappings`, `self.chords`, and `self.shift_layers`.
#### 7. Implementation Details
Reads `layer_base` and multi-shift layers. Extracts mappings containing '+' into `self.chords` arrays, deleting them from standard single-button mappings.

---

#### 1. Name
`Mapper._mouse_interpolation_loop`
#### 2. Purpose
Background thread function that interpolates analog stick values into discrete OS mouse movements at a fixed high tick rate.
#### 3. Parameters
- None
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Continuously invokes `pynput.mouse.Controller.move`.
#### 7. Implementation Details
Runs a `while self.mouse_thread_active:` loop with `time.sleep(1.0 / 250.0)`. Safely reads `self.mouse_dx` and `self.mouse_dy` using `self.mouse_lock`, casting floats to ints for pynput.

---

#### 1. Name
`Mapper._execute_macro`
#### 2. Purpose
Delegates the execution of a named macro to the `macro_executor`.
#### 3. Parameters
- `macro_name` (str): Name of the macro to execute or toggle.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Asynchronously starts or stops macro threads via `self.macro_executor`.
#### 7. Implementation Details
Checks if `self.macro_executor` exists, then calls `execute_or_toggle(macro_name)`.

---

#### 1. Name
`Mapper._press_key_sequence`
#### 2. Purpose
Simulates pressing a sequence of keyboard keys (e.g., chords or single keys).
#### 3. Parameters
- `keys` (List[str]): List of key names to press.
#### 4. Returns
- `None`
#### 5. Exceptions
- None directly raised; inner exceptions caught and logged.
#### 6. Side Effects
- Issues OS keyboard press events via pynput.
#### 7. Implementation Details
Iterates keys. Handles duplicate keys by releasing, sleeping 15ms, and re-pressing. Supports `pynput.keyboard.Key` enums and single char `KeyCode`s.

---

#### 1. Name
`Mapper._release_key_sequence`
#### 2. Purpose
Simulates releasing a sequence of keyboard keys.
#### 3. Parameters
- `keys` (List[str]): List of key names to release.
#### 4. Returns
- `None`
#### 5. Exceptions
- None directly raised; inner exceptions caught and logged.
#### 6. Side Effects
- Issues OS keyboard release events via pynput.
#### 7. Implementation Details
Iterates over the `keys` list in reverse order. Avoids duplicate release calls using a `released` set tracking.

---

#### 1. Name
`Mapper._press`
#### 2. Purpose
Parses a mapped string action and routes it to the correct subsystem (macro, virtual pad, mouse, or keyboard).
#### 3. Parameters
- `mapping` (str): The mapped action string (e.g., 'macro:test', 'mouse:left', 'keyboard:shift+w').
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Triggers hardware simulations via pynput or vgamepad. Modifies scroll state if applicable.
#### 7. Implementation Details
Delegates based on string prefixes. Native gamepad strings are routed to `self.virtual_pad.press_gamepad_button`. Scroll commands update `self.active_scrolls` if continuous. Keyboard strings split on '+' and pass to `_press_key_sequence`.

---

#### 1. Name
`Mapper._release`
#### 2. Purpose
Parses a mapped string action and releases the corresponding subsystems.
#### 3. Parameters
- `mapping` (str): The mapped action string.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Reverts hardware simulations via pynput or vgamepad.
#### 7. Implementation Details
Mirrors `_press`, removing active scrolls, calling `release_gamepad_button`, or invoking `_release_key_sequence` (splitting by '+').

---

#### 1. Name
`Mapper._process_wasd`
#### 2. Purpose
Converts normalized analog 2D coordinate values into discrete digital WASD keyboard inputs with debounce logic.
#### 3. Parameters
- `x` (float): Analog stick X axis (-1.0 to 1.0).
- `y` (float): Analog stick Y axis (-1.0 to 1.0).
- `threshold` (float): Activation threshold (default 0.5).
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Issues keyboard presses/releases via `self._press` and `self._release`. Mutates `self.wasd_state` and `self.wasd_debounce_timers`.
#### 7. Implementation Details
Uses standard boolean comparison against the threshold. If state changes to pressed, checks debounce timer (> 50ms) before sending press to avoid mechanical snap-back registering as opposite input.

---

#### 1. Name
`Mapper.process`
#### 2. Purpose
Main processing loop for mapping logic. Detects button edges, evaluates shift layers and chords, handles analog mouse/WASD generation, and tracks active holds.
#### 3. Parameters
- `state` (ControllerState): The current normalized controller state.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Changes active layer, mutates multiple state dicts (`active_holds`, `pending_inputs`, `toggled_shift_layers`), queues continuous scrolls, modifies mouse velocities.
#### 7. Implementation Details
Merges native buttons and extra buttons. Detects edges to trigger toggle-mode shift layers. Resolves the `target_layer` prioritizing dual-button shift chords over single-button triggers. On layer transitions, releases `active_holds` and fires `HapticEngine` profile. Converts analog inputs to mouse velocities under a mutex lock. Resolves chords using rollback or delay-buffer modes. Dispatches `_press` and `_release` logic. Process active repeat scrolling ticks.

---

#### 1. Name
`Mapper._parse_scroll_mapping`
#### 2. Purpose
Parses advanced scroll action strings into configuration dicts.
#### 3. Parameters
- `mapping` (str): E.g., 'mouse:scroll_up:continuous:1:0.05'.
#### 4. Returns
- `dict`: Parsed keys 'direction', 'mode', 'notches', 'interval', 'last_run_time'.
#### 5. Exceptions
- Catches `ValueError` for cast failures and logs an error, falling back to defaults.
#### 6. Side Effects
- None
#### 7. Implementation Details
Splits string by colons, using safe index checks and try/except parsing for notches and interval floats. Default interval is 0.05s.

---

#### 1. Name
`Mapper._do_scroll_parsed`
#### 2. Purpose
Executes a single parsed scroll tick using pynput.
#### 3. Parameters
- `parsed` (dict): Dict returned by `_parse_scroll_mapping`.
#### 4. Returns
- `None`
#### 5. Exceptions
- Catches generic `Exception` from pynput without crashing.
#### 6. Side Effects
- Modifies OS mouse scroll state.
#### 7. Implementation Details
Maps direction string to dx/dy values and calls `self.mouse.scroll(dx, dy)`.


## MODULE: haptic_engine.py (src/haptic_engine.py)

#### 1. Name
`parse_haptic_profile`
#### 2. Purpose
Parses a haptic vibration string definition into chronological blocks of intensity and timing.
#### 3. Parameters
- `profile_str` (str): Definition string (e.g., 'RM[30% @ 0ms, dur=1500ms]').
#### 4. Returns
- `List[Dict[str, Any]]`: List of events sorted by `start_s`. Keys: `motor`, `intensity`, `start_s`, `duration_s`, `end_s`.
#### 5. Exceptions
- None explicitly raised; uses safe regex matching.
#### 6. Side Effects
- None
#### 7. Implementation Details
Uses regex to extract blocks matching `(RM|LM|BOTH)`. Extracts percentage and duration/start parameters. Supports both `@ Xms, dur=Yms` and fallback `X-Yms` range formats. Normalizes intensity to 0.0-1.0 float and timing to seconds. Duplicates 'BOTH' into discrete LM and RM events. Returns a chronologically sorted list.

### Class: HapticEngine

#### 1. Name
`HapticEngine.__init__`
#### 2. Purpose
Initializes state for the background haptic processing system.
#### 3. Parameters
- `virtual_pad` (Optional[Any]): The virtual pad instance to dispatch vibrations to. Default None.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Instantiates threading primitives (Event, Lock).
#### 7. Implementation Details
Initializes thread handles, `stop_event`, and `is_hijacked` flag to False.

---

#### 1. Name
`HapticEngine.set_virtual_pad`
#### 2. Purpose
Sets the reference to the virtual pad object.
#### 3. Parameters
- `virtual_pad` (Any): Reference to VirtualPad.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Mutates `self.virtual_pad`.
#### 7. Implementation Details
Standard setter.

---

#### 1. Name
`HapticEngine.play_profile`
#### 2. Purpose
Parses a profile and spawns a daemon thread to execute the haptic timeline, interrupting any ongoing profile.
#### 3. Parameters
- `profile_str` (str): The haptic profile definition string.
#### 4. Returns
- `bool`: True if profile is valid and started, False if empty or unparseable.
#### 5. Exceptions
- None
#### 6. Side Effects
- Stops existing threads, sets `self.is_hijacked = True`, spawns a new daemon thread.
#### 7. Implementation Details
Calls `parse_haptic_profile`. Uses a mutex lock to safely trigger `self.stop()`, clear the `stop_event`, set hijacked to True, and launch `_run_timeline`.

---

#### 1. Name
`HapticEngine.stop`
#### 2. Purpose
Halts any active haptic vibration playback and cleanly resets state.
#### 3. Parameters
- None
#### 4. Returns
- `None`
#### 5. Exceptions
- Catches and drops exceptions from `virtual_pad.set_vibration`.
#### 6. Side Effects
- Sets threading events, blocks up to 100ms for thread join, mutates `is_hijacked`, zeroes hardware motors.
#### 7. Implementation Details
Sets `stop_event`. Joins `active_thread` with a timeout to avoid hangs. Resets `is_hijacked` to False and forces `set_vibration(0, 0)` via the virtual pad.

---

#### 1. Name
`HapticEngine._run_timeline`
#### 2. Purpose
Background thread target function that evaluates the haptic timeline and pushes high-resolution updates to the motors.
#### 3. Parameters
- `events` (List[Dict[str, Any]]): Parsed and sorted list of motor events.
#### 4. Returns
- `None`
#### 5. Exceptions
- Catches generic exceptions during dispatch and logs them.
#### 6. Side Effects
- Rapidly calls `virtual_pad.set_vibration`. Mutates `is_hijacked` to False on completion.
#### 7. Implementation Details
Finds `total_duration` max bound. Uses `time.perf_counter()` for high-precision looping while `stop_event` is un-set. In each loop iteration (10ms sleep), evaluates which event blocks overlap `t_curr` and takes the `max()` intensity per motor. Casts 0.0-1.0 floats to 0-65535 integers for API. Gracefully returns control by zeroing vibration and clearing `is_hijacked` at completion.


## MODULE: hardware_chords.py (src/hardware_chords.py)

### Class: HardwareChordEngine

#### 1. Name
`HardwareChordEngine.__init__`
#### 2. Purpose
Initializes hardware chord processing and tracking state.
#### 3. Parameters
- `config` (Optional[Any]): Configuration object to parse initial hardware chords.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Initializes lists and dicts. Calls `reload_config` if config is present.
#### 7. Implementation Details
Sets up `poll_intervals` tracking to default to 4ms (250Hz).

---

#### 1. Name
`HardwareChordEngine.reload_config`
#### 2. Purpose
Loads physical hardware chords from the configuration, parsing keys, target actions, delays, and delayed member keys.
#### 3. Parameters
- `config` (Any): Configuration object.
#### 4. Returns
- `None`
#### 5. Exceptions
- Catches `ValueError` when attempting to cast invalid manual delays to floats.
#### 6. Side Effects
- Clears and rebuilds `self.chords`, clears state dicts (`pending_inputs`, `executed_chords`).
#### 7. Implementation Details
Looks for the `[hardware_chords]` section. Parses semicolon separated KV pairs. Converts delay ms strings to float seconds.

---

#### 1. Name
`HardwareChordEngine._get_button_state`
#### 2. Purpose
Helper to extract a boolean state for a specific button from the `ControllerState` object.
#### 3. Parameters
- `state` (ControllerState): Current physical state.
- `btn` (str): The button name.
#### 4. Returns
- `bool`: True if button is pressed above 0.1 threshold, False otherwise.
#### 5. Exceptions
- None
#### 6. Side Effects
- None
#### 7. Implementation Details
Handles both standard attributes via `getattr` and `extra_inputs` dict lookups. Coerces floats > 0.1 to True.

---

#### 1. Name
`HardwareChordEngine._set_button_state`
#### 2. Purpose
Helper to override a boolean state for a specific button within the `ControllerState` object.
#### 3. Parameters
- `state` (ControllerState): The object to mutate.
- `btn` (str): Button name.
- `val` (bool): The desired override state.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Mutates the attributes or `extra_inputs` inside the passed `state` object.
#### 7. Implementation Details
If attribute exists, sets it to 1.0 (if originally a float) or standard bool. Otherwise assigns to `extra_inputs`.

---

#### 1. Name
`HardwareChordEngine.record_poll_interval`
#### 2. Purpose
Maintains a rolling average of time deltas between calls to adapt auto-delay chord timing.
#### 3. Parameters
- None
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Mutates `self.poll_intervals`, `self.avg_poll_interval`, and `self.last_report_time`.
#### 7. Implementation Details
Calculates delta using `time.time()`. Ignores deltas > 100ms. Maintains a history buffer of 50 samples.

---

#### 1. Name
`HardwareChordEngine.process`
#### 2. Purpose
Evaluates chords, enforces input suppression by zeroing out constituent buttons in the state object, and handles timeout logic for delay buffering.
#### 3. Parameters
- `state` (ControllerState): The physical state report to process and modify.
#### 4. Returns
- `ControllerState`: The mutated state object.
#### 5. Exceptions
- None
#### 6. Side Effects
- Heavily mutates the properties of the passed `state` object.
- Modifies tracking dicts: `pending_inputs`, `executed_chords`.
#### 7. Implementation Details
Builds a `current_pressed` set of all physical inputs. Trims released buttons from trackers. Iterates defined chords. If a chord is already executed, it suppresses (sets to False) all constituent keys in the `state` object and injects the output action as True. If a chord's components are fully pressed now, it marks it executed and suppresses the keys. If only a `delayed_btn` is pressed, it buffers the input, hiding it from the `state` object until the timeout (either manual or 2x `avg_poll_interval`) is exceeded.


## MODULE: macro_executor.py (src/macro_executor.py)

### Class: MacroExecutor

#### 1. Name
`MacroExecutor.__init__`
#### 2. Purpose
Initializes state for executing macros and loads macro definitions from a JSON file.
#### 3. Parameters
- `mapper` (Any): Reference to the main Mapper class to trigger actions.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Initializes threading objects. Loads files from disk.
#### 7. Implementation Details
Calls `load_macros()` on startup.

---

#### 1. Name
`MacroExecutor.load_macros`
#### 2. Purpose
Loads JSON array sequences from `macros.json`.
#### 3. Parameters
- None
#### 4. Returns
- `None`
#### 5. Exceptions
- Catches generic exceptions during file read/JSON parsing and logs them.
#### 6. Side Effects
- Reads `macros.json` from the working directory. Modifies `self.macros`.
#### 7. Implementation Details
Uses `utf-8` encoding. Sets `self.macros` to empty dict on failure.

---

#### 1. Name
`MacroExecutor.execute_or_toggle`
#### 2. Purpose
Initiates execution of a macro in a new thread, or stops it if it is already the currently running macro (toggle behavior).
#### 3. Parameters
- `macro_name` (str): The identifier key in the loaded macros dictionary.
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Mutates `self.active_macro`, sets thread `stop_event`, joins existing threads, spawns new daemon threads.
#### 7. Implementation Details
Guarded by `self.lock`. If macro is active, cancels it and returns. If another macro is active, cancels it and proceeds. Clears `stop_event` and spawns a thread targeting `_run_macro` with the requested sequence list.

---

#### 1. Name
`MacroExecutor._run_macro`
#### 2. Purpose
Thread target that steps through a macro sequence array, issuing instructions to the mapper and executing high-precision wait periods.
#### 3. Parameters
- `macro_name` (str): Name of the executing macro.
- `sequence` (List[Dict[str, Any]]): Ordered array of action dicts (press, release, wait).
#### 4. Returns
- `None`
#### 5. Exceptions
- None
#### 6. Side Effects
- Calls `self.mapper._press` and `self.mapper._release` methods. Modifies `self.active_macro` upon completion.
#### 7. Implementation Details
Iterates through the sequence dict. Checks `self.stop_event.is_set()` every step. Extracts `action`. Invokes mapper directly with the provided string `key`. When `action == 'wait'`, computes target completion time and enters a while loop with 5ms `time.sleep` intervals, allowing for sub-wait-step interruption if the `stop_event` is triggered. Clears `self.active_macro` when gracefully exiting.


## MODULE: input_graph.py (src/input_graph.py)

#### 1. Name
`main`
#### 2. Purpose
Launches a standalone Matplotlib live-animation window listening for UDP JSON packets containing analog controller telemetry.
#### 3. Parameters
- None
#### 4. Returns
- `None`
#### 5. Exceptions
- Fails abruptly if port 9999 is already in use by another application.
#### 6. Side Effects
- Binds a UDP socket on 127.0.0.1:9999.
- Spawns GUI matplotlib window blocking the main thread.
#### 7. Implementation Details
Sets up a non-blocking UDP socket. Configures `collections.deque` objects for sticks and triggers with a max length of 100 points. Constructs 2 subplots (Sticks and Triggers) with predefined legends, limits, and colors. Defines nested `update(frame)` function.

---

#### 1. Name
`update` (Nested inside `main`)
#### 2. Purpose
Matplotlib animation frame callback that drains the UDP socket, parses the JSON payload, and updates the graph line data points.
#### 3. Parameters
- `frame` (Any): Frame index passed automatically by `FuncAnimation`.
#### 4. Returns
- `Tuple`: Returns the modified matplotlib Line2D objects (`line_lx`, `line_ly`, etc.)
#### 5. Exceptions
- Safely catches `BlockingIOError` (no data available) and generic decoding `Exception`s.
#### 6. Side Effects
- Modifies local variables from `main` scope (`t_counter`, deques, line data).
#### 7. Implementation Details
Drains the socket with a `while True` loop to ensure only the latest packet is parsed (dropping stale backlog). Extracts `lx`, `ly`, `rx`, `ry`, `lt`, `rt` from JSON using `.get` with 0.0 defaults. Appends to `collections.deque`s. Calls `.set_data` on all lines. Automatically pans the x-axis `set_xlim` forward once history exceeds 100 points. Runs at roughly ~50Hz (20ms interval).
