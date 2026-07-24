# Frequently Asked Questions (FAQ)

<div align="center">

[General Questions](#general-questions) • [Hardware & Driver Questions](#hardware--driver-questions) • [Licensing](#licensing)

</div>

Common questions and answers regarding **UR-XD**.

## General Questions

### What does UR-XD stand for?
**UR-XD** *originally* stood for **Universal Remapper & XInput from DInput Wrapper & Fixer**, but since the addition of native XInput support, it now stands for **Universal Remapper and XInput/DInput Wrapper, *and* Fixer**. Enormous change. I know.

> Fun Fact: The first iteration of this project was just called "*ultimate-2c-dinput-fix*". Yes, it got that much feature-crept.

### Why did you create this project?
*I was pissed because my controller artificially gate-kept a function I paid for.*


> **Long and formal explanation:** The project was originally created out of frustration when the 8BitDo Ultimate 2C wireless controller reported triggers as digital on/off switches under Windows DInput mode despite physically having analog triggers.

### Does UR-XD require flashing custom firmware to my controller?
**No!** UR-XD works entirely in software on Windows. Your controller warranty remains 100% intact.

---

## Hardware & Driver Questions

### Why doesn't rumble work in DInput mode?
Because controller manufacturers firmware-gate rumble requests inside their microcontrollers. When set to DirectInput mode, most controllers ignores rumble commands entirely. Switch to XInput mode if force feedback is required.

### Can UR-XD remap hardware-locked buttons like "Turbo" or "Pairing"?
**No.** Special buttons like hardware Turbo or Mode/Pairing switches are handled exclusively by the controller's internal microcontroller and are never sent over USB/Bluetooth reports to Windows, not even in DInput.

### Will UR-XD work with my generic HID gamepad?
**Probably yes!** As long as Windows can see the HID device, running `.\calibrate.bat` allows you to create a custom profile map for virtually any gamepad. I wouldn't even be surprised if someone managed to map a steering wheel or fightstick. It's that *Universal™*.

---

## Licensing

### Is UR-XD free to use?
Yes! UR-XD is licensed under the **PolyForm Noncommercial License 1.0.0**. It is completely free for personal, noncommercial use and modification.
