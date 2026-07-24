# Comprehensive Troubleshooting Guide

<div align="center">

[Virtual Controller Issues](#no-virtual-controller-appears) • [Double Inputs](#double-inputs-in-games) • [Rumble Limitations](#rumble-force-feedback-issues) • [Diagnostic Suite](#automated-diagnostic-suite)

</div>

<br>

Got an issue? Don't panic. Controller drivers on Windows are notoriously quirky. This guide covers common solutions and automated issue reporting.

---

## Common Issues & Solutions

### No Virtual Controller Appears
1. Ensure the **[ViGEmBus](https://github.com/nefarius/ViGEmBus/releases)** driver is installed.
2. Open Windows Device Manager and check under **System devices** for **Virtual Gamepad Emulation Bus**.
3. If ViGEmBus is installed but no virtual Xbox controller appears, restart the daemon (`.\run_wrapper.bat`).

### Controller Not Detected by UR-XD
1. Verify your physical controller is connected and visible in Windows `joy.cpl`.
2. Ensure you have calibrated your controller first (`.\calibrate.bat`) so a profile exists in `profiles/`.

### Double Inputs in Games
1. When you remap a standard gamepad button (like 'A'), UR-XD blocks the physical 'A' button from reaching the virtual controller.
2. If games are still seeing double inputs, verify that **Steam Input** is disabled for your controller or configure **HidHide** to hide the physical DirectInput controller from games.

### GUI Changes Aren't Applying
1. Ensure `run_wrapper.bat` (the background daemon) is actively running in your system tray. The GUI only modifies `config.ini`; the daemon applies changes live.

---

## Rumble / Force Feedback Issues

> ⚠️ **IMPORTANT NOTICE:** Force feedback (rumble) is **not supported in DirectInput (DInput) mode** and likely never will be.

Extensive black-box reverse engineering revealed that 8BitDo and other third-party controller microcontrollers explicitly firmware-gate rumble output reports outside of XInput mode. When running in DInput mode, the controller firmware ignores haptic motor packets entirely.

If rumble is critical for your gameplay, switch your hardware toggle to **XInput mode**.

---

## Automated Diagnostic Suite

If you encounter an issue that isn't resolved by the steps above, run the built-in 6-step diagnostic suite:

```powershell
.\generate_issue_report.bat
```

[screenshot of generate_issue_report execution][Diagnostic Suite Running Automated System & HID Scans]

1. Performs environment analysis (Python version, ViGEmBus status, installed packages).
2. Scans raw HID byte report packages.
3. Tests exclusive device locks and endpoint topologies.
4. Automatically packages logs into `issue_report.zip` in the repository root.
5. Attach `issue_report.zip` when [opening a GitHub Issue](https://github.com/jesga06/ultimate-2c-dinput-fix/issues).
