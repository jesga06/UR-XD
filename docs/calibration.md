# Controller Calibration Guide

<div align="center">

[Overview](#overview) • [Native GUI Wizard](#native-gui-calibration-wizard) • [Selective Input Calibration](#selective-input-calibration) • [Step-by-Step Profiling](#step-by-step-button--axis-profiling) • [CLI Fallback](#cli-calibration-fallback)

</div>

<br>

UR-XD uses custom profile files stored in `profiles/` to translate raw controller signals into virtual gamepad inputs. If you connect an unprofiled controller, UR-XD launches an interactive calibration wizard to create a precise device profile in minutes.

## Overview

Unlike standard Windows utilities that blindly trust whatever HID descriptors a hardware vendor programmed into their device's firmware, UR-XD directly reads raw payload bytes. Calibration establishes a precise baseline mapping between byte offsets and physical controls.

Calibration can be launched directly from the **Dashboard Tab** in the GUI or executed via CLI scripts.

## Native GUI Calibration Wizard

When launching UR-XD with a newly connected or unprofiled gamepad, the **Profile Decision Engine** automatically presents the native PySide6 Calibration Wizard dialog. You can also trigger full calibration manually at any time by clicking **"Calibrate Controller"** on the GUI Dashboard.

1. **Device Selection & API Mode:**
   - UR-XD enumerates connected USB HID interfaces automatically. Scroll down the list and select your device.
2. **Visual Layout Selection:**
   - Choose your preferred button layout template (**Xbox**, **PlayStation**, or **Nintendo**). This preference is saved to your profile to customize visualizer prompts throughout the application.

## Selective Input Calibration

If only a specific control (such as a thumbstick, trigger, D-Pad, or back paddle) needs recalibration, you do not need to repeat the full calibration process.

1. Click **"🎯 Selective Calibration"** on the Dashboard header card.
2. Select the specific buttons, axes, or D-Pad controls you wish to re-map, or type custom extra button names (e.g. `C`, `Z`, `P1`, `P2`) on the fly.
3. The wizard runs a quick 2-second rest baseline capture, prompts only for your selected controls, and safely merges updated mappings directly into your existing profile JSON without disturbing other inputs.

## Step-by-Step Button & Axis Profiling

Whether running full or selective calibration, the wizard guides you through each target input:

1. **Button Prompts:** Press standard face buttons, shoulder bumpers, stick clicks (`L3`/`R3`), and extra paddles (**L4**, **R4**). When an input registers, release it when prompted to allow rest state settling.
2. **Axis Baselining:** Push Left Stick Up, Left Stick Left, Right Stick Up, and Right Stick Left, followed by real-time interactive stick radar verification.
3. **Trigger Calibration:** Squeeze Left Trigger and Right Trigger fully.
4. **Navigation Controls:**
   - Click **Skip** (or press **`s`** in CLI) to bypass non-existent physical controls.
   - Click **Undo** (or press **`u`** in CLI) to step backward if an input was pressed by mistake.

Once complete, the profile is saved automatically to `profiles/<VID>_<PID>.json`.

## CLI Calibration Fallback

If running without a graphical interface or in debug environments, launch calibration anytime via:

```powershell
.\calibrate.bat
```
*(You can also double-click `tools_and_diagnostics.bat` and select Option 3).*

