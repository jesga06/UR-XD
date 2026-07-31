# UR-XD GUI User Guide

<div align="center">

[Dashboard](#dashboard-tab) • [Remapping](#remapping-tab) • [Tuning & Deadzones](#tuning-tab) • [Circularity Calibrator](#circularity-calibrator) • [Macros Studio](#macros-studio-tab) • [Utilities & System Tray](#utilities--system-tray)

</div>

The UR-XD visual configuration utility features a modern interface for monitoring physical controller inputs, configuring button remapping, fine-tuning analog deadzones/curves, and recording macros—all applying instantly in real-time.

## Dashboard Tab

The **Dashboard** is your live input control room. It visualizes both physical inputs coming from your controller and virtual outputs sent to the virtual Xbox 360 controller.

[screenshot of Dashboard tab][Live Controller Visualizer and Output Monitor]

- **Live Controller Model:** Displays real-time button highlights, thumbstick positions, and analog trigger depths as you move your hardware controls.
- **Active Backend & Profile Status:** Shows current device profile (`profiles/*.json`), output mode (XInput/DInput), and connection state.
- **Selective Calibration:** Click **"🎯 Selective Calibration"** on the header card to launch targeted recalibration for specific buttons, thumbsticks, triggers, or custom back paddles without repeating full device setup.

## Remapping Tab

The **Remapping** tab allows you to assign any physical controller button (standard face buttons, shoulder bumpers, triggers, or back paddles like L4/R4) to any combination of keyboard, mouse, or virtual gamepad outputs.

[screenshot of Remapping tab][Button Mapping Interface with Key Combo Recorder]

### Features:
- **Interactive Recorder:** Click the **Record** button next to any input and press the physical keys on your keyboard/mouse to record bindings automatically.
- **Keyboard Combos:** Chain multiple keys together with `+` (e.g. `keyboard:ctrl+shift+esc` or `keyboard:f13`). Keys are pressed sequentially and released in reverse order.
- **Mouse Simulation:** Assign inputs to `mouse1` (Left Click), `mouse2` (Right Click), `mouse4` (X1 / Back), `mouse5` (X2 / Forward), or mouse wheel scrolls.
- **Dual XInput Blocking (`Blk` & `S.Blk`):** Toggle independent XInput suppression checkboxes for standard mappings (`Blk`) and shift layer mappings (`S.Blk`). When checked, UR-XD swallows the physical button input to prevent double-input issues in games while triggering remapped actions.
- **Shift Layer Remapping:** Configure alternate mapping profiles activated dynamically by holding down assigned modifier buttons.
  - **Layer Management:** Create, rename, delete, and switch between multiple custom shift layers with tab-based navigation.
  - **Activation Chords & 2-Key Priority:** Activate shift layers using a primary shift key (e.g. `[HOME]`) or a 2-key chord combination (e.g. `[HOME+RB]`). 2-key chord layers automatically take precedence over single-trigger layers when both keys are pressed simultaneously.

## Tuning Tab

Because not all thumbsticks and triggers are created equal (and factory calibration can drift), the **Tuning** tab gives you precise control over analog behavior.

[screenshot of Tuning tab][Thumbstick & Trigger Deadzone and Response Curve Tuning]

- **Inner & Outer Deadzones:** Eliminate stick drift by setting inner deadzones or expand maximum reach with outer deadzones.
- **Response Curves:** Toggle between **Linear**, **Aggressive** (S-curve), **Instant Response**, or **Smooth Precision** for stick sensitivity.
- **Trigger Trimming:** Fine-tune trigger min/max points so you reach 100% trigger pull effortlessly.

## Circularity Calibrator

Analogs on third-party gamepads are notorious for squarish boundary caps that cause diagonal acceleration spikes.

[screenshot of Circularity Calibrator][Interactive Circularity Calibrator]

- **Real-Time Sampling:** Rotate your analog sticks 360° inside the visual circle widget.
- **Cardinal & Diagonal Smoothing:** Automatically calculates math adjustments to map outer analog boundaries into a clean, smooth circle output.

## Macros Studio Tab

The **Macros Studio** enables recording complex automation sequences triggered by any controller button.

[screenshot of Macros tab][Macros Studio Recording & Sequence Editor]

- **Multi-Action Recording:** Record keypresses, delays, mouse clicks, and trigger pulls with millisecond precision.
- **Hold & Loop Modes:** Set macros to execute **On Press**, **While Held**, or **Toggle Loop**.
- **Anti-Stuck Safeguard:** Built-in emergency key-release logic guarantees keys are never left virtually "stuck down" if a macro execution is interrupted.

## Utilities & System Tray

- **Diagnostic Wizard:** Launch diagnostic scans directly from the GUI.
- **Live Reload:** Click **Save Settings** to write changes to `config.ini`. The background wrapper process picks up edits within 5 seconds without restarting!
- **System Tray Menu:** Right-click the system tray icon to access:
  - **Open Config:** Opens the GUI configuration interface.
  - **Pause Interception:** Temporarily passes physical inputs directly through to the virtual gamepad without applying remappings or button blocks.
  - **Reload Configuration:** Forces an immediate re-read of `config.ini` and `profiles/`.
  - **Show Console:** Brings the minimized wrapper console window to the front.
  - **Exit:** Safely destroys the virtual gamepad and shuts down the wrapper.