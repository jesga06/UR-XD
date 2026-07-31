# SECTION 2 PART B: EXHAUSTIVE FUNCTION SPECIFICATIONS

### MODULE: config_manager.py
**Filepath**: `src/config_manager.py`

#### Function: `get_sanitized_filename(name: str, mode: Optional[str] = None) -> str`
- **1. Purpose**: Sanitizes a string to be a safe JSON filename by replacing non-alphanumeric chars, converting spaces to underscores, and lowercasing.
- **2. Parameters**:
  - `name` (str): The raw string name to sanitize.
  - `mode` (Optional[str], default=None): An optional mode string to append before the extension.
- **3. Return Value**:
  - (str): The sanitized filename ending in `.json`. Format is `[cleaned].json` or `[cleaned]_[mode].json`.
- **4. Exceptions/Errors**: None explicitly raised.
- **5. Side Effects**: None.
- **6. Dependencies**: `re` (Standard Library).
- **7. GUI Mapping**: Used implicitly when generating default filenames for saving profiles in the GUI.

#### Class: `ControllerConfig`
**Description**: Manages JSON configuration profiles for controller mappings, deadzones, response curves, and macro settings.

##### Method: `__init__(self, filepath: Optional[str] = None)`
- **1. Purpose**: Initializes the configuration object, loading from file if provided and exists, otherwise initializing defaults.
- **2. Parameters**:
  - `filepath` (Optional[str], default=None): The path to the JSON configuration file.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: Safe initialization. File loading errors are handled by `load()`.
- **5. Side Effects**: Assigns instance variables `self.filepath` and `self.data`. May perform file I/O.
- **6. Dependencies**: `os.path.exists`, `self.load`, `self._init_defaults`.
- **7. GUI Mapping**: Instantiated when application loads profiles or switches configurations.

##### Method: `_init_defaults(self) -> None`
- **1. Purpose**: Populates `self.data` with the default configuration skeleton for mappings, deadzones, curves, and shift layers.
- **2. Parameters**: None.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Overwrites `self.data` completely with a predefined dictionary structure.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Serves as the fallback state if profile loading fails or when creating a new blank profile from the GUI.

##### Method: `load(self) -> None`
- **1. Purpose**: Reads the JSON file at `self.filepath` into `self.data` and runs migration scripts.
- **2. Parameters**: None.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: Catches generic `Exception`. Logs error and falls back to `_init_defaults()`.
- **5. Side Effects**: Modifies `self.data`. Reads from disk. Writes to logs on error.
- **6. Dependencies**: `json.load`, `logger.error`, `self._migrate_shift_layers`, `self._init_defaults`.
- **7. GUI Mapping**: Called when loading a profile from the Profile Selector dropdown.

##### Method: `_migrate_shift_layers(self) -> None`
- **1. Purpose**: Upgrades legacy configuration formats (single shift layer) to the modern multi-layer format (`shift_layers` list).
- **2. Parameters**: None.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Mutates `self.data` by creating a `shift_layers` list if it doesn't exist.
- **6. Dependencies**: `self.get`, `self._sync_legacy_shift_fields`.
- **7. GUI Mapping**: Transparent to GUI, ensures old profiles open correctly in the Shift Layers UI.

##### Method: `_sync_legacy_shift_fields(self) -> None`
- **1. Purpose**: Backports the primary shift layer data into legacy fields (`shift_layer`, `shift_mappings`, `shift_block_xinput`) for backward compatibility.
- **2. Parameters**: None.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Modifies `self.data` legacy root keys based on the first item in `shift_layers`.
- **6. Dependencies**: None.
- **7. GUI Mapping**: None direct.

##### Method: `get_shift_layers(self) -> List[Dict[str, Any]]`
- **1. Purpose**: Retrieves the list of all shift layers. Runs migration dynamically if missing.
- **2. Parameters**: None.
- **3. Return Value**:
  - (List[Dict[str, Any]]): The list of shift layer dictionaries.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: May mutate `self.data` if migration is triggered.
- **6. Dependencies**: `self._migrate_shift_layers`.
- **7. GUI Mapping**: Populates the Shift Layer management tabs/lists in the GUI.

##### Method: `set_shift_layers(self, layers: List[Dict[str, Any]]) -> None`
- **1. Purpose**: Replaces the entire shift layer list and syncs legacy fields.
- **2. Parameters**:
  - `layers` (List[Dict[str, Any]]): The new list of shift layer objects.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Overwrites `self.data["shift_layers"]` and updates legacy keys.
- **6. Dependencies**: `self._sync_legacy_shift_fields`.
- **7. GUI Mapping**: Called when the user bulk-saves shift layer reordering or applies a new set of layers from the GUI.

##### Method: `add_shift_layer(self, name: str = "", trigger_button: str = "", modifier_button: str = "", mode: str = "hold", haptic_profile: str = "") -> Dict[str, Any]`
- **1. Purpose**: Creates and appends a new shift layer to the configuration.
- **2. Parameters**:
  - `name` (str): Custom layer name. Defaults to "Shift Layer N".
  - `trigger_button` (str): Button to activate the layer.
  - `modifier_button` (str): Secondary modifier button.
  - `mode` (str): Activation mode, default "hold".
  - `haptic_profile` (str): Layer-specific haptics.
- **3. Return Value**:
  - (Dict[str, Any]): The newly created layer dictionary.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Modifies `self.data` by appending to `shift_layers` list.
- **6. Dependencies**: `self.get_shift_layers`, `self.set_shift_layers`.
- **7. GUI Mapping**: Called by the "Add Layer" button in the Shift Layers UI.

##### Method: `remove_shift_layer(self, layer_id: str) -> None`
- **1. Purpose**: Removes a shift layer by its ID. Prevents removing the last remaining layer.
- **2. Parameters**:
  - `layer_id` (str): The string ID of the layer to remove (e.g., "shift_2").
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Removes an item from `self.data["shift_layers"]`.
- **6. Dependencies**: `self.get_shift_layers`, `self.set_shift_layers`.
- **7. GUI Mapping**: Called by the "Delete Layer" button in the Shift Layers UI.

##### Method: `get_global_haptic_profile(self) -> str`
- **1. Purpose**: Gets the global default haptic profile string.
- **2. Parameters**: None.
- **3. Return Value**:
  - (str): The profile string, defaults to `"RM[30% @ 0ms, dur=1500ms]"`.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Populates the global haptics text input in the GUI.

##### Method: `set_global_haptic_profile(self, profile: str) -> None`
- **1. Purpose**: Sets the global default haptic profile.
- **2. Parameters**:
  - `profile` (str): The new profile string.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Mutates `self.data["haptics"]["global_default"]`.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Saves text input from the global haptics GUI field.

##### Method: `get_haptic_enabled(self) -> bool`
- **1. Purpose**: Checks if global haptics are enabled.
- **2. Parameters**: None.
- **3. Return Value**:
  - (bool): True if enabled, defaults to True.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Binds to the "Enable Haptics" checkbox in the UI.

##### Method: `set_haptic_enabled(self, enabled: bool) -> None`
- **1. Purpose**: Toggles global haptics state.
- **2. Parameters**:
  - `enabled` (bool): Boolean toggle state.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Mutates `self.data["haptics"]["enabled"]`.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Activated by toggling the "Enable Haptics" checkbox.

##### Method: `get_effective_layer_haptic_profile(self, layer_id: str) -> str`
- **1. Purpose**: Returns the haptic profile for a specific layer. Falls back to global profile if empty.
- **2. Parameters**:
  - `layer_id` (str): The ID of the shift layer.
- **3. Return Value**:
  - (str): The effective haptic profile string.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: `self.get_shift_layers`, `self.get_global_haptic_profile`.
- **7. GUI Mapping**: Used by the backend engine; indirectly shown as a fallback in layer-specific GUI text inputs.

##### Method: `save(self) -> None`
- **1. Purpose**: Serializes `self.data` to the JSON file at `self.filepath`.
- **2. Parameters**: None.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: Catches generic `Exception`. Logs error on failure.
- **5. Side Effects**: Performs disk write. May create parent directories. Writes to log on error.
- **6. Dependencies**: `os.makedirs`, `json.dump`, `logger.error`.
- **7. GUI Mapping**: Called by the "Save Profile" button.

##### Method: `has_section(self, section: str) -> bool`
- **1. Purpose**: Checks if a top-level section key exists.
- **2. Parameters**:
  - `section` (str): Section name.
- **3. Return Value**:
  - (bool): True if present.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Utility function for UI rendering conditions.

##### Method: `add_section(self, section: str) -> None`
- **1. Purpose**: Adds an empty dictionary for a new top-level section.
- **2. Parameters**:
  - `section` (str): Section name.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Mutates `self.data`.
- **6. Dependencies**: None.
- **7. GUI Mapping**: None direct.

##### Method: `remove_section(self, section: str) -> None`
- **1. Purpose**: Deletes a top-level section.
- **2. Parameters**:
  - `section` (str): Section name.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Mutates `self.data`.
- **6. Dependencies**: None.
- **7. GUI Mapping**: None direct.

##### Method: `has_option(self, section: str, option: str) -> bool`
- **1. Purpose**: Checks if an option exists within a dictionary section.
- **2. Parameters**:
  - `section` (str): Section name.
  - `option` (str): Key inside the section.
- **3. Return Value**:
  - (bool): True if present.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Utility function.

##### Method: `remove_option(self, section: str, option: str) -> None`
- **1. Purpose**: Deletes a specific option from a section.
- **2. Parameters**:
  - `section` (str): Section name.
  - `option` (str): Option key.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Mutates `self.data`.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Utility function (e.g. unbinding a button).

##### Method: `get(self, section: str, option: str, fallback: Optional[str] = None) -> Optional[str]`
- **1. Purpose**: Retrieves a string value for an option in a section.
- **2. Parameters**:
  - `section` (str): Section name.
  - `option` (str): Option key.
  - `fallback` (Optional[str], default=None): Fallback value.
- **3. Return Value**:
  - (Optional[str]): Stringified value or fallback.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: General getter for fetching values to populate UI inputs.

##### Method: `getboolean(self, section: str, option: str, fallback: Optional[bool] = None) -> Optional[bool]`
- **1. Purpose**: Retrieves a boolean value, parsing strings like 'true', 'yes', 'on', '1'.
- **2. Parameters**:
  - `section`, `option`: Key path.
  - `fallback` (Optional[bool]): Fallback.
- **3. Return Value**:
  - (Optional[bool]): Parsed boolean or fallback.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: `self.get`.
- **7. GUI Mapping**: Used for Checkboxes and Toggle Switches in the GUI.

##### Method: `getfloat(self, section: str, option: str, fallback: Optional[float] = None) -> Optional[float]`
- **1. Purpose**: Retrieves a parsed float value.
- **2. Parameters**:
  - `section`, `option`: Key path.
  - `fallback` (Optional[float]): Fallback.
- **3. Return Value**:
  - (Optional[float]): Parsed float or fallback.
- **4. Exceptions/Errors**: Catches `ValueError` internally and returns fallback.
- **5. Side Effects**: None.
- **6. Dependencies**: `self.get`.
- **7. GUI Mapping**: Used for Slider numerical values (deadzones, curves).

##### Method: `set(self, section: str, option: str, value: Any) -> None`
- **1. Purpose**: Sets a value (converted to string) in a section, creating the section if needed.
- **2. Parameters**:
  - `section` (str): Section name.
  - `option` (str): Option key.
  - `value` (Any): Value to set. Will be cast to string.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Mutates `self.data`.
- **6. Dependencies**: None.
- **7. GUI Mapping**: General setter when UI inputs are modified.

##### Method: `items(self, section: str) -> List[Tuple[str, Any]]`
- **1. Purpose**: Returns all key-value pairs in a section.
- **2. Parameters**:
  - `section` (str): Section name.
- **3. Return Value**:
  - (List[Tuple[str, Any]]): List of tuples containing key and value. Empty list if section missing.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Useful for iterating over all mappings or checkboxes in a category.

##### Method: `options(self, section: str) -> List[str]`
- **1. Purpose**: Returns all keys in a section.
- **2. Parameters**:
  - `section` (str): Section name.
- **3. Return Value**:
  - (List[str]): List of keys. Empty list if section missing.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Utility function.

---

### MODULE: math_utils.py
**Filepath**: `src/math_utils.py`

#### Function: `process_analog_stick(x: float, y: float, inner_dz: float, anti_dz: float, curve_type: str, power: float, rest_dz: float = 0.0, sensitivity: float = 1.0, custom_eq: str = "") -> Tuple[float, float]`
- **1. Purpose**: Processes raw X/Y analog coordinates applying inner radial deadzone, rest deadzone, response curves, anti-deadzone, and sensitivity.
- **2. Parameters**:
  - `x`, `y` (float): Raw input coordinates in [-1.0, 1.0].
  - `inner_dz` (float): Inner deadzone radius [0.0, 1.0].
  - `anti_dz` (float): Anti-deadzone offset [0.0, 1.0].
  - `curve_type` (str): The response curve identifier.
  - `power` (float): The curve power variable >= 0.
  - `rest_dz` (float, default=0.0): Secondary deadzone buffer [0.0, 1.0].
  - `sensitivity` (float, default=1.0): Multiplier applied at the end.
  - `custom_eq` (str, default=""): Custom equation string for 'custom' or 'dotted' curves.
- **3. Return Value**:
  - (Tuple[float, float]): The processed (X, Y) coordinates in range [-1.0*sensitivity, 1.0*sensitivity].
- **4. Exceptions/Errors**: Safe from division by zero.
- **5. Side Effects**: None.
- **6. Dependencies**: `math.sqrt`, `curves.evaluate_curve`.
- **7. GUI Mapping**: Executed by the backend loop. Configured via the GUI Stick/Deadzone panels.

#### Function: `process_trigger(val: float, inner_dz: float, anti_dz: float, curve_type: str, power: float, rest_dz: float = 0.0, sensitivity: float = 1.0, custom_eq: str = "") -> float`
- **1. Purpose**: Processes 1D analog trigger value applying inner deadzone, rest deadzone, curves, anti-deadzone, and sensitivity.
- **2. Parameters**:
  - `val` (float): Raw trigger input [0.0, 1.0].
  - (other params identical in function to `process_analog_stick`).
- **3. Return Value**:
  - (float): Processed trigger value clamped strictly to [0.0, 1.0]. (Note: sensitivity multiplier is clamped).
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: `curves.evaluate_curve`.
- **7. GUI Mapping**: Configured via GUI Trigger panels.

#### Function: `apply_circularity_correction(x: float, y: float, center_x: float, center_y: float, bounds_data: List[float]) -> Tuple[float, float]`
- **1. Purpose**: Stretches analog stick values radially based on empirical bounds calibration data to enforce perfect circularity.
- **2. Parameters**:
  - `x`, `y` (float): Raw stick coords.
  - `center_x`, `center_y` (float): Center offsets.
  - `bounds_data` (List[float]): Exactly 360 float max radius measurements per degree.
- **3. Return Value**:
  - (Tuple[float, float]): The scaled X and Y coordinates.
- **4. Exceptions/Errors**: None. Returns raw X/Y if `bounds_data` is invalid.
- **5. Side Effects**: None.
- **6. Dependencies**: `math.sqrt`, `math.degrees`, `math.atan2`.
- **7. GUI Mapping**: Controlled by Calibration Wizard bounds.

#### Function: `calculate_circularity_error(bounds_data: List[float]) -> float`
- **1. Purpose**: Calculates the average percentage deviation from a perfect circle (radius 1.0).
- **2. Parameters**:
  - `bounds_data` (List[float]): 360 float radii.
- **3. Return Value**:
  - (float): The error percentage.
- **4. Exceptions/Errors**: Returns 0.0 on empty data.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Displayed as text output in the Calibration UI summary screen.

#### Function: `_scale_warped_axis(val: float, o_max: float) -> float`
- **1. Purpose**: Helper module function to scale a 1D axis value against a warped outer bound threshold.
- **2. Parameters**:
  - `val` (float): Stick value.
  - `o_max` (float): Outer bound threshold.
- **3. Return Value**:
  - (float): Scaled and clamped value.
- **4. Exceptions/Errors**: Safe.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: None (internal).

#### Function: `apply_warped_stick_correction(x: float, y: float, threshold_pct: float) -> Tuple[float, float]`
- **1. Purpose**: Dynamically scales outputs on asymmetric direction axes to hit 1.0 without hard-clipping bounds based on a user threshold.
- **2. Parameters**:
  - `x`, `y` (float): Stick inputs.
  - `threshold_pct` (float): User configurable percentage deviation threshold.
- **3. Return Value**:
  - (Tuple[float, float]): Adjusted X and Y coords.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: `_scale_warped_axis`.
- **7. GUI Mapping**: Configured via Advanced/Calibration stick panel (Outer threshold setting).

#### Function: `clamp_int(val: int, min_val: int, max_val: int) -> int`
- **1. Purpose**: Enforces min/max boundaries on an integer value.
- **2. Parameters**:
  - `val` (int): Target integer.
  - `min_val` (int): Lower bound.
  - `max_val` (int): Upper bound.
- **3. Return Value**:
  - (int): The clamped integer.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Generic utility.

---

### MODULE: curves.py
**Filepath**: `src/curves.py`

#### Global Variable: `_SAFE_MATH_DICT`
- Dictionary of safe Python `math` module functions pre-cached for `eval()` sandbox.

#### Function: `evaluate_curve(x: float, curve_type: str, power: float, custom_eq: str = "") -> float`
- **1. Purpose**: Computes a new mapped value from a normalized [0.0, 1.0] input based on mathematically defined response curve shapes.
- **2. Parameters**:
  - `x` (float): Input value [0.0, 1.0].
  - `curve_type` (str): Identifier ('linear', 'custom', 'exponential', 'relaxed', 'aggressive', 'cubic', 'sigmoid', 'bezier', 'dotted').
  - `power` (float): Primary adjustment variable dictating slope/intensity.
  - `custom_eq` (str): Equation string for 'custom' eval or JSON string of points for 'dotted'.
- **3. Return Value**:
  - (float): Output value [0.0, 1.0] representing the curved output.
- **4. Exceptions/Errors**: Catches errors in `eval` (custom mode) and JSON parsing (dotted mode), returning input `x` on failure.
- **5. Side Effects**: None.
- **6. Dependencies**: `math`, `json.loads`, `eval`.
- **7. GUI Mapping**: Governs the visual output plot and actual stick output. Selected via Curve dropdown.

#### Function: `export_to_desmos(curve_type: str, power: float, inner_dz: float, anti_dz: float, rest_dz: float) -> List[str]`
- **1. Purpose**: Generates a list of LaTeX strings mathematically describing the curve logic.
- **2. Parameters**: All relevant stick parameters (str/floats).
- **3. Return Value**:
  - (List[str]): Array of LaTeX math equations representing the curve and final output algorithm.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Used by the UI's LaTeX renderer (or link-out) to show users the exact mathematical function active.

#### Function: `export_to_latex(curve_type: str, power: float, inner_dz: float, anti_dz: float, rest_dz: float) -> str`
- **1. Purpose**: Combines Desmos strings into a single multi-line LaTeX block.
- **2. Parameters**: Same as above.
- **3. Return Value**:
  - (str): Newline separated LaTeX strings.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: None.
- **6. Dependencies**: `export_to_desmos`.
- **7. GUI Mapping**: Feeds direct LaTeX string to GUI equation renderer.

---

### MODULE: logger_setup.py
**Filepath**: `src/logger_setup.py`

#### Function: `setup_logger(name: str, log_file: str, is_debug: bool, append: bool = False) -> logging.Logger`
- **1. Purpose**: Instantiates and configures a Python standard `logging.Logger` with a file handler and standardized formatter. Prevents duplicate handlers.
- **2. Parameters**:
  - `name` (str): Internal module logger name.
  - `log_file` (str): Path to write the log text file.
  - `is_debug` (bool): Toggles DEBUG vs INFO level verbosity.
  - `append` (bool, default=False): If True, appends to file. If False, overwrites ('w').
- **3. Return Value**:
  - (logging.Logger): The fully configured logger object.
- **4. Exceptions/Errors**: Passes up filesystem/permission errors natively.
- **5. Side Effects**: Opens a file handle for writing on the disk.
- **6. Dependencies**: `logging`.
- **7. GUI Mapping**: Not visualized directly. Creates the `dinput_fix.log` user debugging files.

---

### MODULE: single_instance.py
**Filepath**: `src/single_instance.py`

#### Global Variable: `_instance_sockets`
- Dictionary holding socket references to prevent garbage collection closing the bind.

#### Function: `ensure_single_instance(app_name: str, port: int) -> socket.socket`
- **1. Purpose**: Ensures that only a single instance of the application script is active on the OS by binding to a local loopback TCP port. Kills the new process if lock fails.
- **2. Parameters**:
  - `app_name` (str): Label for console output logs.
  - `port` (int): Local TCP port number to lock.
- **3. Return Value**:
  - (socket.socket): The bound socket object instance.
- **4. Exceptions/Errors**: Catches `socket.error` and `OSError` to detect port conflicts.
- **5. Side Effects**: Calls `sys.exit(0)` killing the process if duplicate instance found. Binds network port if successful. Modifies global `_instance_sockets`.
- **6. Dependencies**: `socket`, `sys`.
- **7. GUI Mapping**: Prevents users from clicking the application shortcut multiple times causing device locking conflicts.

---

### MODULE: utilities_backend.py
**Filepath**: `src/utilities_backend.py`

#### Global Variable: `monitor`
- A global instance of `LatencyMonitor` used implicitly throughout the backend codebase to track performance.

#### Class: `LatencyMonitor`
**Description**: Measures polling rates and latency overhead of the backend input handling loop, and broadcasts this payload via UDP.

##### Method: `__init__(self, window_size: int = 100)`
- **1. Purpose**: Prepares ring buffers and the UDP socket for latency tracking.
- **2. Parameters**:
  - `window_size` (int, default=100): Size of `collections.deque` buffers for moving average calculation.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Opens an outbound UDP socket (unbound).
- **6. Dependencies**: `collections.deque`, `socket`.
- **7. GUI Mapping**: Initialized on backend start.

##### Method: `record_poll(self) -> float`
- **1. Purpose**: Marks a new input polling iteration tick and pushes delta time to the buffer.
- **2. Parameters**: None.
- **3. Return Value**:
  - (float): The current precise `time.perf_counter()` timestamp.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Mutates `poll_intervals` buffer. Updates `last_poll_time`.
- **6. Dependencies**: `time.perf_counter`.
- **7. GUI Mapping**: None direct.

##### Method: `record_process(self, start_time: float) -> None`
- **1. Purpose**: Measures the execution duration of a block of backend logic and saves to buffer.
- **2. Parameters**:
  - `start_time` (float): The starting timestamp returned from `record_poll()`.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Mutates `process_latencies` buffer.
- **6. Dependencies**: `time.perf_counter`.
- **7. GUI Mapping**: None direct.

##### Method: `broadcast_state(self, state: Any) -> None`
- **1. Purpose**: Serializes arbitrary state objects (dataclasses or object dicts) to JSON and fires it over UDP loopback to `127.0.0.1:9999`.
- **2. Parameters**:
  - `state` (Any): State payload to broadcast.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: Safely swallows all serialization and network exceptions.
- **5. Side Effects**: Emits network packets.
- **6. Dependencies**: `json.dumps`, `dataclasses.asdict`.
- **7. GUI Mapping**: Facilitates real-time 3D stick visualizers in the GUI without tying up IPC queues.

##### Method: `get_stats(self) -> Dict[str, float]`
- **1. Purpose**: Computes statistical summaries from the ring buffers (hz, averages, maximums).
- **2. Parameters**: None.
- **3. Return Value**:
  - (Dict[str, float]): Dictionary containing `polling_rate_hz`, `avg_process_ms`, `max_process_ms`.
- **4. Exceptions/Errors**: Protects against divide-by-zero. Returns 0 values if buffers empty.
- **5. Side Effects**: None.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Populates the debug stats text panel in the GUI bottom bar.

##### Method: `start_logging(self) -> None`
- **1. Purpose**: Spawns a background thread to dump rolling latency statistics to `diagnostics.json` every 0.5s.
- **2. Parameters**: None.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: Swallows file I/O exceptions in thread.
- **5. Side Effects**: Spawns a daemon thread. Writes files repeatedly to disk. Mutates `_logging_started` flag.
- **6. Dependencies**: `threading.Thread`, `json.dump`, `time.sleep`.
- **7. GUI Mapping**: Triggered by the "Start Diagnostics" toggle in UI.

##### Method: `stop_logging(self) -> None`
- **1. Purpose**: Flags the background thread to safely exit loop.
- **2. Parameters**: None.
- **3. Return Value**: None.
- **4. Exceptions/Errors**: None.
- **5. Side Effects**: Disables flag `_logging_started`. Thread will soon terminate.
- **6. Dependencies**: None.
- **7. GUI Mapping**: Triggered by disabling "Start Diagnostics" toggle.
