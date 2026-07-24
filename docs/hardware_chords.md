# Hardware Chords & Combination Bindings

<div align="center">

[Overview](#overview) • [Evaluation Pipeline](#chord-evaluation-pipeline) • [Double Input Prevention](#double-input-prevention)

</div>

<br>

**Hardware Chords** allow you to trigger unique actions by holding down multiple controller buttons simultaneously (e.g. `LB + RB + Back` to mute audio or toggle Shift layers).

---

## Overview

Unlike basic button remapping where each button is evaluated in isolation, the Hardware Chord Engine inspects combinations before individual button actions are triggered.

[diagram of hardware chord evaluation flow][Hardware Button Combo Evaluation Order]

---

## Chord Evaluation Pipeline

```text
Raw Controller Report
        ↓
Chord Evaluator (Checks active multi-button combinations)
   ├─► Match Found: Suppress individual member buttons & trigger Chord Action
   └─► No Match: Pass individual buttons down to standard Mapper & Shift Layer
```

1. When physical inputs arrive, UR-XD evaluates all registered chord rules.
2. If all required buttons in a chord are active simultaneously, the chord action executes.
3. Individual button actions for chord members are suppressed to prevent accidental triggers.

---

## Double Input Prevention

To prevent `LB` or `RB` from sending normal bumper inputs to a game while you are trying to execute the `LB + RB` chord, UR-XD includes a short chord detection window (~25ms). If a second button in a registered chord is pressed within this window, individual inputs are absorbed cleanly.
