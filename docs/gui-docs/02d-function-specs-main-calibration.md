# SECTION 2 PART D: EXHAUSTIVE FUNCTION SPECIFICATIONS

## MODULE: main.py (`src/main.py`)

**Globals:**
- `is_debug_mode` (bool): Defaults to `False`. Enables debug logging if true.
- `logger` (Logger|None): Global logging instance.
- `gui_processes` (list): Tracks launched GUI processes (via `subprocess.Popen`).

### 1. `hide_console()`
1. **Function Name & Signature**: `hide_console()`
2. **Purpose**: Hides the console window on Windows.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Calls Windows API to hide the console window.
6. **Exceptions / Error Handling**: Suppresses all exceptions internally.
7. **Implementation Details / Notes**: Uses `ctypes.windll.kernel32.GetConsoleWindow()` and `ctypes.windll.user32.ShowWindow(hwnd, 0)`.

### 2. `show_console()`
1. **Function Name & Signature**: `show_console()`
2. **Purpose**: Shows and restores the console window on Windows.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Calls Windows API to restore and bring the console to foreground.
6. **Exceptions / Error Handling**: Suppresses all exceptions internally.
7. **Implementation Details / Notes**: Uses `ctypes.windll.user32.ShowWindow(hwnd, 9)` and `SetForegroundWindow(hwnd)`.

### 3. `open_config(icon, item)`
1. **Function Name & Signature**: `open_config(icon, item)`
2. **Purpose**: Launches the GUI process (`gui.py`) from the system tray menu.
3. **Parameters**:
   - `icon`: pystray Icon instance.
   - `item`: pystray MenuItem instance.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Spawns a new process, appending it to the `gui_processes` list.
6. **Exceptions / Error Handling**: Catches all exceptions during subprocess launch and logs them via `logger.error` or `print`.
7. **Implementation Details / Notes**: Executes `sys.executable` on `gui.py` with `--append-log` and optionally `--debug` if `is_debug_mode` is True.

### 4. `show_console_action(icon, item)`
1. **Function Name & Signature**: `show_console_action(icon, item)`
2. **Purpose**: Callback for the system tray menu to show the console.
3. **Parameters**:
   - `icon`: pystray Icon instance.
   - `item`: pystray MenuItem instance.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Invokes `show_console()`.
6. **Exceptions / Error Handling**: None directly; relies on `show_console()` exception handling.
7. **Implementation Details / Notes**: Just a wrapper around `show_console`.

### 5. `write_status(state, device_name='None')`
1. **Function Name & Signature**: `write_status(state, device_name='None')`
2. **Purpose**: Writes the daemon status and connected device name to `status.json`.
3. **Parameters**:
   - `state` (str): Current status (e.g., "Connected", "Disconnected").
   - `device_name` (str): Name of the connected device.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Overwrites `status.json` in the working directory.
6. **Exceptions / Error Handling**: Catches IO exceptions and logs/prints them.
7. **Implementation Details / Notes**: Serializes a dict `{"status": state, "device": device_name}` to JSON.

### 6. `quit_app(icon, item)`
1. **Function Name & Signature**: `quit_app(icon, item)`
2. **Purpose**: Exits the wrapper application from the system tray menu.
3. **Parameters**:
   - `icon`: pystray Icon instance.
   - `item`: pystray MenuItem instance.
4. **Return Value**: None (never returns).
5. **Side Effects / Globals Modified**: Stops the system tray icon, writes "Disconnected" status, and calls `os._exit(0)`.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Hard exits using `os._exit(0)` to ensure all daemon threads are killed immediately.

### 7. `create_image()`
1. **Function Name & Signature**: `create_image()`
2. **Purpose**: Generates the icon image for the system tray.
3. **Parameters**: None.
4. **Return Value**: PIL `Image` object.
5. **Side Effects / Globals Modified**: None.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Draws a 64x64 RGBA icon using Pillow (`Image`, `ImageDraw`), drawing an ellipse and a rectangle.

### 8. `load_config(filename='config.ini')`
1. **Function Name & Signature**: `load_config(filename='config.ini')`
2. **Purpose**: Loads an INI configuration file.
3. **Parameters**:
   - `filename` (str): Path to the config file (defaults to `config.ini`).
4. **Return Value**: `configparser.ConfigParser` instance.
5. **Side Effects / Globals Modified**: Reads from the filesystem.
6. **Exceptions / Error Handling**: None explicitly; relies on `ConfigParser.read` internal handling for missing files.
7. **Implementation Details / Notes**: Returns an empty ConfigParser if the file does not exist.

### 9. `main()`
1. **Function Name & Signature**: `main()`
2. **Purpose**: The primary entry point for the wrapper daemon.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Modifies `is_debug_mode`, `logger`. Initializes multiple components, starts threads, and blocks on pystray icon run.
6. **Exceptions / Error Handling**: Catches component initialization failures and exits if critical components fail. Captures `KeyboardInterrupt` to shut down cleanly.
7. **Implementation Details / Notes**: Ensures single instance via socket. Parses arguments (`--debug`, `--boot`). Updates community databases. Initializes Backend (DInput/XInput), `Mapper`, `VirtualPad`, `HapticEngine`, `MacroExecutor`, `HardwareChordEngine`. Spawns `config_poller` and backend poll threads. Defines nested callbacks: `rumble_callback` and `data_handler`.

---

## MODULE: profile_tools.py (`src/profile_tools.py`)

### 1. `validate_hid_map(hid_map_path: str) -> str`
1. **Function Name & Signature**: `validate_hid_map(hid_map_path: str) -> str`
2. **Purpose**: Validates a HID map JSON file for structural correctness.
3. **Parameters**:
   - `hid_map_path` (str): File path to the HID map JSON.
4. **Return Value**: A string containing validation results (errors, warnings).
5. **Side Effects / Globals Modified**: None.
6. **Exceptions / Error Handling**: Returns a string describing an error if the file doesn't exist or JSON is invalid.
7. **Implementation Details / Notes**: Checks valid bytes, lengths (1-8), valid types ('button','axis','trigger','hat'), and overlapping bitmasks.

### 2. `diff_hid_maps(path1: str, path2: str) -> str`
1. **Function Name & Signature**: `diff_hid_maps(path1: str, path2: str) -> str`
2. **Purpose**: Compares two HID maps and reports structural differences.
3. **Parameters**:
   - `path1` (str): File path to first HID map.
   - `path2` (str): File path to second HID map.
4. **Return Value**: A string detailing the differences.
5. **Side Effects / Globals Modified**: None.
6. **Exceptions / Error Handling**: Returns an error string if files don't exist or JSON parsing fails.
7. **Implementation Details / Notes**: Compares reports, inputs, and individual input configurations (adds, removes, changes).

---

## MODULE: community_fetcher.py (`src/community_fetcher.py`)

**Constants:**
- `_RAW_BASE`: Base GitHub raw URL for the community map repo.
- `_DB_URL`: URL to fetch `database.json`.
- `_COMMUNITY_DIR`: Local path `'profiles/community'`.
- `_DB_LOCAL_PATH`: Local path `'profiles/community/database.json'`.

### 1. `_log(logger, level, msg)`
1. **Function Name & Signature**: `_log(logger, level, msg)`
2. **Purpose**: Helper to log messages using the provided logger or print to standard output.
3. **Parameters**:
   - `logger`: Logger instance (can be None).
   - `level` (str): Log level (e.g., 'info', 'error').
   - `msg` (str): Message to log.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: None.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Uses `getattr(logger, level)` if logger is provided.

### 2. `_ensure_dir()`
1. **Function Name & Signature**: `_ensure_dir()`
2. **Purpose**: Ensures the community profiles directory exists.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Creates directory if missing.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Uses `os.makedirs`.

### 3. `_download_raw(url, dest_path, timeout=10) -> bool`
1. **Function Name & Signature**: `_download_raw(url: str, dest_path: str, timeout: int = 10) -> bool`
2. **Purpose**: Downloads a file from a URL to a local destination.
3. **Parameters**:
   - `url` (str): Source URL.
   - `dest_path` (str): Local destination file path.
   - `timeout` (int): Connection timeout in seconds.
4. **Return Value**: `True` if successful.
5. **Side Effects / Globals Modified**: Writes file to disk.
6. **Exceptions / Error Handling**: Raises `RuntimeError` on failure.
7. **Implementation Details / Notes**: Uses `urllib.request`. User-Agent set to `UR-XD/1.0`.

### 4. `fetch_database(logger=None) -> dict`
1. **Function Name & Signature**: `fetch_database(logger=None) -> dict`
2. **Purpose**: Downloads and parses the community `database.json`.
3. **Parameters**:
   - `logger`: Optional logger.
4. **Return Value**: Parsed database as a Python dictionary.
5. **Side Effects / Globals Modified**: Modifies local `database.json`.
6. **Exceptions / Error Handling**: Can raise exceptions thrown by `_download_raw`.
7. **Implementation Details / Notes**: Refreshes the local database directly from `_DB_URL`.

### 5. `fetch_maps_for_devices(connected_vids_pids: list, logger=None) -> dict`
1. **Function Name & Signature**: `fetch_maps_for_devices(connected_vids_pids: list, logger=None) -> dict`
2. **Purpose**: Fetches specific community HID maps matching connected devices.
3. **Parameters**:
   - `connected_vids_pids` (list): List of tuples `(vid, pid)`.
   - `logger`: Optional logger.
4. **Return Value**: Dict mapping device names to local file paths for fetched maps.
5. **Side Effects / Globals Modified**: Downloads missing HID map files into community directory.
6. **Exceptions / Error Handling**: Catch and log exceptions per file download without stopping entirely.
7. **Implementation Details / Notes**: Compares provided VID/PIDs to aliases in `database.json`.

### 6. `fetch_community_hid_maps(logger=None) -> str`
1. **Function Name & Signature**: `fetch_community_hid_maps(logger=None) -> str`
2. **Purpose**: Top-level wrapper to update database and all maps for currently connected devices.
3. **Parameters**:
   - `logger`: Optional logger.
4. **Return Value**: Human-readable status string.
5. **Side Effects / Globals Modified**: See `fetch_database` and `fetch_maps_for_devices`.
6. **Exceptions / Error Handling**: Catch exceptions and return them in the status string.
7. **Implementation Details / Notes**: Typically called by the GUI 'Update Community HID Maps' button.

---

## MODULE: circularity_modal.py (`src/circularity_modal.py`)

### Class `CircularityCalibrationModal(ctk.CTkToplevel)`
State machine: REST -> WAIT_SWEEP -> SWEEP -> DONE. Runs an update loop at 60Hz.

#### 1. `__init__(self, parent, title, section, on_finish=None)`
1. **Function Name & Signature**: `__init__(self, parent, title, section, on_finish=None)`
2. **Purpose**: Initializes the calibration modal window.
3. **Parameters**:
   - `parent`: Parent window.
   - `title`: Modal title string.
   - `section`: Target config section.
   - `on_finish`: Callback on completion.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Creates UI elements.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Sets up a 360-element `bounds_data` list.

#### 2. `draw_grid(self)`
1. **Function Name & Signature**: `draw_grid(self)`
2. **Purpose**: Draws the background coordinate grid.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Modifies canvas content.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Draws center crosshairs and bounding circle.

#### 3. `get_raw_input(self)`
1. **Function Name & Signature**: `get_raw_input(self)`
2. **Purpose**: Retrieves live raw analog input.
3. **Parameters**: None.
4. **Return Value**: Tuple (x, y) representing stick position.
5. **Side Effects / Globals Modified**: None.
6. **Exceptions / Error Handling**: Returns `(0.0, 0.0)` if state is unavailable.
7. **Implementation Details / Notes**: Checks `self.parent.current_state`.

#### 4. `update_loop(self)`
1. **Function Name & Signature**: `update_loop(self)`
2. **Purpose**: Main 60Hz UI and data processing loop.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Updates state machine, samples data, modifies UI.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Runs via `self.after(16, ...)`.

#### 5. `draw_bounds(self)`
1. **Function Name & Signature**: `draw_bounds(self)`
2. **Purpose**: Renders the current bounding polygon for the sampled circularity.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Updates canvas `bounds` tag.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Converts polar to cartesian coordinates based on `bounds_data`.

#### 6. `start_sweep(self)`
1. **Function Name & Signature**: `start_sweep(self)`
2. **Purpose**: Transitions state to `SWEEP`.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Modifies `calib_state`.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Prepares system for 3x CW/CCW rotations.

#### 7. `interpolate_bounds(self)`
1. **Function Name & Signature**: `interpolate_bounds(self)`
2. **Purpose**: Interpolates zero values in the bounds array to fill gaps.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Alters `self.bounds_data`.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Uses angular distance ratio to linearly interpolate gap values.

#### 8. `finish_sweep(self)`
1. **Function Name & Signature**: `finish_sweep(self)`
2. **Purpose**: Finalizes calibration sweep and calculates error.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Transitions to `DONE` state. Updates UI labels.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Calls `math_utils.calculate_circularity_error`.

#### 9. `save_and_close(self)`
1. **Function Name & Signature**: `save_and_close(self)`
2. **Purpose**: Commits circularity data to config and closes modal.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Saves parent configuration to disk. Invokes `on_finish` callback. Destroys window.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Saves `circularity_bounds` and offset into config section. Auto-enables `circularity_mode` to `'before'` if previously disabled.

---

## MODULE: calibration.py (`src/calibration.py`)

### Helper Functions

#### 1. `cls()`
1. **Function Name & Signature**: `cls()`
2. **Purpose**: Clears terminal screen without flickering.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Manipulates `sys.stdout`.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Uses ANSI escape code `\033[H`.

#### 2. `select_stdin()`
1. **Function Name & Signature**: `select_stdin()`
2. **Purpose**: Stub helper used for flushing input.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: None.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Does practically nothing in implementation, placeholder.

### Class `Calibrator`

#### 1. `__init__(self)`
1. **Function Name & Signature**: `__init__(self)`
2. **Purpose**: Initializes Calibrator context.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Creates basic empty profile.
6. **Exceptions / Error Handling**: Suppresses config load failures.
7. **Implementation Details / Notes**: Checks config.ini to auto-determine last `layout`.

#### 2. `get_layout_labels(self)`
1. **Function Name & Signature**: `get_layout_labels(self)`
2. **Purpose**: Retrieves physical button label text mapping based on layout type.
3. **Parameters**: None.
4. **Return Value**: Dict mapping internal button identifiers to user-friendly strings.
5. **Side Effects / Globals Modified**: None.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Handles 'xbox', 'playstation', 'nintendo' layouts.

#### 3. `get_test_labels(self)`
1. **Function Name & Signature**: `get_test_labels(self)`
2. **Purpose**: Retrieves short-hand physical button labels for the test UI.
3. **Parameters**: None.
4. **Return Value**: Dict of shorthand button string names.
5. **Side Effects / Globals Modified**: None.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Similar to `get_layout_labels` but more compact text.

#### 4. `_data_handler(self, report: HIDReport)`
1. **Function Name & Signature**: `_data_handler(self, report: HIDReport)`
2. **Purpose**: Raw HID callback updating internal latest_reports state.
3. **Parameters**:
   - `report` (HIDReport): Received HID report data.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Updates `self.latest_reports`.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Extremely brief; meant to capture newest report per report_id.

#### 5. `scan_devices(self, test_only=False, skip_discovery=False)`
1. **Function Name & Signature**: `scan_devices(self, test_only=False, skip_discovery=False)`
2. **Purpose**: Scans system for devices and facilitates user selection/discovery.
3. **Parameters**:
   - `test_only` (bool): Skip calibration, just load device.
   - `skip_discovery` (bool): Skip the 15s discovery phase.
4. **Return Value**: `True` if successfully setup, `False` otherwise.
5. **Side Effects / Globals Modified**: Initializes `HIDReader` threads, configures `self.profile`, populates `self.readers`.
6. **Exceptions / Error Handling**: Catch and log HID connection failures.
7. **Implementation Details / Notes**: Handles interactive multi-device lists and a 15-second interface activity discovery window.

#### 6. `_wait_for_input(self, prompt, is_axis=False)`
1. **Function Name & Signature**: `_wait_for_input(self, prompt, is_axis=False)`
2. **Purpose**: Wait for user button input explicitly (Stub).
3. **Parameters**:
   - `prompt` (str): Output text string to prompt user.
   - `is_axis` (bool): If waiting for an analog axis move.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: None.
6. **Exceptions / Error Handling**: None.
7. **Implementation Details / Notes**: Noted as essentially an empty stub because inline polling handles logic instead.

#### 7. `setup_auto_detect(self)`
1. **Function Name & Signature**: `setup_auto_detect(self)`
2. **Purpose**: Automatically detects whether controller supports XInput.
3. **Parameters**: None.
4. **Return Value**: `True` if XInput is detected, `False` otherwise.
5. **Side Effects / Globals Modified**: Edits `config.ini` backend mode setting.
6. **Exceptions / Error Handling**: Handles XInput init failures.
7. **Implementation Details / Notes**: Uses `XInputBackend` polling to wait for A+B buttons simultaneously.

#### 8. `run(self, test_only=False)`
1. **Function Name & Signature**: `run(self, test_only=False)`
2. **Purpose**: Main entry point flow for CLI.
3. **Parameters**:
   - `test_only` (bool): If true, jumps straight to test mode.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Runs calibration loop, configures system config.
6. **Exceptions / Error Handling**: Ensures readers shut down cleanly using `finally`.
7. **Implementation Details / Notes**: Interactively prompts for layout selection and handles XInput vs DInput mode split.

#### 9. `_continue_dinput_calibration(self)`
1. **Function Name & Signature**: `_continue_dinput_calibration(self)`
2. **Purpose**: Executes DInput calibration after device discovery.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Runs calibration process.
6. **Exceptions / Error Handling**: Ensures readers shut down properly.
7. **Implementation Details / Notes**: Supports remapping specific inputs by mutating existing profile data instead of wiping it. Prompts for layout and gyro questions.

#### 10. `_calibrate_loop(self, remapping_targets=None)`
1. **Function Name & Signature**: `_calibrate_loop(self, remapping_targets=None)`
2. **Purpose**: Core data loop interacting with user to map physical actions to byte deltas.
3. **Parameters**:
   - `remapping_targets` (list): Specific input names to remap, if any.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Populates `self.profile["reports"]` with input definitions.
6. **Exceptions / Error Handling**: Uses `time.sleep` timeouts to avoid locking.
7. **Implementation Details / Notes**: Relies on diffing bytes against a moving baseline. Detects axes, hats, standard buttons, and analog triggers. Has advanced logic for filtering noise from gyro and noisy axes. Incorporates skip ('s') and undo ('u') functionality via non-blocking `msvcrt.kbhit()`.

#### 11. `save_profile(self)`
1. **Function Name & Signature**: `save_profile(self)`
2. **Purpose**: Persists the mapped profile to JSON.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Writes `profiles/{VID}_{PID}.json`.
6. **Exceptions / Error Handling**: Catches file saving errors and prints.
7. **Implementation Details / Notes**: Uses `json.dump`.

#### 12. `_calibrate_rumble(self)`
1. **Function Name & Signature**: `_calibrate_rumble(self)`
2. **Purpose**: Identifies heavy/light rumble motor bytes via manual iteration.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Mutates `self.profile["rumble"]`.
6. **Exceptions / Error Handling**: Skips on invalid hex inputs.
7. **Implementation Details / Notes**: Uses a base template payload and iterates bytes setting to 255 to ask the user which motor vibrates.

#### 13. `test_mode(self, is_temp=False, profile_path=None)`
1. **Function Name & Signature**: `test_mode(self, is_temp=False, profile_path=None)`
2. **Purpose**: Displays a live ASCII visualization of decoded HID inputs.
3. **Parameters**:
   - `is_temp` (bool): True if using a temporary profile file.
   - `profile_path` (str): Path to profile JSON.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Runs continuously until `Ctrl+C`. Modifies standard output repeatedly.
6. **Exceptions / Error Handling**: Traps `KeyboardInterrupt` to cleanly exit.
7. **Implementation Details / Notes**: Re-creates `Decoder` using the mapped profile, uses ANSI sequences to clear screen efficiently, drawing grids for axes at ~20 FPS.

#### 14. `dump_raw_mode(self)`
1. **Function Name & Signature**: `dump_raw_mode(self)`
2. **Purpose**: Continuously monitors and prints raw byte deltas on all active interfaces.
3. **Parameters**: None.
4. **Return Value**: None.
5. **Side Effects / Globals Modified**: Continuously prints to standard out.
6. **Exceptions / Error Handling**: Stops via `KeyboardInterrupt`. Stops readers properly on exit.
7. **Implementation Details / Notes**: Bypasses the mapping engine, intended purely for reverse-engineering unknown controller payloads.
