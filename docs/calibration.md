# Controller Calibration Guide

<div align="center">

[Overview](#overview) • [Stage 1: Auto-Detection](#stage-1-auto-detect-mode) • [Stage 2: Manual Endpoint Selection](#stage-2-manual-selection-mode) • [Button Mapping Steps](#step-by-step-button-baselining) • [Interactive Layout Builder](#interactive-layout-builder)

</div>

<br>

UR-XD uses custom JSON profile maps stored in `profiles/` to decode raw HID report packages into standardized virtual inputs. If you are using a new or unsupported controller, the interactive CLI calibration tool guides you through creating a profile in minutes.

---

## Overview

Unlike standard Windows tools that trust whatever garbage HID descriptors a controller vendor programmed into their device firmware, UR-XD directly reads raw byte payloads. Calibration establishes a baseline mapping between byte offsets and physical controls.

Run calibration anytime via:
```powershell
.\calibrate.bat
```

---

## Stage 1: Auto-Detect Mode

When you start calibration, UR-XD lists all detected HID hardware endpoints and enters a **15-Second Discovery Window**.

[gif of CLI stage 1 auto-detection][Auto-detecting Active Endpoint Telemetry in Real-time]

1. Press buttons, pull triggers, and rotate sticks on your physical controller.
2. UR-XD monitors byte changes across all active USB/Bluetooth endpoints.
3. If activity is detected, UR-XD automatically selects the active input endpoints and advances to layout configuration.

---

## Stage 2: Manual Selection Mode

Some controllers split their inputs across multiple HID interfaces (for example, sending main buttons on Interface 0 and extra paddle telemetry or motion gyro data on Interface 1).

If auto-detection does not pick up your inputs (or if you press **ENTER** without moving any controls to skip auto-detection), you enter **Manual Mode**:

```text
Available HID Endpoints:
[0] VID: 0x2DC8 PID: 0x3106 (Interface 0 - HID Gamepad)
[1] VID: 0x2DC8 PID: 0x3106 (Interface 1 - Custom Vendor Endpoint)

Enter target interface index/indices (e.g. 0 or 0,1):
```

Simply type `0` or `0,1` to combine telemetry across multiple endpoints!

---

## Step-by-Step Button Baselining

Once endpoints are selected, the CLI walks you through mapping each standard control:

1. **Button Prompts:** Press **A**, **B**, **X**, **Y**, **LB**, **RB**, **Back**, **Start**, **L3**, **R3**, **Guide/Home**, and extra paddles (**L4**, **R4**).
2. **Axis Baselining:** Push Left Stick Up, Left Stick Left, Right Stick Up, Right Stick Left.
3. **Trigger Calibration:** Squeeze Left Trigger fully, then Right Trigger.
4. **Interactive Controls:**
   - Press **`s`** on your keyboard to **Skip** a non-existent button.
   - Press **`u`** on your keyboard to **Undo** the previous step if you mispressed something.

Once finished, the profile JSON is formatted and saved automatically to `profiles/<vendor_product_name>.json`.

---

## Interactive Layout Builder

If your controller layout in the GUI dashboard appears misaligned or overlapping, you can interactively adjust button positions:

```powershell
python technical-stuff/interactive_layout_builder.py
```

[screenshot of interactive layout builder tool][Snap-to-Grid Button Layout Builder]

- Switch between **Xbox**, **PlayStation**, or **Generic** layout templates.
- Adjust the **Grid Snap Slider** (5px to 20px) for automatic alignment.
- Drag button anchors visually and click **Save Layout** to update `resources/button_layout.json`.
