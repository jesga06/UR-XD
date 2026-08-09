# Comprehensive Troubleshooting Guide

<div align="center">

[Virtual Controller Issues](#no-virtual-controller-appears) • [Controller Detection](#controller-not-detected-by-the-wrapper) • [Double Inputs](#double-inputs-in-games) • [Calibration & Axis Quirks](#pulling-a-trigger-moves-thumbsticks-during-calibration) • [GUI & Remapping Issues](#gui--remapping-issues) • [Rumble Limitations](#no-vibration-in-directinput-dinput-mode) • [Diagnostic Suite](#automated-diagnostic-suite)

</div>

<br>

Got an issue? Don't panic. Controller drivers on Windows can be notoriously finicky. This guide covers common issues, setup mistakes, and weird hardware quirks—along with easy, step-by-step solutions.

## Virtual Controller & Driver Issues

### No Virtual Controller Appears
- **Symptom:** You launched `run_wrapper.bat`, but games or Windows (`joy.cpl`) do not see a new "Xbox 360 Controller" or "Virtual Gamepad".
- **Cause:** The **ViGEmBus** driver (the component that creates virtual Xbox controllers) is missing or failed to start.
- **Fix:**
  1. Download and install the latest **[ViGEmBus Driver Installer](https://github.com/nefarius/ViGEmBus/releases)**.
  2. Open Windows Device Manager (`devmgmt.msc`), expand **System devices**, and verify that **Virtual Gamepad Emulation Bus** is listed without any yellow warning icon.
  3. Restart `run_wrapper.bat`.

### Other Apps Blocking the Controller (Steam or Background Remappers)
- **Symptom:** The wrapper fails immediately upon launching or prints `PermissionError` / `Device locked`.
- **Cause:** Another program running on your computer (such as Steam, DS4Windows, reWASD, or a web browser) has grabbed full control of your controller, blocking UR-XD from reading its buttons.
- **Fix:**
  1. Close Steam completely (or disable Steam Input for generic controllers in Steam Settings -> Controller).
  2. Close any third-party remapping software.
  3. Relaunch `run_wrapper.bat` once the competing app is closed.

## Controller Detection Issues

### Controller Not Detected by the Wrapper
- **Symptom:** `run_wrapper.bat` says `No active profile found for device` or scans indefinitely.
- **Cause:** You are using a controller that does not have a pre-packaged file in `profiles/` yet.
- **Fix:**
  1. Turn on your controller and run the guided calibration wizard:
     ```powershell
     .\calibrate.bat
     ```
  2. Follow the prompts to create a profile file for your specific controller model.
  3. Relaunch `run_wrapper.bat`.

## Double Inputs in Games

### Physical Controller and Virtual Controller Both Sending Inputs
- **Symptom:** Pressing 'A' in a game jumps twice, or opening a menu causes it to scroll two items at once.
- **Cause:** The game is receiving inputs from BOTH your physical controller and UR-XD's virtual controller at the same time.
- **Fix:**
  1. Verify **"Block XInput"** is checked in the GUI **Remapping** tab for remapped buttons. UR-XD automatically blocks physical buttons from reaching the virtual controller when checked.
  2. Install **[HidHide](https://github.com/nefarius/HidHide)**. UR-XD automatically detects HidHide, whitelists itself (`python.exe`), cloaks your physical gamepad on connect, and uncloaks it on exit.
  3. Run `diagnostics/07_hidhide_audit.py` to verify your local HidHide driver installation, process elevation status, and device instance path resolution.

## Calibration & Axis Quirks

### Pulling a Trigger Moves Thumbsticks During Calibration
- **Symptom:** Squeezing a trigger during calibration causes the tool to report thumbstick movement or misidentify the trigger.
- **Cause:** On some controllers, pulling a trigger causes minor electrical interference that makes an analog stick wiggle slightly at the same time.
- **Fix:**
  1. UR-XD automatically filters out minor stick wiggles during calibration.
  2. If the interference is severe, press **s** on your keyboard to **Skip** the trigger step during calibration. You can then open your controller's file in `profiles/` and adjust the trigger line manually.

### Calibration Advances Automatically Without Pressing Buttons
- **Symptom:** During calibration, the prompts advance by themselves without you touching anything.
- **Cause:** Your controller has built-in motion sensors (gyroscope/accelerometer) that constantly send movement data to Windows, making the calibration tool think you are pressing buttons.
- **Fix:**
  1. When prompted during `calibrate.bat` setup ("Does your controller stream continuous gyroscope telemetry?"), select **Yes**.
  2. UR-XD will turn on a motion filter to ignore sensor drift during calibration.

## GUI & Remapping Issues

### GUI Changes Aren't Applying Live
- **Symptom:** You changed something in the GUI, but nothing changed in your game.
- **Cause:** The background wrapper (`run_wrapper.bat`) is not running, or you forgot to click **Save Settings**.
- **Fix:**
  1. Ensure `run_wrapper.bat` is running in your system tray (look for the circular icon). The GUI only modifies settings; the wrapper process applies them live.
  2. Click **Save Settings** in the GUI. The wrapper reloads your changes automatically within 5 seconds.

### Home / Guide Button Hold Turns Off Controller
- **Symptom:** Setting the **HOME** button as a Shift Layer modifier causes the controller to shut down after 3 seconds.
- **Cause:** Most wireless controllers have a built-in hardware shortcut that turns the controller off if the Home button is held down for 3 seconds.
- **Fix:**
  1. Change the Shift Layer mode from **Hold** to **Toggle** mode in the Remapping tab.
  2. Use a different modifier button (such as `LB`, `RB`, or `Select`).

### Keyboard Keys Stuck Down After a Macro
- **Symptom:** After running a macro or stopping the app, Windows acts as if the `SHIFT` or `CTRL` key is stuck down.
- **Cause:** A macro was interrupted before it could send the key release signal.
- **Fix:**
  1. UR-XD automatically releases all simulated keys whenever a macro finishes or the app closes.
  2. If Windows gets stuck due to an outside event, tap the stuck key (`SHIFT` or `CTRL`) once on your physical keyboard to reset it.

## Rumble / Force Feedback Limitations

### No Vibration in DirectInput (DInput) Mode
- **Symptom:** Vibration works when your controller is set to XInput mode, but stops completely when switched to DInput mode.
- **Cause:** Testing revealed that controller hardware manufacturers explicitly turn off vibration motors inside the controller whenever it is switched to DirectInput mode. The controller's internal software ignores vibration commands completely when not in XInput mode.
- **Fix:** This is a hardware limitation built into the controller itself. If you need rumble, switch your controller to **XInput mode** before playing.

## Automated Diagnostic Suite

If you encounter an issue that isn't resolved by the solutions above, run the automated diagnostic tool:

```powershell
.\generate_issue_report.bat
```

[gif of generate_issue_report execution][Automated Diagnostics Running]

1. Runs 6 automated checks to test your drivers, Python setup, controller connection, and system settings.
2. Packages all logs into a single file named `issue_report.zip` in the main folder.
3. Attach `issue_report.zip` when [opening an issue on GitHub](https://github.com/jesga06/ultimate-2c-dinput-fix/issues).
