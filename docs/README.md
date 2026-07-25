# UR-XD Documentation Hub

<div align="center">

[User Documentation](#-user-documentation) • [Developer Documentation](#-developer-documentation) • [Quick Reference](#-quick-reference)

</div>


Welcome to the **Universal Remapper & DInput Fixer (UR-XD)** documentation hub! Whether you are here to fix analog triggers, set up complex mouse macros, tune stick deadzones, or dive deep into raw HID input report decoders, we've got you covered.

## 📖 User Documentation
*For players, controller enthusiasts, and anyone who just wants their gamepad working properly.*

- **[Getting Started](getting_started.md):** System requirements, driver installation, launching the background wrapper, and system tray operations.
- **[User Guide](user_guide.md):** Complete walkthrough of the visual configuration GUI (Dashboard, Remapping, Stick/Trigger Tuning, Circularity Calibrator, Macros Studio, Utilities, and System Tray controls).
- **[Calibration Guide](calibration.md):** Guided CLI wizard, interface endpoint selection, button baselining, and the Interactive Layout Builder tool.
- **[HID Maps & Profiles](hid_maps.md):** Profile JSON structure (`profiles/*.json`), auto-downloading community profiles, and composite endpoint merging.
- **[Macros Studio](macros.md):** Recording keyboard, mouse, and trigger macros, press/hold execution modes, loop delays, and anti-stuck key safeguards.
- **[Hardware Chords](hardware_chords.md):** Origin story, architectural necessity, input suppression, output synthesis, and setting up hardware button combinations.
- **[Troubleshooting Guide](troubleshooting.md):** Detailed diagnostic scenarios covering missing virtual gamepads, double inputs, DirectInput rumble firmware limitations, trigger cross-talk, Steam Input conflicts, and using `generate_issue_report.bat`.
- **[Frequently Asked Questions (FAQ)](faq.md):** Common questions about controller modes, license terms, and hardware quirks.

## 💻 Developer Documentation
*For contributors, reverse engineers, and code mechanics.*

- **[Architecture & Input Pipeline](architecture.md):** Technical breakdown of the runtime pipeline (`Controller -> Backend -> Raw Telemetry -> Decoder -> Chords -> Mapper -> Virtual Gamepad`), threading model, live reload mechanics, and rumble reverse-engineering notes.
- **[Developer Guide](developer_guide.md):** Repository structure (`src/`), custom HID report decoders, JSON profile schema reference, automated diagnostic suite, contribution guidelines, PR formats/templates, and testing workflows.

## ⚡ Quick Reference

| Task | Command / Location |
| :--- | :--- |
| **Run Wrapper** | `.\run_wrapper.bat` |
| **Calibrate Device** | `.\calibrate.bat` |
| **Tools & Diagnostics Menu** | `.\tools_and_diagnostics.bat` |
| **Interactive Layout Builder** | `python technical-stuff/interactive_layout_builder.py` |
| **Run Diagnostics** | `.\generate_issue_report.bat` |
| **Profile Storage** | `profiles/<controller_name>.json` |
| **User Mappings** | `config.ini` |
