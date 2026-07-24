# UR-XD Documentation Hub

<div align="center">

[User Documentation](#-user-documentation) • [Developer Documentation](#-developer-documentation) • [Quick Reference](#-quick-reference)

</div>

<br>

Welcome to the **Universal Remapper & DInput Fixer (UR-XD)** documentation hub! Whether you are here to fix analog triggers, set up complex mouse macros, or dive deep into raw HID input report decoders, we've got you covered.

---

## 📖 User Documentation
*For players, controller enthusiasts, and anyone who just wants their gamepad working properly.*

- **[Getting Started](getting_started.md):** System requirements, driver installation, launching the background daemon, and system tray operation.
- **[User Guide](user_guide.md):** Complete walkthrough of the dark-mode configuration GUI (Dashboard, Remapping, Stick/Trigger Tuning, Circularity Calibrator, and Utilities).
- **[Calibration Guide](calibration.md):** Interactive CLI wizard, Stage 1 endpoint auto-detection, Stage 2 manual override, and the Interactive Layout Builder tool.
- **[HID Maps & Profiles](hid_maps.md):** Profile JSON structure (`profiles/*.json`), auto-downloading community profiles, and composite endpoint merging.
- **[Macros Studio](macros.md):** Recording keyboard, mouse, and trigger macros, press/hold execution modes, loop delays, and anti-stuck key safeguards.
- **[Hardware Chords](hardware_chords.md):** Configuring hardware button combinations and evaluating button chording prior to mapping.
- **[Troubleshooting Guide](troubleshooting.md):** Diagnosing missing virtual gamepads, double inputs, DirectInput rumble firmware limitations, and using `generate_issue_report.bat`.
- **[Frequently Asked Questions (FAQ)](faq.md):** Common questions about controller modes, license terms, and hardware quirks.

---

## 💻 Developer Documentation
*For contributors, reverse engineers, and code mechanics.*

- **[Architecture & Input Pipeline](architecture.md):** Complete technical breakdown of the runtime pipeline (`Controller -> Backend -> Raw Telemetry -> Decoder -> Chords -> Mapper -> Virtual Gamepad`), threading model, live reload mechanics, and rumble reverse-engineering notes.
- **[Developer Guide](developer_guide.md):** Repository structure (`src/`), custom HID report decoders, JSON profile schema reference, automated diagnostic suite, and testing workflows.

---

## ⚡ Quick Reference

| Task | Command / Location |
| :--- | :--- |
| **Run Daemon** | `.\run_wrapper.bat` |
| **Calibrate Device** | `.\calibrate.bat` |
| **Interactive Layout Builder** | `python technical-stuff/interactive_layout_builder.py` |
| **Run Diagnostics** | `.\generate_issue_report.bat` |
| **Profile Storage** | `profiles/<controller_name>.json` |
| **User Mappings** | `config.ini` |
