# Controller Calibration Guide

<div align="center">

[Overview](#overview) • [Device Selection & Setup](#device-selection--setup) • [Step-by-Step Profiling](#step-by-step-button--axis-profiling) • [Interactive Layout Builder](#interactive-layout-builder)

</div>

UR-XD uses custom JSON profile maps stored in `profiles/` to decode raw HID report packages into standardized virtual inputs. If you are using a new or unsupported controller, the interactive CLI calibration tool guides you through creating a profile in minutes.

## Overview

Unlike standard Windows utilities that blindly trust whatever garbage HID descriptors a hardware vendor programmed into their device's firmware, UR-XD directly reads raw payload bytes. Calibration establishes a precise baseline mapping between byte offsets and physical controls.

Run calibration anytime via:
```powershell
.\calibrate.bat
```
*(You can also double-click `tools_and_diagnostics.bat` and select Option 2).*

## Device Selection & Setup

When you start calibration, UR-XD initializes the input device scanner:

1. **Gamepad Selection Menu:**
   - UR-XD scans all connected USB and Bluetooth input devices and displays a numbered list.
   - If only one controller is connected on your system, UR-XD automatically selects it and skips the manual menu.
2. **API Mode Selection:**
   - Choose between **DInput HID Mode** (for DirectInput controllers with broken descriptors or missing analog triggers) and **XInput Mode**.
3. **Layout Template & Gyro Filter Prompts:**
   - Select your preferred button layout template (**Xbox**, **PlayStation**, or **Nintendo**). This layout is stored in the device profile to customize future visualizer prompts.
   - Indicate whether your controller streams continuous gyroscope/motion telemetry. If enabled, UR-XD activates a sensor filter to prevent gyro drift from interfering with button calibration.

## Step-by-Step Button Baselining

Once endpoints are selected, the CLI walks you through mapping each standard control:

1. **Button Prompts:** Press **A**, **B**, **X**, **Y**, **LB**, **RB**, **Back**, **Start**, **L3**, **R3**, **Guide/Home**, and extra paddles (**L4**, **R4**).
2. **Axis Baselining:** Push Left Stick Up, Left Stick Left, Right Stick Up, Right Stick Left.
3. **Trigger Calibration:** Squeeze Left Trigger fully, then Right Trigger.
4. **Interactive Controls:**
   - Press **`s`** on your keyboard to **Skip** a non-existent button.
   - Press **`u`** on your keyboard to **Undo** the previous step if you mispressed something.

Once complete, the profile is saved automatically to `profiles/<vendor_product_name>.json`.

## Interactive Layout Builder

If your controller layout in the GUI dashboard appears misaligned or overlapping, you can visually reposition button anchors:

```powershell
python technical-stuff/interactive_layout_builder.py
```

[screenshot of interactive layout builder tool][Snap-to-Grid Button Layout Builder]

- Switch between **Xbox**, **PlayStation**, or **Generic** layout templates.
- Adjust the **Grid Snap Slider** (5px to 20px) for automatic alignment.
- Drag button anchors visually and click **Save Layout** to update `resources/button_layout.json`.
