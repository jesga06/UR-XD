# HID Maps & Profile Architecture

<div align="center">

[Profile JSON Structure](#profile-json-structure) • [Community Database](#community-hid-map-database) • [Composite Endpoint Merging](#composite-endpoint-merging)

</div>

UR-XD separates hardware button reading from virtual controller output by storing controller specifications in JSON format inside `profiles/`.

## Profile JSON Structure

Each profile file defines hardware identification (VID/PID), endpoint parsing rules, axis bit-lengths, and button byte offsets:

```json
{
  "device_name": "8BitDo Ultimate 2C Wireless",
  "vendor_id": 11720,
  "product_id": 12550,
  "endpoints": [0],
  "axes": {
    "left_stick_x": {"byte": 1, "type": "uint8", "min": 0, "max": 255},
    "left_stick_y": {"byte": 2, "type": "uint8", "min": 0, "max": 255, "invert": true},
    "left_trigger": {"byte": 5, "type": "uint8", "min": 0, "max": 255}
  },
  "buttons": {
    "a": {"byte": 7, "bit": 0},
    "b": {"byte": 7, "bit": 1},
    "l4": {"byte": 8, "bit": 4},
    "r4": {"byte": 8, "bit": 5}
  }
}
```

## Community HID Map Database

To save users from manually calibrating popular gamepads, UR-XD features an **Automated Community Database Downloader**:

1. On first startup, UR-XD queries the online community HID map repository.
2. Missing or updated controller profiles are downloaded into `profiles/` seamlessly.
3. If you create a profile using `calibrate.bat`, consider submitting your JSON file as a Pull Request to help out the community!

## Composite Endpoint Merging

Certain hardware designs (like the **Machenike G5 Pro**) do not send all inputs inside a single signal packet. Instead, they operate as a composite USB device with multiple interfaces:

- **Interface 0:** Transmits standard face buttons and thumbstick positions.
- **Interface 1:** Transmits back paddle states and motion sensor data.

UR-XD's multi-threaded backend concurrently listens to all declared interfaces in `"endpoints": [0, 1]`, combining inputs into a single controller report before passing data to the remapping pipeline.
