# Getting Started with UR-XD

<div align="center">

[Prerequisites](#1-prerequisites) • [Installation](#2-installation) • [Calibration](#3-first-time-calibration) • [Running the Daemon](#4-running-the-background-daemon) • [System Tray Controls](#5-system-tray-controls)

</div>

<br>

Getting **UR-XD** up and running takes less than 5 minutes. This guide will walk you through setting up dependencies, running your one-time controller calibration, and intercepting inputs silently in the background.

---

## 1. Prerequisites

Before installing UR-XD, ensure your system satisfies the following hardware and software requirements:

- **Operating System:** Windows 10 or 11 (64-bit).
- **Python:** [Python 3.13](https://www.python.org/downloads/) or higher (ensure "Add Python to PATH" is checked during installation).
- **Virtual Gamepad Driver:** **[ViGEmBus](https://github.com/nefarius/ViGEmBus/releases)** driver installed. This driver allows UR-XD to create virtual Xbox 360 controllers on demand.
- **Physical Controller:** Connected via 2.4 GHz wireless dongle, USB cable, or Bluetooth in **DirectInput (DInput)** or **XInput** mode.

---

## 2. Installation

1. Clone or download this repository to a folder on your computer.
2. Open PowerShell or Command Prompt inside the project directory.
3. Install the required Python packages:

```powershell
pip install -r requirements.txt
```

> 💡 **Tip:** You can also double-click `tools_and_diagnostics.bat` and select Option 5 to install all requirements automatically.

---

## 3. First-Time Calibration

If your controller does not have a profile generated yet (or if you're using a custom HID gamepad), run the interactive calibration wizard:

```powershell
.\calibrate.bat
```

[screenshot of interactive CLI calibration prompt][Guided CLI Endpoint & Button Calibration Stage]

Follow the step-by-step CLI prompts (pressing buttons, pulling triggers, moving analog sticks). Once completed, your custom controller profile will be saved to `profiles/`.

---

## 4. Running the Background Daemon

To start intercepting inputs and driving your virtual controller, launch the wrapper daemon:

```powershell
.\run_wrapper.bat
```

- The command prompt window will automatically minimize/hide.
- A circular white and purple icon will appear in your **Windows System Tray**.
- Your remapped bindings, trigger fixes, and stick deadzones are now active system-wide!

---

## 5. System Tray Controls

UR-XD operates quietly in the background without stealing focus from your games.

[screenshot of system tray icon context menu][Accessing Open Config from System Tray Context Menu]

- **Right-Click System Tray Icon:**
  - **Open Config:** Opens the visual dark-mode Configuration GUI.
  - **Pause Interception:** Temporarily passes physical inputs through without remapping.
  - **Reload Configuration:** Forces an immediate re-read of `config.ini` and `profiles/`.
  - **Exit:** Safely destroys the virtual gamepad and closes the background daemon.
