# Backend Specification for GUI Integration

> **Version:** 1.0.0  
> **Generated:** 2026-07-25  
> **Target Audience:** GUI Developer  
> **Zero-Ambiguity Policy:** Every function, data type, range, and GUI mapping is explicitly documented. No assumptions required.

## Purpose

This documentation serves as the **single source of truth** for building a graphical user interface (GUI) against the `UR-XD` backend. The target reader can hook up every visual element, form, slider, button, state listener, and data view without reading raw backend code or guessing any data types, units, or behaviors.

## Architecture Overview

The system operates as a **dual-process architecture**:

1. **Daemon Process** (`main.py`) — Runs in the background, managing hardware input, virtual gamepad emulation, input mapping, and macro execution. Communicates with the GUI via file-based state exchange and UDP telemetry.
2. **GUI Process** (`gui.py`) — A standalone frontend that reads/writes shared configuration files and receives real-time controller state via UDP broadcast.

```
┌─────────────────────────────┐     UDP (9999)     ┌───────────────────────┐
│         DAEMON              │ ──────────────────► │         GUI           │
│   main.py                   │                     │   gui.py              │
│   ├── Backend (XInput/DIn)  │  status.json (1Hz)  │   ├── Dashboard       │
│   ├── Decoder               │ ──────────────────► │   ├── Remapping       │
│   ├── HardwareChordEngine   │                     │   ├── Analog Tuning   │
│   ├── Mapper                │  diagnostics.json   │   ├── Advanced        │
│   ├── VirtualPad            │ ──────────────────► │   ├── Utilities       │
│   ├── HapticEngine          │                     │   └── Customization   │
│   └── MacroExecutor         │  config.ini (R/W)   │                       │
│                             │ ◄──────────────────►│                       │
│                             │  profiles/*.json    │                       │
│                             │ ◄──────────────────►│                       │
└─────────────────────────────┘                     └───────────────────────┘
```

## Document Map

This specification is organized into the following files:

### Section 1: Global Data Dictionary & Enums
📄 [`01-data-dictionary.md`](01-data-dictionary.md)

Defines every custom struct, class schema, type alias, and enum used across the backend. Includes:
- `ControllerState` dataclass (the central data bus)
- `RawHIDReport` dataclass
- XInput ctypes structures and button constants
- `ControllerConfig` JSON schema and defaults
- Shift Layer schema
- Haptic Event schema
- `LatencyMonitor` stats schema
- `config.ini` schema (all sections, keys, and allowed values)
- All implicit string enums (curve types, layout types, circularity modes, backend modes)
- Theme JSON schema

---

### Section 2: Exhaustive Function Specifications
Every function in every backend module, documented with the full 7-part template:

1. Identifier & Signature
2. Operational Purpose
3. Input Parameters (every parameter individually)
4. State Mutation & Side Effects
5. Return Value & Payload Interpretation
6. Complete Error & Exception Matrix
7. Timing, Latency & Rate Limiting

Split into 4 parts for manageability:

📄 [`02a-function-specs-backends.md`](02a-function-specs-backends.md)
- `backend_base.py` — Abstract base interface (8 methods)
- `backend_dinput.py` — DInput/HID backend (7 methods)
- `backend_xinput.py` — XInput backend (10 methods + constants + ctypes)
- `decoder.py` — HID report decoder (3 methods + dataclass)
- `hid_reader.py` — Raw HID device reader (8 methods + dataclass + constant)

📄 [`02b-function-specs-config-math-utilities.md`](02b-function-specs-config-math-utilities.md)
- `config_manager.py` — JSON profile manager (1 standalone function + 23 class methods)
- `math_utils.py` — Analog processing math (7 functions)
- `curves.py` — Response curve evaluation (3 functions + 1 global)
- `logger_setup.py` — Logger configuration (1 function)
- `single_instance.py` — Process singleton guard (1 function + 1 global)
- `utilities_backend.py` — Latency monitoring & UDP broadcast (7 class methods + 1 global)

📄 [`02c-function-specs-controller-systems.md`](02c-function-specs-controller-systems.md)
- `virtual_pad.py` — Virtual Xbox 360 gamepad (9 methods + 1 global)
- `mapper.py` — Keyboard/mouse/gamepad mapping (12 methods)
- `haptic_engine.py` — Haptic vibration engine (1 standalone function + 5 class methods)
- `hardware_chords.py` — Hardware-level chord detection (6 methods)
- `macro_executor.py` — Macro playback engine (4 methods)
- `input_graph.py` — Live matplotlib telemetry viewer (1 function + 1 nested)

📄 [`02d-function-specs-main-calibration.md`](02d-function-specs-main-calibration.md)
- `main.py` — Entry point & daemon orchestrator (9 functions + 3 nested callbacks)
- `profile_tools.py` — HID map validation & diff (2 functions)
- `community_fetcher.py` — Community HID map fetcher (6 functions + 4 constants)
- `circularity_modal.py` — Circularity calibration dialog (8 methods)
- `calibration.py` — CLI calibration tool (2 helpers + 12 class methods)

---

### Section 3: System Event & State Listener Directives + Section 4: State Machines
📄 [`03-events-state-machines.md`](03-events-state-machines.md)

**Section 3** documents all asynchronous communication channels:
- UDP Telemetry Broadcast (500Hz, port 9999)
- HID Reader Data Callback pipeline
- XInput Polling Callback pipeline
- Force Feedback Notification pipeline (with haptic hijack suppression)
- Configuration Hot-Reload daemon
- Diagnostics File Broadcast (500ms interval)
- Status File Broadcast (event-driven writes)
- GUI Timer-based Polling Loops (complete frequency table)

**Section 4** documents lifecycle management:
- Daemon initialization sequence (20 ordered steps)
- GUI initialization sequence (11 ordered steps)
- Daemon teardown sequence (4 steps)
- GUI teardown sequence (implicit + modal cleanup)
- Mermaid state transition diagrams for:
  - Daemon connection states (CONNECTING → CONNECTED → DISCONNECTED → ERROR)
  - GUI tab lifecycle (LOADING → ACTIVE)
  - Circularity calibration states (REST → SWEEP → DONE)
  - Shift layer trigger states (INACTIVE ↔ ACTIVE)

---

## Quick Reference: Key Integration Points

| GUI Element | Backend Function | Data Source | Update Frequency |
|---|---|---|---|
| Joystick position display | `ControllerState.lx/ly/rx/ry` | UDP port 9999 | 60Hz UI read |
| Trigger bar display | `ControllerState.lt/rt` | UDP port 9999 | 60Hz UI read |
| Button highlight indicators | `ControllerState.[button]` | UDP port 9999 | 60Hz UI read |
| Deadzone slider | `ControllerConfig.get/set` | JSON profile file | On user change |
| Curve type dropdown | `ControllerConfig.get/set` | JSON profile file | On user change |
| Response curve canvas | `math_utils.process_analog_stick` | Computed | On slider change |
| Connection status pill | `status.json` | Daemon file write | 1Hz read |
| Polling rate display | `diagnostics.json` | Daemon file write | 2Hz read |
| Haptic waveform editor | `parse_haptic_profile()` | User input string | On edit |
| Theme selector | `config.ini [UI] theme` | INI file | On selection |
| Shift layer editor | `ControllerConfig.get/set_shift_layers` | JSON profile file | On user change |
| Circularity calibration | `CircularityCalibrationModal` | Live hardware + canvas | 60Hz |

## File Inventory

| Backend Source File | Size | Primary GUI Surface |
|---|---|---|
| `src/main.py` | 17KB | System tray, daemon lifecycle |
| `src/gui.py` | 178KB | Entire GUI (being replaced) |
| `src/backend_base.py` | 2KB | Abstract interface |
| `src/backend_dinput.py` | 3KB | DInput hardware connection |
| `src/backend_xinput.py` | 9KB | XInput hardware connection |
| `src/decoder.py` | 8KB | HID byte → ControllerState |
| `src/hid_reader.py` | 7KB | Raw USB/BT reading |
| `src/config_manager.py` | 11KB | All profile CRUD |
| `src/math_utils.py` | 6KB | Deadzone/curve/circularity math |
| `src/curves.py` | 4KB | Response curve evaluation |
| `src/virtual_pad.py` | 19KB | Virtual gamepad emulation |
| `src/mapper.py` | 25KB | Input → keyboard/mouse mapping |
| `src/haptic_engine.py` | 6KB | Vibration pattern playback |
| `src/hardware_chords.py` | 7KB | Hardware chord detection |
| `src/macro_executor.py` | 3KB | Macro playback |
| `src/calibration.py` | 71KB | CLI calibration wizard |
| `src/circularity_modal.py` | 10KB | Circularity calibration dialog |
| `src/community_fetcher.py` | 7KB | Community HID map downloads |
| `src/profile_tools.py` | 5KB | HID map validation/diff |
| `src/utilities_backend.py` | 3KB | Latency monitoring |
| `src/logger_setup.py` | 1KB | Logging setup |
| `src/single_instance.py` | 1KB | Singleton process guard |
