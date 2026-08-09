"""
HidHide Interop Manager (hidhide_manager.py)
Provides automated double-input prevention using Nefarius HidHide.
Manages process whitelisting, physical HID gamepad cloaking/uncloaking,
device instance path normalization, and crash-recovery safeguards.
"""
import os
import sys
import re
import json
import ctypes
import logging
import subprocess
import atexit
import signal
from typing import List, Optional, Set, Tuple

logger = logging.getLogger('hidhide_manager')

DEFAULT_CLI_PATHS = [
    r"C:\Program Files\Nefarius Software Solutions\HidHide\x64\HidHideCLI.exe",
    r"C:\Program Files\Nefarius Software Solutions\HidHide\HidHideCLI.exe",
]

STATE_FILE_NAME = ".hidhide_active_cloaks.json"


def normalize_device_path(path: str) -> str:
    """
    Normalizes a hidapi device path or raw OS path into a standard Windows Device Instance ID.
    Example:
      Input:  \\\\?\\hid#vid_045e&pid_028e&mi_00#7&37190c10&0&0000#{4d1e55b2-f16f-11cf-88cb-001111000030}
      Output: HID\\VID_045E&PID_028E&MI_00\\7&37190C10&0&0000
    """
    if not path:
        return ""

    cleaned = path.strip()
    # Strip leading \\?\ or \\.\
    cleaned = re.sub(r'^\\\\[\?\.]\\', '', cleaned)
    # Strip trailing GUID block e.g. #{4d1e55b2-f16f-11cf-88cb-001111000030}
    cleaned = re.sub(r'#\{[a-fA-F0-9\-]+\}$', '', cleaned)
    # Convert remaining '#' separators to '\'
    cleaned = cleaned.replace('#', '\\')

    # Convert to uppercase for canonical Windows Device Instance ID matching
    return cleaned.upper()


class HidHideManager:
    """
    Singleton service managing interactions with Nefarius HidHide.
    Handles CLI command execution, application whitelisting, device cloaking,
    and automatic uncloaking cleanup.
    """

    _instance: Optional['HidHideManager'] = None

    def __init__(self, custom_cli_path: Optional[str] = None):
        self.custom_cli_path: Optional[str] = custom_cli_path
        self._cli_path: Optional[str] = None
        self._active_cloaks: Set[str] = set()
        self._state_file_path: str = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            STATE_FILE_NAME
        )
        self._cleanup_registered: bool = False
        self.detect_cli()

    @classmethod
    def instance(cls, custom_cli_path: Optional[str] = None) -> 'HidHideManager':
        if cls._instance is None:
            cls._instance = HidHideManager(custom_cli_path=custom_cli_path)
        elif custom_cli_path:
            cls._instance.custom_cli_path = custom_cli_path
            cls._instance.detect_cli()
        return cls._instance

    @staticmethod
    def is_admin() -> bool:
        """Checks if the current process is running with Administrator privileges."""
        try:
            return ctypes.windll.shell32.IsUserAnAdmin() != 0
        except Exception:
            return False

    def detect_cli(self) -> Optional[str]:
        """Locates HidHideCLI.exe from custom override or standard installation paths."""
        if self.custom_cli_path and os.path.isfile(self.custom_cli_path):
            self._cli_path = self.custom_cli_path
            return self._cli_path

        for p in DEFAULT_CLI_PATHS:
            if os.path.isfile(p):
                self._cli_path = p
                return self._cli_path

        self._cli_path = None
        return None

    def is_installed(self) -> bool:
        """Returns True if HidHideCLI.exe was detected on the system."""
        return self._cli_path is not None and os.path.isfile(self._cli_path)

    def _run_cli(self, args: List[str]) -> Tuple[int, str, str]:
        """Executes HidHideCLI.exe with specified arguments."""
        if not self.is_installed():
            logger.warning("HidHideCLI.exe is not installed or path is invalid.")
            return -1, "", "HidHideCLI not found"

        if not self.is_admin():
            logger.warning("HidHide CLI requires Administrator privileges. Launch UR-XD as Administrator (or via run_wrapper.bat) to allow driver handle access.")

        cmd = [self._cli_path] + args
        try:
            # Hide console window on Windows
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = 0  # SW_HIDE

            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                startupinfo=startupinfo
            )
            stdout, stderr = proc.communicate(timeout=5)
            logger.debug("HidHideCLI exec %s exit code %d", args, proc.returncode)
            return proc.returncode, stdout.strip(), stderr.strip()
        except subprocess.TimeoutExpired:
            logger.error("HidHideCLI command timed out: %s", args)
            return -2, "", "Command timed out"
        except Exception as e:
            logger.error("Failed to run HidHideCLI: %s", e)
            return -3, "", str(e)

    def ensure_app_whitelisted(self, app_path: Optional[str] = None) -> bool:
        """
        Registers executable path to HidHide whitelist so UR-XD can access physical controllers.
        Defaults to current python executable sys.executable if not specified.
        """
        if not self.is_installed():
            return False

        target_app = os.path.abspath(app_path or sys.executable)
        code, stdout, stderr = self._run_cli(["--app-reg", target_app])
        if code == 0:
            logger.info("Successfully whitelisted app in HidHide: %s", target_app)
            return True
        else:
            logger.warning("Failed to whitelist app in HidHide (code=%d): %s", code, stderr)
            return False

    def remove_app_whitelist(self, app_path: Optional[str] = None) -> bool:
        """Unregisters an application from HidHide whitelist."""
        if not self.is_installed():
            return False

        target_app = os.path.abspath(app_path or sys.executable)
        code, stdout, stderr = self._run_cli(["--app-unreg", target_app])
        return code == 0

    def cloak_device(self, raw_device_path: str) -> bool:
        """
        Cloaks (hides) a physical HID device from Windows applications.
        Normalizes device path, adds it to HidHide blocked list, and enables global cloaking.
        """
        if not self.is_installed():
            return False

        instance_id = normalize_device_path(raw_device_path)
        if not instance_id:
            logger.error("Cannot cloak empty device instance ID for path: %s", raw_device_path)
            return False

        # 1. Add device instance ID to blocked list
        code, stdout, stderr = self._run_cli(["--dev-hide", instance_id])
        if code != 0:
            logger.warning("HidHide --dev-hide failed for %s (code=%d): %s", instance_id, code, stderr)
            return False

        # 2. Enable global cloaking
        code_cloak, _, _ = self._run_cli(["--cloak-on"])
        if code_cloak != 0:
            logger.warning("HidHide --cloak-on failed")

        self._active_cloaks.add(instance_id)
        self._save_state()
        self._register_cleanup_hooks()
        logger.info("Successfully cloaked physical controller: %s", instance_id)
        return True

    def uncloak_device(self, raw_device_path: str) -> bool:
        """Unhides a physical HID device, making it visible to Windows again."""
        if not self.is_installed():
            return False

        instance_id = normalize_device_path(raw_device_path)
        if not instance_id:
            return False

        code, stdout, stderr = self._run_cli(["--dev-unhide", instance_id])
        if instance_id in self._active_cloaks:
            self._active_cloaks.remove(instance_id)
            self._save_state()

        if code == 0:
            logger.info("Successfully uncloaked physical controller: %s", instance_id)
            return True
        return False

    def set_cloaking_active(self, active: bool) -> bool:
        """Toggles global HidHide cloaking state ON or OFF."""
        if not self.is_installed():
            return False

        arg = "--cloak-on" if active else "--cloak-off"
        code, stdout, stderr = self._run_cli([arg])
        return code == 0

    def emergency_uncloak_all(self) -> None:
        """
        Safety cleanup: Uncloaks all tracked active devices and disables cloaking.
        Executes automatically on process exit or signal.
        """
        if not self.is_installed() or not self._active_cloaks:
            return

        logger.info("Executing HidHide emergency uncloak for %d devices...", len(self._active_cloaks))
        cloaks_to_clear = list(self._active_cloaks)
        for instance_id in cloaks_to_clear:
            self._run_cli(["--dev-unhide", instance_id])

        self._active_cloaks.clear()
        self._save_state()
        self._run_cli(["--cloak-off"])

    def recover_orphaned_cloaks(self) -> None:
        """
        Reads local state file on startup. If orphaned cloaks exist from a prior crash,
        uncloaks them automatically to protect the user's controllers.
        """
        if not os.path.exists(self._state_file_path):
            return

        try:
            with open(self._state_file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                orphans = data.get("active_cloaks", [])
                if orphans and self.is_installed():
                    logger.warning("Found %d orphaned HidHide device cloaks from prior crash. Restoring...", len(orphans))
                    for inst in orphans:
                        self._run_cli(["--dev-unhide", inst])
                    self._run_cli(["--cloak-off"])
        except Exception as e:
            logger.error("Failed reading HidHide recovery file: %s", e)

        # Clear state file after recovery attempt
        try:
            if os.path.exists(self._state_file_path):
                os.remove(self._state_file_path)
        except Exception:
            pass

    def _save_state(self) -> None:
        """Persists active cloaks to state file for crash recovery."""
        try:
            if not self._active_cloaks:
                if os.path.exists(self._state_file_path):
                    os.remove(self._state_file_path)
                return

            with open(self._state_file_path, "w", encoding="utf-8") as f:
                json.dump({"active_cloaks": list(self._active_cloaks)}, f, indent=2)
        except Exception as e:
            logger.warning("Failed saving HidHide state file: %s", e)

    def _register_cleanup_hooks(self) -> None:
        """Registers atexit and signal handlers once."""
        if self._cleanup_registered:
            return

        self._cleanup_registered = True
        atexit.register(self.emergency_uncloak_all)

        # Handle SIGINT and SIGTERM gracefully on supported platforms
        try:
            signal.signal(signal.SIGINT, self._signal_handler)
            signal.signal(signal.SIGTERM, self._signal_handler)
        except Exception:
            pass

    def _signal_handler(self, signum, frame):
        logger.info("Signal %s received; executing HidHide cleanup...", signum)
        self.emergency_uncloak_all()
        sys.exit(0)
