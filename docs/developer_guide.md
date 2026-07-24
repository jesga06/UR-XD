# Developer & Contributor Guide

<div align="center">

[Codebase Structure](#codebase-structure) • [Contributing Guidelines](#contributing-guidelines) • [PR Format & Template](#pull-request-pr-format--template) • [Extending Decoders](#extending-decoders) • [Profile Schema](#profile-schema-reference) • [Testing & Diagnostics](#testing--diagnostics)

</div>

<br>

Welcome to the **UR-XD** developer and contributor guide! This document outlines repository organization, code conventions, pull request templates, decoder extension points, and testing workflows.

## Codebase Structure

UR-XD source files reside primarily in `src/`, with utilities in `technical-stuff/`:

```text
src/
├── calibration.py            # Guided CLI calibration tool & profiling wizard
├── config.py                 # Configuration loader & config.ini manager
├── controller.py             # Main gamepad mapping engine & vgamepad interface
├── daemon.py                 # System tray wrapper & background process runner
├── decoder.py                # Raw HID report decoding engine & BaseDecoder class
├── device_detector.py        # USB/HID device discovery & endpoint scanner
├── gui.py                    # PySide6 GUI interface
├── hid_database.py           # Community HID profile downloader & GitHub API fetcher
├── macro_engine.py           # Macro execution & anti-stuck key tracking
├── mapper.py                 # Button remapping & pynput keyboard/mouse simulation
├── profile_manager.py        # Profile JSON loader & schema validator
└── tuning.py                 # Radial deadzone math, response curves & circularity
```

Auxiliary directories:
- **`profiles/`:** Device profile JSON files named by VID/PID.
- **`technical-stuff/`:** Deep architectural timelines and the `interactive_layout_builder.py`.
- **`tests/`:** Unittest test suites.

## Contributing Guidelines

We welcome contributions! To maintain code quality and architectural stability, please follow these guidelines:

### 1. Code Style & Conventions
- **Explicit UTF-8 Encoding:** Always specify `encoding='utf-8'` when opening files or managing configuration persistence.
- **Performance-First Hot Loop:** Keep input polling loops allocation-free. Avoid instantiating heavy objects inside high-frequency math calls (~1000Hz).
- **Button Name Standardization:** All button names exposed to client code or UI elements must be standardized to uppercase (e.g. `A`, `B`, `LB`, `L4`).
- **No Silent Error Swallowing:** Log exceptions clearly in `wrapper.log` or raise descriptive exceptions.

### 2. Git & Commit Protocol
- Work on a dedicated feature or fix branch (e.g. `feat/custom-decoder` or `fix/trigger-deadzone`).
- Use Conventional Commit prefixes:
  - `feat:` New user-facing feature or enhancement.
  - `fix:` Bug fix or error resolution.
  - `docs:` Documentation updates or additions.
  - `refactor:` Code restructuring without functional changes.
  - `test:` Unit tests or testing infrastructure additions.
- Make commits atomic (one logical change per commit).

## Pull Request (PR) Format & Template

When submitting a Pull Request, please copy and fill out the following template in your PR description:

```markdown
## Summary of Changes
Provide a brief summary of what this PR accomplishes and why it is needed.

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change fixing an issue)
- [ ] ✨ New feature (non-breaking change adding functionality)
- [ ] ♻️ Refactoring (no functional or API change)
- [ ] 📚 Documentation update
- [ ] 🧪 Test suite addition / update
- [ ] ❓ Other

## Related Issues
Fixes # (issue number)

## How Has This Been Tested?
Describe the testing performed to verify your changes:
- [ ] Executed unittest suite (`python -m unittest discover -s tests`).
- [ ] Verified live wrapper execution (`.\run_wrapper.bat`).
- [ ] Tested GUI configuration rendering.

## Checklist
- [ ] My code follows the project's code style and formatting guidelines.
- [ ] I have updated relevant documentation files in `docs/` if functionality changed.
- [ ] All new and existing unit tests pass cleanly.
```

## Extending Decoders

If a new hardware gamepad requires specialized payload parsing (such as multi-byte checksum verification or custom bit-masking), you can extend `src/decoder.py`:

1. Inherit from `BaseDecoder`:
   ```python
   class CustomControllerDecoder(BaseDecoder):
       def parse_report(self, raw_bytes: bytes) -> dict:
           # Extract custom payload byte offsets and return normalized input dictionary
           ...
   ```
2. Register your decoder class in `DecoderFactory` in `src/decoder.py`.

## Profile Schema Reference

Controller profiles in `profiles/` must strictly validate against the profile JSON schema:

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

If adding a new profile for a popular controller, verify your JSON file with `validate_hid_map` on the Dashboard tab, and submit a PR to add it to the community database!

## Testing & Diagnostics

Before submitting changes, run the test suite:

```powershell
python -m unittest discover -s tests
```

To verify system diagnostics and environment health, run:

```powershell
.\generate_issue_report.bat
```
