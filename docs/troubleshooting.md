# Comprehensive Troubleshooting Guide

<div align="center">

[Virtual Controller Issues](#no-virtual-controller-appears) • [Controller Detection](#controller-not-detected-by-the-wrapper) • [Double Inputs](#double-inputs-in-games) • [Calibration & Axis Quirks](#calibration--axis-quirks) • [GUI & Remapping Issues](#gui--remapping-issues) • [Rumble Limitations](#rumble--force-feedback-limitations) • [Diagnostic Suite](#automated-diagnostic-suite)

</div>


Got an issue? Don't panic. Controller drivers and Windows HID APIs are notoriously quirky. This guide covers common failure modes, driver quirks, user setup mistakes, and machine bullshit—along with exact solutions.

## Virtual Controller & Driver Issues (Machine Bullshit)

### No Virtual Controller Appears
- **Symptom:** You launched `run_wrapper.bat`, but games or Windows `joy.cpl` do not see a new "Xbox 360 Controller" or "Virtual Gamepad".
- **Cause:** The **ViGEmBus** (Virtual Gamepad Emulation Bus) driver is missing or failed to initialize.
- **Fix:**
  1. Download and install the latest **[ViGEmBus Driver Installer](https://github.com/nefarius/ViGEmBus/releases)**.
  2. Open Windows Device Manager (`devmgmt.msc`), expand **System devices**, and verify that **Virtual Gamepad Emulation Bus** is listed without any yellow exclamation mark.
  3. Restart `run_wrapper.bat`.

### Exclusive Interface Locks (Port-Locked Sockets / Steam Input)
- **Symptom:** The wrapper fails immediately upon launching or prints `PermissionError` / `Device locked`.
- **Cause:** Another application (such as Steam, DS4Windows, reWASD, or a browser with WebHID) opened an exclusive read/write lock on your physical controller's USB interface.
- **Fix:**
  1. Close Steam completely (or disable Steam Input for generic controllers in Steam Settings -> Controller).
  2. Close third-party remapping software.
  3. Relaunch `run_wrapper.bat` once the competing app is closed.

## Controller Detection Issues

### Controller Not Detected by the Wrapper
- **Symptom:** `run_wrapper.bat` says `No active profile found for device` or scans indefinitely.
- **Cause:** You are using a controller that does not have a pre-packaged profile in `profiles/` yet.
- **Fix:**
  1. Turn on your controller and run the guided calibration wizard:
     ```powershell
     .\calibrate.bat
     ```
  2. Complete the prompts to generate a profile JSON named after your hardware's Vendor ID (VID) and Product ID (PID).
  3. Relaunch `run_wrapper.bat`.

## Double Inputs in Games

### Physical Controller and Virtual Controller Both Sending Inputs
- **Symptom:** Pressing 'A' in game jumps twice, or opening a menu causes it to scroll two items at a time.
- **Cause:** The game is receiving inputs from BOTH your physical controller (DirectInput) and UR-XD's virtual controller (XInput) simultaneously.
- **Fix:**
  1. Verify **"Block XInput"** is checked in the GUI **Remapping** tab for remapped standard buttons. UR-XD automatically suppresses physical standard buttons from reaching the virtual pad when checked.
  2. If the game still reads the physical DInput controller directly, use **[HidHide](https://github.com/nefarius/HidHide)** to cloak the physical controller from all applications except UR-XD (`python main.py`).

## Calibration & Axis Quirks

### Calibration Fails Due to Dual-Axis Trigger Movement
- **Symptom:** Squeezing a single trigger during calibration causes the CLI tool to report movement on two separate axes simultaneously or misidentify the trigger axis.
- **Cause:** Hardware quirk present on cheap potentiometers or certain third-party microcontrollers where squeezing a trigger causes cross-talk voltage spikes on an unshielded thumbstick axis.
- **Fix:**
  1. UR-XD includes a multi-axis movement rejection heuristic (0.7 threshold) to filter out minor cross-talk.
  2. If cross-talk is severe, press **`s`** on your keyboard to **Skip** the trigger prompt during calibration, then manually edit the resulting profile JSON in `profiles/` to set the correct `byte` offset.

### Gyroscope / Motion Sensor Telemetry Noise
- **Symptom:** During calibration, the prompt advances automatically without pressing any buttons.
- **Cause:** Your controller streams continuous motion sensor telemetry (gyro/accelerometer) over HID reports, causing rolling byte changes that confuse calibration.
- **Fix:**
  1. When prompted during `calibrate.bat` setup ("Does your controller stream continuous gyroscope telemetry?"), select **Yes**.
  2. UR-XD will enable a sensor noise filter during button baselining.

## GUI & Remapping Issues

### GUI Changes Aren't Applying Live
- **Symptom:** You changed something in the GUI, but nothing changed in game.
- **Cause:** The background wrapper (`run_wrapper.bat`) is not running, or you forgot to click **Save Settings**.
- **Fix:**
  1. Ensure `run_wrapper.bat` is running in your system tray (look for the circular icon). The GUI only modifies `config.ini`; the wrapper applies the changes live.
  2. Click **Save Settings** in the GUI, if available. The wrapper reloads `config.ini` automatically within 5 seconds.

### Home / Guide Button Hold Turns Off Controller
- **Symptom:** Setting the **HOME** button as a Shift Layer modifier causes the controller to shut down after 3 seconds.
- **Cause:** Most wireless controllers have a hardware firmware timer that forces the controller to power off if the Home button is physically held down for 3+ seconds.
- **Fix:**
  1. Change the Shift Layer mode from **Hold** to **Toggle** mode in the Remapping tab.
  2. Use a different modifier button (such as `LB`, `RB`, or `Select`).

### Simulated Keyboard Keys Stuck Down
- **Symptom:** After running a macro or stopping the app, Windows acts as if the `SHIFT` or `CTRL` key is stuck down.
- **Cause:** An interrupted macro loop or unexpected process exit.
- **Fix:**
  1. UR-XD includes an **Active Key Tracking Matrix** that automatically broadcasts explicit `key_up` events upon loop completion or exit.
  2. If Windows gets stuck due to an outside event, tap the stuck key (`SHIFT`/`CTRL`) once on your physical keyboard to reset Windows state.

## Rumble / Force Feedback Limitations

### No Vibration in DirectInput (DInput) Mode
- **Symptom:** Haptic rumble works in native XInput mode, but when switching your controller hardware toggle to DInput mode, rumble ceases to work entirely.
- **Cause:** Extensive black-box reverse engineering revealed that third-party controller microcontrollers (such as 8BitDo Ultimate 2C) explicitly **firmware-gate** output reports outside of XInput mode. When set to DInput mode, the controller firmware ignores haptic motor packets entirely.
- **Fix:** This is a hardware/firmware restriction enforced by controller vendors. If vibration is essential, operate your controller in **XInput mode** using UR-XD's XInput backend (`backend_xinput.py`).

## Automated Diagnostic Suite

If you encounter an issue that isn't resolved by the solutions above, run the automated diagnostic suite:

```powershell
.\generate_issue_report.bat
```

[gif of generate_issue_report execution][Automated Diagnostics Running]

1. Launches 6 comprehensive automated scans inspecting Python environment, ViGEmBus status, installed packages, raw byte packets, exclusive locks, and endpoint topology.
2. Packages all logs into `issue_report.zip` in the root folder.
3. Attach `issue_report.zip` when [opening an issue on GitHub](https://github.com/jesga06/ultimate-2c-dinput-fix/issues).
