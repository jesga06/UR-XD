# Ultimate 2C DInput Fix — Comprehensive GUI Visual Blueprint & Mockups Archive

> [!NOTE]
> This document archives **every visual plan, UI layout mockup, design specification, color token, and visual change** conceptualized and refined during the GUI design iterations. Feature code is omitted—this serves as a definitive visual reference blueprint for future GUI development.

---

## 🎨 1. Core Visual Design System ("Built Tomorrow")

### Visual Aesthetic & Glassmorphism Tokens
* **Color Palette & Theme Architecture**:
  * **Deep Space Background**: `#0c0914` (Ultra-dark background to maximize card contrast).
  * **Glassmorphism Container Cards**: Semi-transparent `#161024` base with 85% opacity (`rgba(22, 16, 36, 0.85)`).
  * **Card Borders**: 1px thin glowing outlines (`rgba(168, 85, 247, 0.35)` base, `#a855f7` on focus/hover).
  * **Typography**: `Outfit` / `Inter` variable fonts for UI elements; monospaced `JetBrains Mono` / `Fira Code` for telemetry and log streams.
  * **Mandatory High-Contrast Text Box Outlines**: 1.5px solid neon accent border (`#a855f7`) around all typable text fields (`QLineEdit`, `QSpinBox`, `QComboBox`) to prevent blending into the window background, with italicized semi-transparent placeholders (`rgba(255, 255, 255, 0.6)`).

### 7 Theme Color Presets (QSS Palette Tokens)
1. **Purple (Default)**: Primary `#7500ab`, Glow `#a855f7`, Accent Green `#00f5a0`
2. **Ocean Blue**: Primary `#0284c7`, Glow `#38bdf8`, Base `#08101e`
3. **Cyber Green**: Primary `#16a34a`, Glow `#4ade80`, Base `#08140c`
4. **Crimson Red**: Primary `#dc2626`, Glow `#f87171`, Base `#140809`
5. **Solar Yellow**: Primary `#ca8a04`, Glow `#facc15`, Base `#141208`
6. **Neon Orange**: Primary `#ea580c`, Glow `#fb923c`, Base `#140c08`
7. **Monochrome Light Dark (White)**: Primary `#64748b`, Glow `#e2e8f0`, Base `#111318`

---

## 📐 2. Visual Layout Mockups by Tab

### Tab 1: Dashboard View

```
+-------------------------------------------------------------------------------------------------------------------+
|  [● ONLINE] 8BitDo Ultimate 2C (DInput)                                                                           |
+-------------------------------------------------------------------------------------------------------------------+
|                                                                                                                   |
|  +---------------------------------------+     +---------------------------------------+                          |
|  | LEFT STICK RADAR                      |     | RIGHT STICK RADAR                     |                          |
|  |  .---------------------------------.  |     |  .---------------------------------.  |                          |
|  |  |                |                |  |     |  |                |                |  |                          |
|  |  |           .----+----.           |  |     |  |           .----+----.           |  |                          |
|  |  |          /  DZ |     \          |  |     |  |          /  DZ |     \          |  |                          |
|  |  |---------+--(●)-+--●--+----------|  |     |  |---------+--(●)-+--------|  |                          |
|  |  |          \     |     /          |  |     |  |          \     |     /          |  |                          |
|  |  |           '----+----'           |  |     |  |           '----+----'           |  |                          |
|  |  |                |                |  |     |  |                |                |  |                          |
|  |  '---------------------------------'  |     |  '---------------------------------'  |                          |
|  | Raw: (-0.02, +0.01) | Tuned: (+0.12)  |     | Raw: (+0.00, -0.00) | Tuned: (+0.00)  |                          |
|  +---------------------------------------+     +---------------------------------------+                          |
|                                                                                                                   |
|  +-------------------------------------------------------------------------------------------------------------+  |
|  | ANALOG TRIGGERS                                                                                             |  |
|  | LT [████████████████░░░░░░░░] 74.2%                 RT [████████████████████████] 100.0%                    |  |
|  +-------------------------------------------------------------------------------------------------------------+  |
|                                                                                                                   |
|  +-------------------------------------------------------------------------------------------------------------+  |
|  | CONTROLLER BUTTON STATUS INDICATORS                                                                         |  |
|  | [ LT ]  [ RT ]  [ LB ]  [ RB ]  [ DPAD_UP ]  [ DPAD_DOWN ]  [ DPAD_LEFT ]  [ DPAD_RIGHT ]                    |  |
|  | [  A ]  [  B ]  [  X ]  [  Y ]  [    L3   ]  [    R3    ]  [  SELECT   ]  [   START    ]  [ HOME ]          |  |
|  | [ M1 ]  [ M2 ]  (Dynamic extra hardware chord targets auto-populate here)                                  |  |
|  +-------------------------------------------------------------------------------------------------------------+  |
|                                                                                                                   |
|  +-------------------------------------------------------------------------------------------------------------+  |
|  | ⚡ ACTIVE HARDWARE CHORDS TELEMETRY                                                                         |  |
|  | Status: [LB + START] -> Triggered Virtual Paddle [M1]                                                      |  |
|  +-------------------------------------------------------------------------------------------------------------+  |
|                                                                                                                   |
+-------------------------------------------------------------------------------------------------------------------+
|  TELEMETRY: Polling Rate: 250 Hz | Latency: <1.0 ms                                                               |
+-------------------------------------------------------------------------------------------------------------------+
```

---

### Tab 2: Remapping View

```
+-------------------------------------------------------------------------------------------------------------------+
|  +-- SHIFT LAYERS CONFIGURATION & MANAGEMENT (Expanded Height Panel) -------------------------------------------+  |
|  | Active Layer: [ Shift Layer 1 (Default) v ]    [ + Add Layer ]    [ ✏️ Rename Layer ]    [ 🗑️ Delete Layer ]    |  |
|  |                                                                                                             |  |
|  | Shift Trigger Key:  [ LB      v ]              Shift Modifier: [ RB      v ]                                  |  |
|  | Shift Trigger Mode: (*) Toggle  ( ) Hold                                                                    |  |
|  +-------------------------------------------------------------------------------------------------------------+  |
|                                                                                                                   |
|  +-- FACE BUTTONS ---------------------+   +-- SHOULDERS & STICKS ------------------+                              |
|  | Button | Mapping   | Blk | Shift Map|   | Button | Mapping   | Blk | Shift Map   |                              |
|  | -------|-----------|-----|----------|   | -------|-----------|-----|-------------|                              |
|  |  A     | [space ]R | [x] | [  m   ]R|   |  LB    | [      ]R | [x] | [         ]R|                              |
|  |  B     | [c     ]R | [x] | [      ]R|   |  RB    | [      ]R | [x] | [         ]R|                              |
|  |  X     | [r     ]R | [x] | [      ]R|   |  LT    | [      ]R | [x] | [         ]R|                              |
|  |  Y     | [e     ]R | [x] | [      ]R|   |  RT    | [      ]R | [x] | [         ]R|                              |
|  +-------------------------------------+   +----------------------------------------+                              |
|                                                                                                                   |
|  +-- D-PAD ----------------------------+   +-- SYSTEM & EXTRAS ---------------------+                              |
|  | Button | Mapping   | Blk | Shift Map|   | Button | Mapping   | Blk | Shift Map   |                              |
|  | -------|-----------|-----|----------|   | -------|-----------|-----|-------------|                              |
|  | UP     | [w     ]R | [x] | [      ]R|   | SELECT | [      ]R | [x] | [         ]R|                              |
|  | DOWN   | [s     ]R | [x] | [      ]R|   | START  | [      ]R | [x] | [         ]R|                              |
|  | LEFT   | [a     ]R | [x] | [      ]R|   | HOME   | [      ]R | [x] | [         ]R|                              |
|  | RIGHT  | [d     ]R | [x] | [      ]R|   | M1     | [v     ]R | [x] | [         ]R|                              |
|  +-------------------------------------+   +----------------------------------------+                              |
|                                                                                                                   |
+-------------------------------------------------------------------------------------------------------------------+
```

#### Key Recorder Modal Mockup (`KeyRecorderDialog`)
```
+-------------------------------------------------------------+
| Record Input for [Button Name]                             |
+-------------------------------------------------------------+
|                                                             |
|  [ ⚡ Press key / combo or use Notch UI below ]             |
|                                                             |
|  🖱️ Quick Mouse Buttons:                                    |
|  [ + Left Click ] [ + Right Click ] [ + Middle ]            |
|  [ + Mouse4 ]     [ + Mouse5 ]                              |
|                                                             |
|  📜 Scroll Wheel Notch Settings:                            |
|  Direction: [ Scroll Up v ]    Notches: [ 1  ^v ]           |
|  Mode:      (*) Oneshot ( ) Continuous                      |
|  Delay (s): [ 0.05 ^v ]                                     |
|  [ Apply Scroll Notch Binding ]                             |
|                                                             |
|  ---------------------------------------------------------  |
|  [ Clear ]              [ Save ]              [ Cancel ]    |
+-------------------------------------------------------------+
```

---

### Tab 3: Tuning View

```
+-------------------------------------------------------------------------------------------------------------------+
|  +-- LEFT STICK -----------------------+   +-- RIGHT STICK ----------------------+                              |
|  | [ RADAR VISUALIZER ]                |   | [ RADAR VISUALIZER ]                |                              |
|  | [ 🔄 Circularity Calibration ]       |   | [ 🔄 Circularity Calibration ]       |                              |
|  | [ 📄 Export Curve Math (LaTeX) ]    |   | [ 📄 Export Curve Math (LaTeX) ]    |                              |
|  | Deadzone:         [===|------] 5%   |   | Deadzone:         [===|------] 5%   |                              |
|  | Anti-Deadzone:    [---|------] 0%   |   | Anti-Deadzone:    [---|------] 0%   |                              |
|  | Rest Deadzone:    [---|------] 0%   |   | Rest Deadzone:    [---|------] 0%   |                              |
|  | Warp Threshold:   [---|------] 0%   |   | Warp Threshold:   [---|------] 0%   |                              |
|  | Curve Factor:     [====|-----] 1.2  |   | Curve Factor:     [====|-----] 1.2  |                              |
|  | Sensitivity:      [=====|----] 1.0  |   | Sensitivity:      [=====|----] 1.0  |                              |
|  | Preset: [ Exponential          v ]  |   | Preset: [ Exponential          v ]  |                              |
|  | Custom Math: [ x^1.2              ] |   | Custom Math: [ x^1.2              ] |                              |
|  +-------------------------------------+   +-------------------------------------+                              |
|                                                                                                                   |
|  +-- LEFT TRIGGER ---------------------+   +-- RIGHT TRIGGER --------------------+                              |
|  | [ RESPONSE CURVE GRAPH ]            |   | [ RESPONSE CURVE GRAPH ]            |                              |
|  | Min Deadzone:     [---|------] 0%   |   | Min Deadzone:     [---|------] 0%   |                              |
|  | Max Deadzone:     [█████████-] 100% |   | Max Deadzone:     [█████████-] 100% |                              |
|  | Curve Factor:     [====|-----] 1.0  |   | Curve Factor:     [====|-----] 1.0  |                              |
|  | [ ] Digital Trigger Mode            |   | [ ] Digital Trigger Mode            |                              |
|  +-------------------------------------+   +-------------------------------------+                              |
|                                                                                                                   |
|  [ ❓ Circularity Info Modal ]                                                                                     |
+-------------------------------------------------------------------------------------------------------------------+
```

---

### Tab 4: Advanced View

```
+-------------------------------------------------------------------------------------------------------------------+
|  HARDWARE CHORDS ENGINE (INPUT SUPPRESSION)              [ ? Hardware Chords Guide ]                               |
|  +-------------------------------------------------------------------------------------------------------------+  |
|  | Chord: [ lb+start   ]   Delayed: [        ]   Action: [ M1       ]   Mode: [ auto  v ]   [ X ]             |  |
|  | Chord: [ dpad_up    ]   Delayed: [ dpad_left ] Action: [ L4       ]   Mode: [ 50ms  v ]   [ X ]             |  |
|  +-------------------------------------------------------------------------------------------------------------+  |
|  [ + Add Hardware Chord ]                                                                                         |
|                                                                                                                   |
|  MACROS BUILDER                                          [ ? Macros Guide ]                                       |
|  +-------------------------------------------------------------------------------------------------------------+  |
|  | Macro Name: [ FastCombo1           ]   Mode: (*) Toggle ( ) Loop                                            |  |
|  | Sequence Steps:                                                                                            |  |
|  | [ keyboard:shift+a, delay:50ms, mouse_left, delay:100ms, keyboard:space ]                                  |  |
|  | [ X Delete Macro ]                                                                                         |  |
|  +-------------------------------------------------------------------------------------------------------------+  |
|  [ + Add Macro ]   [ Save Settings ]                                                                          |
+-------------------------------------------------------------------------------------------------------------------+
```

---

### Tab 5: Utilities & Log Console

```
+-------------------------------------------------------------------------------------------------------------------+
|  +-- DIAGNOSTICS & SYSTEM HELPERS -----------------------------------------------------------------------------+  |
|  | [ 📥 Community Profiles Fetcher ]    [ 🛠️ Launch Tools & Diagnostics ]    [ 📈 Open Realtime Oscilloscope ] |  |
|  +-------------------------------------------------------------------------------------------------------------+  |
|                                                                                                                   |
|  +-- CYBER LOG CONSOLE (Real-Time Output Stream) ---------------------------------------------------------------+  |
|  | Filter: [ Search log text...         ]   Level: [ INFO  v ]   [ 🔄 Clear ]   [ 💾 Export Logs ]              |  |
|  | +---------------------------------------------------------------------------------------------------------+ |  |
|  | | [14:05:01] [INFO] Streaming logs from wrapper.log...                                                     | |  |
|  | | [14:05:02] [INFO] Controller Polling: 250 Hz | Latency: 0.8 ms                                            | |  |
|  | | [14:05:05] [DEBUG] Hardware Chord Triggered: LB + START -> M1                                            | |  |
|  | +---------------------------------------------------------------------------------------------------------+ |  |
|  +-------------------------------------------------------------------------------------------------------------+  |
+-------------------------------------------------------------------------------------------------------------------+
```

---

### Tab 6: Customization View & Custom Theme Builder

```
+-------------------------------------------------------------------------------------------------------------------+
|  +-- THEME SELECTOR & PRESETS ---------------------------------------------------------------------------------+  |
|  | Theme Preset: [ Custom Theme Builder v ]   Font Family: [ Inter          v ]   Size: [ 11pt ^v ]            |  |
|  | Palette Swatches: [ 🟣 Purple ] [ 🔵 Blue ] [ 🟢 Green ] [ 🔴 Red ] [ 🟡 Yellow ] [ 🟠 Orange ] [ ⚪ White ]   |  |
|  +-------------------------------------------------------------------------------------------------------------+  |
|                                                                                                                   |
|  +-- CUSTOM THEME BUILDER & COLOR PICKERS ---------------------------------------------------------------------+  |
|  |  Widget Preview Elements                             |  Color Picker Controls                                 |  |
|  |  ---------------------------------------------------+----------------------------------------------------   |  |
|  |  [ Primary Action Button ]                          |  [ 🎨 Pick Color ] Primary Button Base                |  |
|  |  [ Secondary Button ]                               |  [ 🎨 Pick Color ] Secondary Button Base              |  |
|  |  Outlined Text Box: [ Sample Text                ]  |  [ 🎨 Pick Color ] Text Field Border Outline          |  |
|  |  Slider Control:    [=======|--------------]        |  [ 🎨 Pick Color ] Slider Track & Handle Glow         |  |
|  |  Radar Canvas Grid: [ (●) Stick Radar Canvas    ]   |  [ 🎨 Pick Color ] Radar Ring & Vector Point          |  |
|  |  Window Base Frame: [ Dark Space Container     ]   |  [ 🎨 Pick Color ] Window / Card Background           |  |
|  +-------------------------------------------------------------------------------------------------------------+  |
|                                                                                                                   |
|  [ 💾 Export Theme JSON ]   [ 📥 Import Theme JSON ]   [ 🔄 Reset Default Theme ]                                |
+-------------------------------------------------------------------------------------------------------------------+
```

---

## 💡 4. Architectural & Visual Suggestions for Future Rebuilds

1. **Standalone Visual Component Architecture**:
   - Keep each tab in its own completely isolated PySide6 `QWidget` class (e.g. `DashboardTab`, `RemappingTab`, `TuningTab`) with zero cross-tab widget references during `setup_ui()` to avoid `AttributeError` initialization crashes.

2. **Clean Dynamic Custom Theme Builder**:
   - Provide a live `QColorDialog` binding for each element token (Background, Card Fill, Border Glow, Primary Button, Slider Accent, Radar Grid).
   - Export custom user themes cleanly to `themes/custom_theme.json`.

3. **Tuning View Ergonomics**:
   - Place stick-specific actions (`🔄 Circularity Calibration Wizard` and `📄 Export Curve Math`) directly underneath their corresponding Left/Right stick visualizer cards for immediate context.

4. **Simplified Macro Engine UI**:
   - Strictly restrict macro execution modes to **Toggle** (press once to start, press again to stop) and **Loop** (repeats macro sequence continuously while holding button down).

5. **Direct File-Pipe Log Console**:
   - Bind the Log Console `QPlainTextEdit` widget to a background file-tailing thread reading directly from `wrapper.log` or Python's `logging` stream handler, with auto-scroll and line buffer caps (e.g., max 500 lines).

6. **KeyRecorder Mouse Input Names**:
   - Standardize extra mouse button text to `Mouse4` and `Mouse5` instead of driver-specific terms like `X1`/`X2`.
