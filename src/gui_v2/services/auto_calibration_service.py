"""
Auto-Calibration & Profile Resolution Service (auto_calibration_service.py)
Executes automated decision tree when a controller is detected:
1. Is Controller in XInput Mode? -> Skip calibration.
2. Does Local Profile Exist? -> Load local profile.
3. Fetch Community Profile -> If cached/downloaded successfully, load profile.
4. Otherwise -> Launch Native GUI Calibration Wizard.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from PySide6.QtCore import QObject, Signal

from backend_base import ConnectionState

logger = logging.getLogger("auto_calibration_service")


class ProfileDecisionEngine(QObject):
    """
    Automated profile decision engine for detecting hardware modes,
    matching existing profiles (local/community), or triggering wizard calibration.
    """
    profile_resolved = Signal(str)  # Emits path to profile JSON (or "xinput")
    launch_wizard = Signal(dict)    # Emits device info payload when wizard needed
    state_changed = Signal(object)  # Emits ConnectionState

    def __init__(self, parent: Optional[QObject] = None):
        super().__init__(parent)
        self._current_state: ConnectionState = ConnectionState.DISCONNECTED

    @property
    def current_state(self) -> ConnectionState:
        return self._current_state

    def set_state(self, state: ConnectionState) -> None:
        if self._current_state != state:
            self._current_state = state
            self.state_changed.emit(state)
            logger.info(f"ProfileDecisionEngine state changed to: {state.name}")

    def process_device(self, device_info: dict, is_xinput: bool = False, force_calibrate: bool = False) -> None:
        """
        Executes automated profile decision tree when a controller is detected during CONNECTING state.
        
        Args:
            device_info: Dictionary containing HID device attributes (vendor_id, product_id, product_string, path, etc.)
            is_xinput: True if controller is actively in XInput mode.
            force_calibrate: If True, skips profile checks and launches calibration wizard directly.
        """
        self.set_state(ConnectionState.CONNECTING)

        if force_calibrate:
            logger.info(f"Force calibration requested for device {device_info.get('product_string')}. Triggering wizard.")
            self.launch_wizard.emit(device_info)
            return

        # 1. Is Controller in XInput Mode?
        if is_xinput:
            logger.info("Device is in XInput mode. Skipping calibration.")
            self.set_state(ConnectionState.CONNECTED)
            self.profile_resolved.emit("xinput")
            return

        vid = device_info.get('vendor_id', 0)
        pid = device_info.get('product_id', 0)
        
        # 2. Does Local Profile Exist?
        local_profile = f"profiles/{vid:04X}_{pid:04X}.json".lower()
        if os.path.exists(local_profile):
            logger.info(f"Found local profile: {local_profile}")
            self.set_state(ConnectionState.CONNECTED)
            self.profile_resolved.emit(local_profile)
            return

        # 3. Fetch Community Profile
        db_path = os.path.join("profiles", "community", "database.json")
        if os.path.exists(db_path):
            try:
                with open(db_path, 'r', encoding='utf-8') as f:
                    db = json.load(f)
                vid_pid_str = f"{vid:04X}:{pid:04X}".upper()
                for entry_name, entry_data in db.items():
                    if vid_pid_str in entry_data.get("aliases", []):
                        hid_map_filename = os.path.basename(entry_data.get("hid_map_file", ""))
                        comm_map = os.path.join("profiles", "community", hid_map_filename)
                        if not os.path.exists(comm_map):
                            logger.info(f"Downloading community HID map for {vid_pid_str}...")
                            try:
                                import community_fetcher
                                community_fetcher.fetch_maps_for_devices([(vid, pid)], logger=logger)
                            except Exception as fe:
                                logger.warning(f"Could not auto-download community map: {fe}")
                        
                        if os.path.exists(comm_map):
                            logger.info(f"Using community profile: {comm_map}")
                            self.set_state(ConnectionState.CONNECTED)
                            self.profile_resolved.emit(comm_map)
                            return
            except Exception as e:
                logger.warning(f"Error querying community database: {e}")

        # 4. Failure to find profile -> Launch Native GUI Calibration Wizard
        logger.info(f"No profile found for device {vid:04X}:{pid:04X}. Triggering calibration wizard.")
        self.launch_wizard.emit(device_info)
