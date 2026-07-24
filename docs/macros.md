# Macros Studio & Automation

<div align="center">

[Overview](#overview) • [Execution Modes](#execution-modes) • [Recording Sequences](#recording-sequences) • [Referencing & Setup](#referencing--setup) • [Anti-Stuck Key Safeguards](#anti-stuck-key-safeguards)

</div>

<br>

The UR-XD **Macros Studio** allows binding complex multi-action sequences (keyboard keys, mouse clicks, delays, and trigger pulls) to any controller button or chord combination.

## Overview

Macros are configured via the GUI or while stored in `macros.json`. They permit precise automation for combos, rapid-fire actions, or complex hotkey shortcuts.

[gif of macro recording][Recording a Key Macro in Real-Time]

## Execution Modes

1. **Press & Release (One-Shot):** Triggers the macro sequence once when the button is pressed.
2. **Hold to Repeat (Turbo):** Continuously repeats the macro loop while the physical button remains pressed.
3. **Toggle Loop:** Pressing the button once starts the macro loop infinitely; pressing it a second time stops execution.

---

## Recording Sequences

When recording a macro in the GUI, UR-XD captures:
- **Down Actions:** Keypress or mouse button click down events.
- **Up Actions:** Key or mouse release events.
- **Delays:** Inter-key delays specified in milliseconds.

Example Macro JSON structure:
```json
{
  "macro_id": "fast_combo",
  "trigger_button": "r4",
  "mode": "press",
  "actions": [
    {"type": "key_down", "value": "keyboard:shift"},
    {"type": "delay", "ms": 50},
    {"type": "key_down", "value": "keyboard:e"},
    {"type": "delay", "ms": 50},
    {"type": "key_up", "value": "keyboard:e"},
    {"type": "key_up", "value": "keyboard:shift"}
  ]
}
```

## Referencing & Setup

Macros can be assigned by typing `macro:MyMacro` (or simply `MyMacro`) into any button field in the **Remapping** tab or **Shift Layer** panel. The mapper engine resolves the macro name automatically!

## Anti-Stuck Key Safeguards

A major flaw in input simulation utilities occurs when a macro is interrupted or the application closes while a simulated key is held down—leaving Windows believing `SHIFT` or `CTRL` is stuck down forever.

UR-XD eliminates this using an **Active Key Tracking Matrix**:
- Every simulated keypress is registered in an active key table (`macro_engine.py`).
- If a macro loop terminates, a profile reloads, or the wrapper shuts down, UR-XD automatically broadcasts explicit `key_up` release events for all active keys.
