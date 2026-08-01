# Getting Started with UR-XD

<div align="center">

[Prerequisites](#1-prerequisites) • [Installation](#2-installation) • [Calibration](#3-first-time-calibration) • [Running the Wrapper](#4-running-the-wrapper) • [System Tray Controls](#5-system-tray-controls)

</div>


Getting **UR-XD** up and running takes less than 5 minutes. This guide will walk you through setting up dependencies, running your one-time controller calibration, and running the background wrapper process.

## 1. Prerequisites

Before installing UR-XD, ensure your system satisfies the following hardware and software requirements:

- **Operating System:** Windows 10 or 11 (64-bit).
- **Python:** [Python 3.13 or 3.14](https://www.python.org/downloads/) (ensure "Add Python to PATH" is checked during installation).
- **Virtual Gamepad Driver:** **[ViGEmBus](https://github.com/nefarius/ViGEmBus/releases)** driver installed. This driver allows UR-XD to create virtual Xbox 360 controllers on demand.
    - **Optional:** Install **[HidHide](https://github.com/nefarius/HidHide/releases)** to prevent double inputs in games.
- **Physical Controller:** Connected via 2.4 GHz wireless dongle, USB cable, or Bluetooth in **DirectInput (DInput)** or **XInput** mode.

## 2. Installation

1. Clone or download this repository to a folder on your computer.
2. Open PowerShell or Command Prompt inside the project directory.
3. Install the required Python packages:

```powershell
pip install -r requirements.txt
```

> 💡 **Tip:** You can also double-click `tools_and_diagnostics.bat` and select **Option 2** to install or repair all dependencies automatically.

## 3. First-Time Calibration

If your controller does not have a profile generated yet (or if you're using a generic HID gamepad), run the interactive calibration wizard:

```powershell
.\calibrate.bat
```

[screenshot of interactive CLI calibration prompt][Guided CLI Endpoint & Button Calibration Stage]

Follow the step-by-step CLI prompts (pressing buttons, pulling triggers, moving thumbsticks). You can skip buttons by typing `s` or undo mispresses by typing `u`. Once completed, your custom controller profile will be saved automatically to `profiles/`.

## 4. Running the Wrapper

To start intercepting inputs and driving your virtual controller, launch the wrapper process:

```powershell
.\run_wrapper.bat
```

- The command prompt window will automatically hide/minimize.
- A circular white and purple icon will appear in your **Windows System Tray**.
- Your remapped bindings, trigger fixes, and stick deadzones are now active system-wide!

> 💡 **Silent Boot Mode:** You can pass the `--boot` argument to `main.py` (or run in boot mode) to launch the wrapper silently on Windows startup without opening the GUI configuration window.

## 5. System Tray Controls

UR-XD operates quietly in the background without stealing focus from your games.

[screenshot of system tray icon context menu][Accessing Open Config from System Tray Context Menu]

Right-clicking the system tray icon reveals the full context menu:
- **Open Config:** Opens the visual dark-mode Configuration GUI to tweak mappings live.
- **Pause Interception:** Temporarily passes physical inputs directly through to the virtual gamepad without applying remappings or button blocks.
- **Reload Configuration:** Forces an immediate re-read of `config.ini` and `profiles/`.
- **Show Console:** Restores the minimized CLI wrapper console window to the foreground.
- **Exit:** Safely destroys the virtual gamepad instance (`vgamepad`) and closes the background wrapper process cleanly.
