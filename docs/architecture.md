# Architecture & Runtime Pipeline

<div align="center">

[Runtime Pipeline](#runtime-input-pipeline) • [Thread Model](#thread-model) • [Live Reloading](#live-reloading-architecture) • [Rumble Reverse Engineering](#rumble-reverse-engineering)

</div>

<br>

UR-XD is designed as a high-performance, non-blocking input interception pipeline capable of processing low-latency HID telemetry and translating it to XInput/virtual controller frames.

---

## Runtime Input Pipeline

[diagram of end-to-end input pipeline][Controller to Virtual XInput Processing Pipeline]

```text
Physical Controller (USB / 2.4GHz / Bluetooth)
        ↓
Raw HID / DInput Receiver Thread (hidapi / win32)
        ↓
Decoder & Endpoint Merger (Extracts raw byte offsets to normalized 0-255 / bit flags)
        ↓
Hardware Chords Engine (Evaluates multi-button combos & blocks individual member inputs)
        ↓
Mapper & Shift Layer (Translates normalized inputs to Virtual Gamepad or Keyboard/Mouse)
        ↓
Virtual Gamepad Output Driver (vgamepad / ViGEmBus)
```

---

## Thread Model

UR-XD uses a multi-threaded architecture to ensure zero latency input delivery and responsive UI controls:

1. **Receiver Threads:** Dedicated low-latency worker threads monitoring raw HID endpoints.
2. **Mapper Engine Thread:** Central event loop that processes axis deadzones, curves, macros, and virtual button outputs.
3. **System Tray & GUI Thread:** Runs the dark-mode configuration interface and system tray loop without blocking input processing.

---

## Live Reloading Architecture

When settings are modified in the visual GUI or `config.ini`, the background daemon monitors file modification timestamps:
- Upon detecting changes, the mapping engine re-parses configuration structures in-memory.
- Virtual controller state is preserved during reload—ensuring no disconnect drops during gameplay.

---

## Rumble Reverse Engineering

During initial project development, extensive investigation was conducted to determine why rumble failed in DInput mode on 8BitDo Ultimate 2C devices:
- **Packet Tracing:** Using `hidapitester` and `USBView`, out-of-band output reports were crafted and sent to all physical endpoints.
- **Firmware Gating:** The controller microcontroller responded with ACK on USB endpoints but failed to trigger haptic motors unless the physical hardware switch was set to XInput.
- **Conclusion:** Rumble restrictions are hardware/firmware enforced by controller vendors. UR-XD documents this constraint to prevent wasteful troubleshooting.
