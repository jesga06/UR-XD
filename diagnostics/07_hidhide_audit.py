"""
Diagnostic Step 7: HidHide Driver & Environment Audit (07_hidhide_audit.py)
Audits Nefarius HidHide driver presence, CLI path resolution, Administrator elevation status,
device instance path normalization, and process whitelisting functionality.
"""
import sys
import os
import time
import argparse
import traceback

parser = argparse.ArgumentParser()
parser.add_argument('--debug', '-d', action='store_true')
args, _ = parser.parse_known_args()
IS_DEBUG = args.debug

if IS_DEBUG:
    def debug_excepthook(exc_type, exc_value, exc_traceback):
        print("[DEBUG TRACE]")
        traceback.print_exception(exc_type, exc_value, exc_traceback)
    sys.excepthook = debug_excepthook

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
SRC_DIR = os.path.join(REPO_ROOT, "src")
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

LOG_DIR = os.path.join(REPO_ROOT, "diagnostics_logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "07_hidhide_audit.log")

class DualLogger:
    def __init__(self, filepath):
        self.terminal = sys.stdout
        self.log = open(filepath, "w", encoding="utf-8")

    def write(self, message):
        self.terminal.write(message)
        try:
            self.log.write(message)
            self.log.flush()
        except Exception:
            pass

    def flush(self):
        self.terminal.flush()
        try:
            self.log.flush()
        except Exception:
            pass

logger = DualLogger(LOG_FILE)
sys.stdout = logger
sys.stderr = logger


def main():
    print("=" * 60)
    print("   DIAGNOSTIC STEP 7: HIDHIDE ENVIRONMENT AUDIT")
    print("=" * 60)

    from hidhide_manager import HidHideManager, normalize_device_path
    import hid

    manager = HidHideManager.instance()

    print("\n1. SYSTEM ELEVATION STATUS:")
    is_admin = manager.is_admin()
    print(f"   - Process Elevated (Admin): {is_admin}")
    if not is_admin:
        print("   [!] Note: HidHide CLI operations require Administrator rights.")

    print("\n2. HIDHIDE CLI DETECTION:")
    installed = manager.is_installed()
    cli_path = manager.detect_cli()
    print(f"   - Installed / Detected: {installed}")
    print(f"   - CLI Executable Path: {cli_path or 'NOT FOUND'}")

    if not installed:
        print("\n[!] HidHide is not installed or HidHideCLI.exe was not found.")
        print("    Download HidHide from: https://github.com/nefarius/HidHide/releases")
        return

    print("\n3. DEVICE PATH NORMALIZATION TEST:")
    sample_raw_paths = [
        r"\\?\hid#vid_045e&pid_028e&mi_00#7&37190c10&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}",
        r"\\?\HID#VID_2345&PID_E02D#0000#{4d1e55b2-f16f-11cf-88cb-001111000030}",
    ]
    for raw in sample_raw_paths:
        norm = normalize_device_path(raw)
        print(f"   Raw:  {raw}")
        print(f"   Norm: {norm}\n")

    print("4. CONNECTED USB HID CONTROLLER NORMALIZATION:")
    devices = hid.enumerate()
    print(f"   - Enumerated {len(devices)} total HID devices.")
    gamepad_count = 0
    for d in devices:
        prod = d.get('product_string', '')
        path = d.get('path', '')
        if isinstance(path, bytes):
            path = path.decode('utf-8', errors='ignore')
        if prod and not any(kw in prod.upper() for kw in ("KEYBOARD", "MOUSE", "KB")):
            gamepad_count += 1
            norm_id = normalize_device_path(path)
            print(f"   [{gamepad_count}] Device: {prod}")
            print(f"       Raw Path: {path}")
            print(f"       Device Instance ID: {norm_id}")

    print("\n5. PROCESS WHITELIST STATUS:")
    current_exe = sys.executable
    print(f"   - Current Executable: {current_exe}")
    whitelisted = manager.ensure_app_whitelisted(current_exe)
    print(f"   - Whitelist Registration Result: {whitelisted}")

    print("\n=" * 60)
    print("   HIDHIDE DIAGNOSTIC AUDIT COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    main()
