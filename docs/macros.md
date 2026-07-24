# Macros Studio & Automation

<div align="center">

[Overview](#overview) • [Execution Modes](#execution-modes) • [Recording Sequences](#recording-sequences) • [Anti-Stuck Key Logic](#anti-stuck-key-safeguard)

</div>

<br>

The UR-XD **Macros Studio** allows binding complex keyboard, mouse, and trigger sequences to any controller button.

---

## Overview

Macros are configured via the visual GUI interface or stored in `macros.json`. They permit precise automation for combos, rapid-fire actions, or complex hotkey shortcuts.

[gif of macro recording & playback preview][Recording and Executing Key Macro in Real-Time]

---

## Execution Modes

1. **Press & Release (One-Shot):** Triggers the macro sequence once when the button is pressed.
2. **Hold to Repeat (Turbo):** Continuously repeats the macro loop while the physical button remains depressed.
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

---

## Anti-Stuck Key Safeguard

A major issue in input simulation tools occurs when a macro is interrupted or the app exits while a simulated key is held down—leaving Windows thinking your `SHIFT` or `CTRL` key is stuck forever.

UR-XD addresses this with an **Active Key Tracking Matrix**:
- Every virtual keypress is registered in an active key table.
- If a macro loop terminates, a profile reloads, or the app shuts down, UR-XD automatically broadcasts explicit `key_up` release events for all active keys.
