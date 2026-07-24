# Frequently Asked Questions (FAQ)

<div align="center">

[General Questions](#general-questions) • [Hardware & Driver Questions](#hardware--driver-questions) • [Licensing](#licensing)

</div>

<br>

Common questions and answers regarding **UR-XD**.

---

## General Questions

### What does UR-XD stand for?
**UR-XD** stands for **Universal Remapper, XInput/DInput Wrapper, *and* Fixer**.

### Why did you create this project?
The project was originally created out of frustration when the 8BitDo Ultimate 2C wireless controller reported triggers as digital on/off switches under Windows DInput mode despite physically having analog triggers.

### Does UR-XD require flashing custom firmware to my controller?
No! UR-XD works entirely in software on Windows. Your controller warranty remains 100% intact.

---

## Hardware & Driver Questions

### Why doesn't rumble work in DInput mode?
Because controller manufacturers firmware-gate rumble reports inside their microcontrollers. When set to DirectInput mode, the controller ignores rumble output commands entirely. Switch to XInput mode if force feedback is required.

### Can UR-XD remap hardware-locked buttons like "Turbo" or "Pairing"?
No. Special buttons like hardware Turbo or Mode/Pairing switches are handled exclusively by the controller's internal microcontroller and are never sent over USB/Bluetooth reports to Windows.

### Will UR-XD work with my generic HID gamepad?
Yes! As long as Windows can see the HID device, running `.\calibrate.bat` allows you to create a custom profile map for virtually any gamepad.

---

## Licensing

### Is UR-XD free to use?
Yes! UR-XD is licensed under the **PolyForm Noncommercial License 1.0.0**. It is completely free for personal, noncommercial use and modification.
