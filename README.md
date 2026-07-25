# Universal Remapper, XInput/DInput Wrapper, ***and*** Fixer

<div align="center">

[Overview](#-what-problem-does-this-solve) • [Quick Start](#-quick-start-5-minutes) • [Documentation Index](#-documentation-index) • [Extras & Origin Story](#-extras) • [License](#-license)

</div>


**Fixes Windows controllers whose HID descriptors lie just enough to ruin your day.**

**UR-XD** is a lightweight Windows utility ***originally*** designed to fix controllers whose HID descriptors are incomplete or broken, restoring missing analog triggers, enabling extra back buttons, mapping inputs to macros, keyboard, and mouse actions. [Also does a whole truckload of other shit.](FEATURELIST.md)

## 🎯 What Problem Does This Solve?

Many third-party controllers report incorrect behavior on Windows depending on their operating mode (DirectInput vs XInput)—such as analog triggers being treated as digital switches in DInput, or extra back paddles being entirely inaccessible in XInput.

UR-XD bypasses buggy driver descriptors, decodes raw HID payload data directly, and exposes a fully compliant Virtual Xbox 360 controller while allowing deep customization and remapping.

### Why Use UR-XD?
- **Analog Triggers Fix:** Restores missing analog polling on controllers with broken DInput configurations. You paid for analog triggers, you're getting analog triggers.
- **Precise Tuning & Tinkering:** Adjust button remapping, macros, stick and trigger deadzones, response curves, circularity, and sensitivity, even on controllers without official software support.
- **No Firmware Hacks:** Fixes issues entirely in software without voiding warranties or flashing custom firmware.
- **And Much More!** Check out the full list of features in the [Features List](FEATURELIST.md).

## 🎮 Supported Devices

### Officially Supported
- ✅ **8BitDo Ultimate 2C Wireless 2.4 GHz** (literally what this whole project was built to fix)
- ✅ **Machenike G5 Pro**

> ℹ️ **NOTE**: These are only the devices tested so far. If your controller is not listed, don't forget what the ***U*** in ***UR-XD*** stands for—it might still be compatible! Check out the [Calibration Guide](docs/calibration.md) for more information.

## ⚡ Quick Start (5 Minutes)

### 1. Prerequisites
- **Python 3.13-3.14** installed.
- **[ViGEmBus Driver](https://github.com/nefarius/ViGEmBus/releases)** installed on your system.

### 2. Install Dependencies
Run the following command in PowerShell or Command Prompt (or via Option 5 in `tools_and_diagnostics.bat`):
```powershell
pip install -r requirements.txt
```

### 3. Calibrate Your Controller (One-time Setup)
Run the guided calibration wizard:
```powershell
.\calibrate.bat
```
[screenshot of interactive CLI calibration prompt][Guided Button Calibration]

Follow the step-by-step prompts (pressing buttons, pulling triggers, moving thumbsticks). You can skip buttons by typing `s` or undo by typing `u`. A custom controller profile will be saved automatically in `profiles/`.

### 4. Launch the Wrapper & GUI
Start the wrapper process:
```powershell
.\run_wrapper.bat
```
Right-click the system tray icon and select **Open Config** to open the GUI and tinker with your controller to your heart's extent.

[screenshot of configuration GUI dashboard][GUI Configuration Dashboard & Live Remapping Interface]

## 📚 Documentation Index

For detailed guides, deep architecture breakdowns, and troubleshooting, explore the full documentation suite:

### 📖 User Documentation
- **[Getting Started](docs/getting_started.md):** Complete installation, requirements, and background wrapper configuration.
- **[User Guide](docs/user_guide.md):** Detailed breakdown of GUI tabs (Dashboard, Remapping, Tuning, Macros, Utilities, System Tray).
- **[Calibration Guide](docs/calibration.md):** Endpoint selection, button baselining, and Interactive Layout Builder.
- **[HID Maps & Profiles](docs/hid_maps.md):** Profile JSON formats, database auto-downloads, and multi-endpoint hardware merging.
- **[Macros Studio](docs/macros.md):** Recording sequences, press/hold states, loop modes, and anti-stuck key logic.
- **[Hardware Chords](docs/hardware_chords.md):** Configuring hardware button combinations and multi-button chords.
- **[Troubleshooting Guide](docs/troubleshooting.md):** Solutions for undetected controllers, double inputs, rumble restrictions, and issue reporting.
- **[FAQ](docs/faq.md):** Frequently asked questions.

### 💻 Developer Documentation
- **[Architecture & Pipeline](docs/architecture.md):** Input pipeline architecture, data flow, thread model, and hardware rumble findings.
- **[Developer Guide](docs/developer_guide.md):** Codebase navigation (`src/`), custom decoders, profile schemas, PR guidelines, and testing workflows.

## 🎨 EXTRAS

### AI NOTICE:
Yes, this was programmed by a clanker.

No, the clanker did not do the fun part (the actual reverse engineering behind this hot mess).

No, I don't feel bad about it.

### NOTES:
- **No Force Feedback / Rumble in DirectInput (DInput) Mode:** Force feedback (rumble) is **not supported** in DirectInput mode and likely never will be. Extensive reverse-engineering revealed that controller microcontrollers firmware-gate output reports outside of XInput mode, ignoring haptic motor execution routines entirely. For details on the technical reverse-engineering campaign, see the [Rumble Investigation Timeline](docs/architecture.md#rumble-reverse-engineering).
- No, this tool does not disable the hardware L4/R4 remapping. I have no idea how to disable that.
  - It does let you completely disable or remap the home button to something else though, so there's that!
- It also does not let you remap special controller buttons like "turbo", a profile/mode switch, pairing button, the one you'd use to remap extra buttons, etc.

### (maybe) TO-DOs:
- [ ] bundle all of this up into a standalone `.exe` executable for those who just want to use the damn controller they paid for

### (fun) TIMELINE OF EVENTS THAT LED TO THIS PROJECT COMING TO LIFE:

Stumbled upon a [reddit post](https://www.reddit.com/r/Controller/comments/1hu5faa/guide_for_8bitdo_ultimate_2c_wireless_controller/) with some tips about the 8BitDo Ultimate 2 controller family. Noticed that my controller could be used in Xinput or Dinput modes. Decided to test it out.

Noticed that for some godforsaken reason the triggers didn't use analog polling when the controller was set to Dinput. Got pissed.

Used [this USBView Tool](https://learn.microsoft.com/en-us/windows-hardware/drivers/debugger/usbview) to find out the VID and PID.

Used [this CLI tool](https://github.com/todbot/hidapitester) to read raw input to determine whether it was a firmware issue (the controller actually just wouldn't send analog data) or if it was Windows being Windows.

Noticed the controller was actually sending analog data. "Windows being Windows" theory didn't make sense because no tool correctly reported analog input.

Decided to take a look into the descriptor to figure out how the values were being mapped. Found out the 8BitDo engineers are lazier than I am (The descriptors didn't properly map to what the controller actually outputs). Got even more pissed.

Wrote a proof of concept script. Concept was proven. Wrote a prompt. AI pumped this out faster than anyone could have. Learned basic black-box reverse engineering in the process. Not pissed anymore.

Ended up feature-creeping this to the point where the name of this repository was outdated within hours of creation.

## 📜 License

This project is licensed under the **PolyForm Noncommercial License 1.0.0**. Free for noncommercial use and modification under the terms of the license.
