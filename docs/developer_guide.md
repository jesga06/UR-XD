# Developer & Contributor Guide

<div align="center">

[Codebase Structure](#codebase-structure) • [Extending Decoders](#extending-decoders) • [Profile Schemas](#profile-schema-reference) • [Testing Workflow](#testing-workflow)

</div>

<br>

Welcome to the UR-XD developer guide! This document outlines codebase organization, custom decoders, profile schemas, and testing workflows for contributors.

---

## Codebase Structure

Key source files reside under the `src/` directory:

```text
src/
├── calibration.py            # Guided CLI calibration tool
├── config.py                 # Configuration loader & config.ini manager
├── controller.py             # Main gamepad mapping & Virtual Controller interface
├── daemon.py                 # System tray daemon & background process runner
├── decoder.py                # Raw HID report decoding engine
├── device_detector.py        # USB/HID device discovery & endpoint scanner
├── gui.py                    # Dark-mode PySide/Tkinter GUI interface
├── hid_database.py           # Community HID profile downloader
├── macro_engine.py           # Macro execution & anti-stuck key tracking
├── mapper.py                 # Button remapping & pynput keyboard/mouse simulation
├── profile_manager.py        # Profile JSON loader & validator
└── tuning.py                 # Deadzone calculation & circularity algorithms
```

---

## Extending Decoders

If a new controller requires special payload handling (such as multi-byte checksum verification or custom bit masking), you can extend `src/decoder.py`:

1. Inherit from `BaseDecoder`.
2. Implement `parse_report(self, raw_bytes: bytes) -> dict`.
3. Register your decoder class in `DecoderFactory`.

---

## Profile Schema Reference

Controller profiles in `profiles/` must strictly validate against the JSON schema:

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["device_name", "vendor_id", "product_id", "endpoints", "axes", "buttons"],
  "properties": {
    "device_name": {"type": "string"},
    "vendor_id": {"type": "integer"},
    "product_id": {"type": "integer"},
    "endpoints": {"type": "array", "items": {"type": "integer"}},
    "axes": {"type": "object"},
    "buttons": {"type": "object"}
  }
}
```

---

## Testing Workflow

1. Run unit tests before submitting Pull Requests:
```powershell
python -m unittest discover -s tests
```
2. Verify visual GUI layout rendering using the Interactive Layout Builder tool:
```powershell
python technical-stuff/interactive_layout_builder.py
```
3. Run `generate_issue_report.bat` to verify diagnostic suite health.
