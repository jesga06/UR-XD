"""
HidHide Helper Utilities (src/hidhide_helper.py)
Provides CLI interop functions for Nefarius HidHide, including sys.executable whitelisting,
PnP Device Instance ID discovery (USB and HID nodes), global cloaking state toggles,
and PnP software re-plug triggers.
"""
import os
import sys
import json
import logging
import subprocess

logger = logging.getLogger(__name__)

DEFAULT_CLI_PATH = r"C:\Program Files\Nefarius Software Solutions\HidHide\x64\HidHideCLI.exe"


def get_hidhide_cli_path() -> str:
    """Returns the resolved path to HidHideCLI.exe if installed."""
    if os.path.exists(DEFAULT_CLI_PATH):
        return DEFAULT_CLI_PATH
    return ""


def is_hidhide_installed() -> bool:
    """Returns True if HidHideCLI.exe is detected on the system."""
    return bool(get_hidhide_cli_path())


def _run_cli(args: list) -> tuple[int, str, str]:
    """Runs HidHideCLI.exe with the specified arguments."""
    cli_path = get_hidhide_cli_path()
    if not cli_path:
        return -1, "", "HidHideCLI.exe not found"

    cmd = [cli_path] + args
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        return res.returncode, res.stdout.strip(), res.stderr.strip()
    except Exception as e:
        logger.error("Error executing HidHideCLI %s: %s", args, e)
        return -1, "", str(e)


def register_app_whitelist() -> tuple[bool, str]:
    """
    Registers the currently executing Python interpreter (sys.executable)
    into the HidHide whitelist (--app-reg).
    """
    python_exe = os.path.abspath(sys.executable)
    code, stdout, stderr = _run_cli(["--app-reg", python_exe])
    if code == 0:
        logger.info("Successfully registered app whitelist for: %s", python_exe)
        return True, f"Registered: {python_exe}"
    else:
        logger.warning("Failed to register app whitelist (code=%d): %s", code, stderr)
        return False, stderr or f"Error code {code}"


def set_global_cloak(active: bool) -> tuple[bool, str]:
    """
    Toggles global HidHide cloaking state ON (--cloak-on) or OFF (--cloak-off).
    """
    arg = "--cloak-on" if active else "--cloak-off"
    code, stdout, stderr = _run_cli([arg])
    if code == 0:
        logger.info("HidHide global cloaking set to: %s", active)
        return True, f"Global cloaking {'ON' if active else 'OFF'}"
    else:
        logger.warning("Failed to set global cloaking to %s (code=%d): %s", active, code, stderr)
        return False, stderr or f"Error code {code}"


def get_connected_controller_vids() -> list[str]:
    """Scans connected HID devices and returns a list of active controller Vendor IDs (e.g. ['2DC8'])."""
    try:
        from hid_reader import HIDReader
        devices = HIDReader.get_all_devices()
        vids = set()
        for d in devices:
            usage_page = d.get('usage_page', 0)
            usage = d.get('usage', 0)
            prod = (d.get('product_string') or '').lower()
            vid = d.get('vendor_id', 0)
            if vid <= 0:
                continue

            # Check HID Gamepad Usage (Page 0x01, Usage 0x05 = Gamepad, Usage 0x04 = Joystick)
            is_gamepad_usage = (usage_page == 0x01 and usage in (0x04, 0x05))
            is_gamepad_name = any(kw in prod for kw in ("controller", "gamepad", "8bitdo", "xbox", "dualshock", "dualsense", "switch", "wireless", "pad"))

            if is_gamepad_usage or is_gamepad_name:
                vids.add(f"{vid:04X}")

        return list(vids)
    except Exception as e:
        logger.debug("Error querying connected controller VIDs: %s", e)
        return []


def get_pnp_instance_ids(vendor_id: str = "") -> list[str]:
    """
    Uses PowerShell Get-PnpDevice to query active (Status == 'OK') Device Instance IDs
    associated exclusively with connected gamepads/controllers.
    Returns both root USB parent IDs and child HID interface IDs for the active controller.
    """
    vids_to_check = [vendor_id.upper()] if vendor_id else get_connected_controller_vids()
    if not vids_to_check:
        logger.info("No connected controller VIDs found to query PnP instance IDs.")
        return []

    vid_conditions = " -or ".join([f'$_.InstanceId -like "*VID_{v}*"' for v in vids_to_check])
    cmd = (
        f'Get-PnpDevice | Where-Object {{ ($_.Status -eq "OK") -and ({vid_conditions}) }} '
        f'| Select-Object InstanceId, FriendlyName, Status | ConvertTo-Json'
    )

    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode != 0 or not res.stdout.strip():
            return []

        data = json.loads(res.stdout)
        items = data if isinstance(data, list) else [data]
        instance_ids = []
        for item in items:
            iid = item.get("InstanceId", "").strip()
            if iid and (iid.startswith("USB\\") or iid.startswith("HID\\")):
                instance_ids.append(iid)

        return instance_ids
    except Exception as e:
        logger.error("Error querying PnP device instance IDs: %s", e)
        return []


def add_device_to_blocklist(instance_id: str) -> tuple[bool, str]:
    """
    Adds a device instance ID to HidHide's blocklist (--dev-hide).
    """
    if not instance_id:
        return False, "Empty Instance ID"

    code, stdout, stderr = _run_cli(["--dev-hide", instance_id])
    if code == 0:
        logger.info("Successfully added instance ID to HidHide blocklist: %s", instance_id)
        return True, f"Cloaked: {instance_id}"
    else:
        logger.warning("Failed to add instance ID to blocklist (code=%d): %s", code, stderr)
        return False, stderr or f"Error code {code}"


def remove_device_from_blocklist(instance_id: str) -> tuple[bool, str]:
    """
    Removes a device instance ID from HidHide's blocklist (--dev-unhide).
    """
    if not instance_id:
        return False, "Empty Instance ID"

    code, stdout, stderr = _run_cli(["--dev-unhide", instance_id])
    if code == 0:
        logger.info("Successfully removed instance ID from HidHide blocklist: %s", instance_id)
        return True, f"Uncloaked: {instance_id}"
    else:
        logger.warning("Failed to remove instance ID from blocklist (code=%d): %s", code, stderr)
        return False, stderr or f"Error code {code}"


def restart_pnp_device(instance_id: str) -> tuple[bool, str]:
    """
    Performs a software PnP device restart (Disable-PnpDevice followed by Enable-PnpDevice).
    """
    if not instance_id:
        return False, "Empty Instance ID"

    cmd = (
        f'Disable-PnpDevice -InstanceId "{instance_id}" -Confirm:$false; '
        f'Start-Sleep -Milliseconds 500; '
        f'Enable-PnpDevice -InstanceId "{instance_id}" -Confirm:$false'
    )

    try:
        res = subprocess.run(
            ["powershell", "-NoProfile", "-Command", cmd],
            capture_output=True,
            text=True,
            timeout=10
        )
        if res.returncode == 0:
            logger.info("Successfully restarted PnP device: %s", instance_id)
            return True, f"Restarted PnP device: {instance_id}"
        else:
            stderr = res.stderr.strip() or f"Exit code {res.returncode}"
            logger.warning("Failed to restart PnP device %s: %s", instance_id, stderr)
            return False, stderr
    except Exception as e:
        logger.error("Error restarting PnP device %s: %s", instance_id, e)
        return False, str(e)


def get_hidhide_status() -> dict:
    """
    Queries HidHide CLI for current system status:
    - installed: bool
    - app_registered: bool (whether sys.executable is in --app-get)
    - cloak_active: bool
    - dev_list: list of blocked instance IDs
    """
    python_exe = os.path.abspath(sys.executable).lower()
    status = {
        "installed": is_hidhide_installed(),
        "app_registered": False,
        "cloak_active": False,
        "dev_list": [],
        "python_exe": python_exe
    }

    if not status["installed"]:
        return status

    # Query --app-get
    code_app, stdout_app, _ = _run_cli(["--app-get"])
    if code_app == 0 and stdout_app:
        registered_apps = [line.strip().lower() for line in stdout_app.splitlines() if line.strip()]
        status["app_registered"] = python_exe in registered_apps

    # Query --dev-get
    code_dev, stdout_dev, _ = _run_cli(["--dev-get"])
    if code_dev == 0 and stdout_dev:
        status["dev_list"] = [line.strip() for line in stdout_dev.splitlines() if line.strip()]

    # Query global cloaking status by attempting a test or parsing
    # HidHideCLI returns status info
    code_cloak, stdout_cloak, _ = _run_cli(["--cloak-on"])
    if code_cloak == 0:
        status["cloak_active"] = True

    return status
