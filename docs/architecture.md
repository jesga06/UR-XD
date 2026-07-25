# Architecture & Runtime Pipeline

<div align="center">

[Runtime Pipeline](#runtime-input-pipeline) • [Dual-Backend Architecture](#dual-backend-architecture) • [High-Performance Math Engine](#high-performance-1000hz-math-engine) • [Thread Model](#thread-model) • [Live Reloading](#live-reloading-architecture) • [Rumble Reverse Engineering](#rumble-reverse-engineering)

</div>


UR-XD is engineered as a high-performance, non-blocking input interception pipeline capable of processing low-latency HID telemetry and translating it to Virtual XInput controller frames.

## Runtime Input Pipeline

```text
Physical Controller (USB / 2.4GHz / Bluetooth)
        ↓
Raw HID / DInput / XInput Receiver Thread (hidapi / ctypes)
        ↓
Decoder & Composite Endpoint Merger (Extracts raw payload offsets to normalized 0-255 / bit flags)
        ↓
Hardware Chords Engine (Evaluates multi-button combos & suppresses member inputs)
        ↓
Mapper & Shift Layer (Translates normalized inputs to Virtual Gamepad or Keyboard/Mouse)
        ↓
Virtual Gamepad Output Driver (vgamepad / ViGEmBus)
```

## Dual-Backend Architecture

UR-XD features a hot-swappable dual-backend engine:

- **XInput Backend (`backend_xinput.py`):** Utilizes native `ctypes` bindings to poll gamepads in XInput mode, unlocking hardware vibration/rumble, slot management, and high-frequency updates while avoiding generic HID limits.
- **DirectInput HID Backend (`backend_dinput.py`):** Direct raw HID payload parser that reads raw byte packages directly from USB/Bluetooth endpoints, bypassing incomplete or buggy Windows driver descriptors (such as 8BitDo Ultimate 2C digital trigger bugs).

## High-Performance 1000Hz Math Engine

To operate smoothly at high-frequency polling rates (up to 1000Hz) without causing frame drops in games:

- **Zero-Allocation Closures:** Hot-loop math routines eliminate dynamic object allocation during telemetry updates.
- **Pre-Cached Math Evaluation (`_SAFE_MATH_DICT`):** Restricts and pre-caches mathematical string evaluation context for custom user curves without incurring Python runtime evaluation overhead.
- **Pre-Cached Metadata Lookups (`_STANDARD_FIELDS`):** Fast dictionary slot lookups for standard gamepad buttons and axes.
- **True Radial Vector Math:** Computes stick deadzones and response curves on true radial vector magnitude rather than independent axes, yielding a smooth 1.0 circular boundary output.

## Thread Model & Process Guards

UR-XD uses a multi-threaded architecture to ensure zero latency input delivery and responsive UI controls:

1. **Receiver Threads:** Dedicated low-latency worker threads monitoring raw HID endpoints or XInput ctypes slots.
2. **Mapper Engine Thread:** Central event loop that processes axis deadzones, curves, macros, and virtual button outputs.
3. **System Tray & GUI Thread:** Runs the dark-mode configuration interface and system tray loop without blocking input processing.
4. **Single-Instance Process Protection:** Port-locked socket guards prevent duplicate instances of the wrapper, GUI, or calibration wizard, preserving running processes and log continuity.

## Live Reloading Architecture

When settings are modified in the visual GUI or `config.ini`, the background wrapper monitors file modification timestamps:
- Upon detecting changes, the mapping engine re-parses configuration structures in-memory within 5 seconds.
- Virtual controller state (`vgamepad`) is preserved during reload—ensuring no disconnect drops occur during gameplay.

## Rumble Reverse Engineering

During initial project development, an extensive investigation was conducted to determine why rumble failed in DInput mode on 8BitDo Ultimate 2C devices:
- **Packet Tracing:** Using `hidapitester` and `USBView`, out-of-band output reports were crafted and sent to all physical endpoints.
- **Firmware Gating:** The controller microcontroller responded with ACK on USB endpoints but failed to trigger haptic motors unless the physical hardware switch was set to XInput mode.
- **Conclusion:** Rumble restrictions are hardware/firmware enforced by controller vendors. UR-XD documents this constraint to prevent wasteful troubleshooting. For details, see `technical-stuff/RUMBLE_TIMELINE.md`.