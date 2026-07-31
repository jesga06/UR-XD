# Hardware Chords & Combination Bindings

<div align="center">

[What Is It?](#what-is-it) • [Origin & Conception](#why-is-it-there) • [Step-by-Step Setup](#how-to-set-it-up)

</div>


**Hardware Chords** allow you to trigger unique virtual gamepad actions, keyboard shortcuts, or macros by holding down combinations of physical controller buttons simultaneously (e.g. `LB + Start`, `Home + Dpad Up`, or `LB + RB`).

## What Is It?

Hardware Chords is a feature built into UR-XD that evaluates multi-button combinations before standard button mapping occurs. It allows physical controller buttons to act as modifier combinations—effectively creating extra virtual button slots without needing special software from the manufacturer.

## Why Is It There?

In standard **XInput mode**, Windows gamepad protocols strictly recognize a fixed 10-button + 2-trigger layout. Standard third-party controllers equipped with back paddles (such as `L4` and `R4`) or extra shoulder buttons cannot expose these extra inputs to Windows when operating in XInput mode because the XInput driver specification simply has no slots for them.

Furthermore, users who wanted to map shortcuts (like muting Discord or toggling Shift layers) using standard buttons (like `LB + RB` or `LB + Start`) ran into a major problem: pressing `LB + Start` would send the `LB` bumper click and `Start` pause menu press to the game first, causing accidental grenade throws or unwanted pause screens.

To solve both problems, UR-XD evaluates chord combinations upstream:
1. It creates synthetic input slots for extra buttons and combinations.
2. It swallows the physical member button presses before they reach the game via **Input Suppression**, eliminating accidental double inputs entirely.

> [!IMPORTANT]
> Hardware Chords require **XInput mode**. When connected in DirectInput (DInput) mode, an XInput backend warning banner appears in the Advanced tab and hardware chord creation controls are automatically disabled.

## How to Set It Up

Setting up Hardware Chords is done visually in the GUI:

1. Navigate to the **Advanced** tab and scroll to the **Hardware Chords Builder** frame.
2. Click **Add New Chord** to create a chord entry.
3. **Select Primary & Modifier Buttons:**
   - Pick your primary chord button (e.g., `LB`) and secondary modifier button (e.g., `RB` or `Start`).
4. **Configure Output Action:**
   - Type your desired output in the action field (e.g., `keyboard:ctrl+shift+m`, `mouse4`, or `macro:MyCombo`).
5. **Toggle Input Suppression:**
   - Keep **Input Suppression** checked (recommended) so the base physical buttons are swallowed when the chord triggers.
6. **Save Mappings:**
   - Changes are debounced and saved automatically to your controller profile in real-time.
