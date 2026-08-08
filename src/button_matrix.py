"""
Dynamic Button Telemetry Matrix Component for PySide6 UI.
Provides strict separation between standard controller inputs and dynamic extra
hardware buttons, handling real-time button activation illumination, theme token sync, and schema rebuilding.
"""

import sys
import os
import re
import json
from typing import Dict, List, Any, Optional

STANDARD_INPUT_KEYS = {
    'a', 'b', 'x', 'y', 'lb', 'rb', 'lt', 'rt',
    'select', 'start', 'home', 'l3', 'r3',
    'dpad_up', 'dpad_down', 'dpad_left', 'dpad_right', 'dpad',
    'lx', 'ly', 'rx', 'ry'
}


from PySide6.QtWidgets import (
    QWidget, QApplication, QVBoxLayout, QHBoxLayout, QGridLayout,
    QFrame, QLabel, QGroupBox
)
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt, Slot


class ButtonPill(QFrame):
    """
    Individual button indicator pill widget with dynamic ThemeManager token styling for active and inactive states.
    """
    def __init__(self, key_name: str, display_name: Optional[str] = None, parent=None):
        super().__init__(parent)
        self.key_name: str = key_name.lower()
        self.display_name: str = (display_name or key_name).upper()
        self._is_active: bool = False

        self.setMinimumSize(52, 32)
        self.setObjectName("button_pill")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 2, 4, 2)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel(self.display_name)
        self.label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.label)

        self._setup_theme_sync()
        self.apply_style()


    def _setup_theme_sync(self) -> None:
        """Connects to ThemeManager.theme_changed and staging_changed signals for live color token updates."""
        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            tm.theme_changed.connect(self._safe_theme_update)
            tm.staging_changed.connect(self._safe_theme_update)
            self._update_qss_cache()
        except Exception:
            self._fallback_qss_cache()

    def _fallback_qss_cache(self) -> None:
        accent_1 = QColor("#a855f7")
        bg_color = QColor("#161024")
        self._rebuild_qss(bg_color, accent_1)

    @Slot(dict)
    def _safe_theme_update(self, tokens: dict = None) -> None:
        try:
            self._update_qss_cache()
            self.apply_style()
        except RuntimeError:
            pass

    def _update_qss_cache(self) -> None:
        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            accent_1 = tm.get_color("accent_1")
            bg_color = tm.get_color("background")
            self._rebuild_qss(bg_color, accent_1)
        except Exception:
            self._fallback_qss_cache()

    def _rebuild_qss(self, bg_color: QColor, accent_1: QColor) -> None:
        from gui_v2.services.theme_manager import color_to_rgba_str
        accent_active_bg = color_to_rgba_str(accent_1, alpha_override=0.65)
        accent_border = color_to_rgba_str(accent_1, alpha_override=1.0)
        self._active_qss = f"""
            QFrame#button_pill {{
                background-color: {accent_active_bg};
                border: 1.5px solid {accent_border};
                border-radius: 6px;
            }}
            QLabel {{
                color: #ffffff;
                font-weight: bold;
                font-size: 11px;
            }}
        """
        bg_card = color_to_rgba_str(bg_color, alpha_override=0.85)
        border_glass = color_to_rgba_str(accent_1, alpha_override=0.25)
        self._inactive_qss = f"""
            QFrame#button_pill {{
                background-color: {bg_card};
                border: 1px solid {border_glass};
                border-radius: 6px;
            }}
            QLabel {{
                color: rgba(255, 255, 255, 0.55);
                font-weight: bold;
                font-size: 11px;
            }}
        """

    def set_active(self, active: bool) -> None:
        """Updates styling only when activation state actually changes."""
        new_active = bool(active)
        if self._is_active == new_active:
            return
        self._is_active = new_active
        self.apply_style()

    def apply_style(self) -> None:
        """Applies pre-cached QSS stylesheet string."""
        if not hasattr(self, '_active_qss'):
            self._update_qss_cache()
        if self._is_active:
            self.setStyleSheet(self._active_qss)
        else:
            self.setStyleSheet(self._inactive_qss)



class StandardButtonArray(QFrame):
    """
    Fixed structural grid widget containing standardized controller inputs.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glass_card")
        self.pills: Dict[str, ButtonPill] = {}
        self._setup_ui()
        self._setup_theme_sync()

    def _setup_theme_sync(self) -> None:
        try:
            from gui_v2.services.theme_manager import ThemeManager
            ThemeManager.get_instance().theme_changed.connect(self._safe_theme_update)
            self.update_card_style()
        except Exception:
            pass

    @Slot(dict)
    def _safe_theme_update(self, tokens: dict = None) -> None:
        try:
            self.update_card_style()
        except RuntimeError:
            pass

    def update_card_style(self) -> None:
        try:
            from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str
            tm = ThemeManager.get_instance()
            bg_color = tm.get_color("background")
            accent_1 = tm.get_color("accent_1")
            bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)
            self.setStyleSheet(f"""
                QFrame#glass_card {{
                    background-color: {bg_glass};
                    border: 1px solid {border_glass};
                    border-radius: 12px;
                }}
            """)
        except Exception:
            pass

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 10, 12, 10)

        header = QLabel("STANDARD INPUTS")
        header.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-weight: bold; font-size: 10px;")
        main_layout.addWidget(header)

        grid = QGridLayout()
        grid.setSpacing(6)

        standard_buttons = [
            # Row 0: Face Buttons
            ("a", "A", 0, 0), ("b", "B", 0, 1), ("x", "X", 0, 2), ("y", "Y", 0, 3),
            # Row 1: Bumpers & Triggers
            ("lb", "LB", 1, 0), ("rb", "RB", 1, 1), ("lt", "LT", 1, 2), ("rt", "RT", 1, 3),
            # Row 2: D-Pad
            ("dpad_up", "DP-UP", 2, 0), ("dpad_down", "DP-DN", 2, 1),
            ("dpad_left", "DP-LT", 2, 2), ("dpad_right", "DP-RT", 2, 3),
            # Row 3: System & Stick Clicks
            ("select", "SELECT", 3, 0), ("start", "START", 3, 1),
            ("home", "HOME", 3, 2), ("l3", "L3", 3, 3), ("r3", "R3", 4, 0)
        ]

        for key, disp, r, c in standard_buttons:
            pill = ButtonPill(key, disp)
            self.pills[key] = pill
            grid.addWidget(pill, r, c)

        main_layout.addLayout(grid)

    def update_states(self, state_dict: Dict[str, Any]) -> None:
        """Updates button pill active states based on incoming state dictionary."""
        for key, pill in self.pills.items():
            val = state_dict.get(key, 0)
            if isinstance(val, (int, float, bool)):
                is_pressed = bool(val > 0.1 if isinstance(val, float) else val)
            else:
                is_pressed = False
            pill.set_active(is_pressed)


class ExtraButtonArray(QFrame):
    """
    Fully independent, dynamic container widget for extra hardware buttons and hardware chords.
    Automatically collapses (setVisible(False)) when zero extra buttons are configured.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("glass_card")
        self.pills: Dict[str, ButtonPill] = {}
        self.container_layout: Optional[QHBoxLayout] = None
        self._setup_ui()
        self._setup_theme_sync()

    def _setup_theme_sync(self) -> None:
        try:
            from gui_v2.services.theme_manager import ThemeManager
            ThemeManager.get_instance().theme_changed.connect(self._safe_theme_update)
            self.update_card_style()
        except Exception:
            pass

    @Slot(dict)
    def _safe_theme_update(self, tokens: dict = None) -> None:
        try:
            self.update_card_style()
        except RuntimeError:
            pass

    def update_card_style(self) -> None:
        try:
            from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str
            tm = ThemeManager.get_instance()
            bg_color = tm.get_color("background")
            accent_1 = tm.get_color("accent_1")
            bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)
            self.setStyleSheet(f"""
                QFrame#glass_card {{
                    background-color: {bg_glass};
                    border: 1.5px solid {border_glass};
                    border-radius: 12px;
                }}
            """)
        except Exception:
            pass

    def _setup_ui(self) -> None:
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(12, 10, 12, 10)

        header = QLabel("EXTRA BUTTONS")
        header.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-weight: bold; font-size: 10px;")
        self.main_layout.addWidget(header)

        self.button_box = QWidget()
        self.container_layout = QHBoxLayout(self.button_box)
        self.container_layout.setContentsMargins(0, 4, 0, 4)
        self.container_layout.setSpacing(8)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.main_layout.addWidget(self.button_box)
        self.setVisible(False)

    @Slot(list)
    def rebuild_extra_buttons(self, extra_button_list: List[str]) -> None:
        """Cleans up existing dynamic widgets and builds new pills."""
        for pill in self.pills.values():
            pill.setParent(None)
            pill.deleteLater()
        self.pills.clear()

        normalized_list = [btn.strip() for btn in extra_button_list if btn.strip()]

        if not normalized_list:
            self.setVisible(False)
            return

        for btn_name in normalized_list:
            key_lower = btn_name.lower()
            pill = ButtonPill(key_lower, btn_name.upper())
            self.pills[key_lower] = pill
            if self.container_layout:
                self.container_layout.addWidget(pill)

        self.setVisible(True)

    def update_states(self, state_dict: Dict[str, Any]) -> None:
        """Updates extra button pill active states based on state dictionary."""
        if not self.isVisible():
            return

        extra_inputs = state_dict.get("extra_inputs", {})
        if not isinstance(extra_inputs, dict):
            extra_inputs = {}

        for key_lower, pill in self.pills.items():
            val = state_dict.get(
                key_lower,
                extra_inputs.get(
                    key_lower,
                    state_dict.get(
                        key_lower.upper(),
                        extra_inputs.get(key_lower.upper(), 0)
                    )
                )
            )
            if isinstance(val, (int, float, bool)):
                is_pressed = bool(val > 0.1 if isinstance(val, float) else val)
            else:
                is_pressed = False
            pill.set_active(is_pressed)


def get_extra_button_actions(config_data: Dict[str, Any], hid_map_path: Optional[str] = None, backend_mode: Optional[str] = None) -> List[str]:
    """
    Extracts human-configured extra button actions (e.g. L4, R4, M1, M2)
    from extra_buttons, settings.extra_inputs, hardware_chords, and HID descriptor maps.
    """
    if not isinstance(config_data, dict):
        config_data = {}

    extra_buttons: List[str] = []

    eb_dict = config_data.get("extra_buttons", {})
    if isinstance(eb_dict, dict) and eb_dict:
        for k in eb_dict.keys():
            k_lower = str(k).strip().lower()
            if k_lower and k_lower not in extra_buttons:
                extra_buttons.append(k_lower)

    eb_settings = config_data.get("settings", {}).get("extra_inputs", [])
    if isinstance(eb_settings, list):
        for x in eb_settings:
            x_lower = str(x).strip().lower()
            if x_lower and x_lower not in extra_buttons:
                extra_buttons.append(x_lower)
    elif isinstance(eb_settings, dict):
        for k in eb_settings.keys():
            k_lower = str(k).strip().lower()
            if k_lower and k_lower not in extra_buttons:
                extra_buttons.append(k_lower)

    # Determine backend mode
    resolved_backend_mode = backend_mode
    if not resolved_backend_mode or resolved_backend_mode == "auto":
        resolved_backend_mode = str(config_data.get("backend", {}).get("mode", "auto")).lower()
    else:
        resolved_backend_mode = str(resolved_backend_mode).lower()

    if resolved_backend_mode in ("auto", "xinput"):
        if os.path.exists("status.json"):
            try:
                with open("status.json", "r", encoding="utf-8") as f:
                    status_data = json.load(f)
                    rt_mode = status_data.get("backend_mode")
                    if rt_mode:
                        resolved_backend_mode = str(rt_mode).lower()
            except Exception:
                pass

    if resolved_backend_mode != "dinput":
        hw_chords = config_data.get("hardware_chords", {})
        chord_items = []
        if isinstance(hw_chords, dict):
            chord_items = list(hw_chords.values())
        elif isinstance(hw_chords, list):
            chord_items = hw_chords

        for item in chord_items:
            action_name = None
            if isinstance(item, dict):
                action_name = item.get("action")
            elif isinstance(item, str):
                m = re.search(r"action\s*=\s*([^;]+)", item, re.IGNORECASE)
                if m:
                    action_name = m.group(1).strip()

            if action_name:
                act_lower = str(action_name).strip().lower()
                if act_lower and act_lower not in extra_buttons:
                    extra_buttons.append(act_lower)

    # Inspect active controller HID map to discover hardware DInput extra buttons (e.g. l4, r4)
    hid_map_paths_to_check = []
    if hid_map_path and os.path.exists(hid_map_path):
        hid_map_paths_to_check.append(hid_map_path)

    if os.path.exists('config.ini'):
        try:
            import configparser
            cp = configparser.ConfigParser()
            cp.read('config.ini', encoding='utf-8')
            lp = cp.get('controller', 'last_profile', fallback='')
            if lp and os.path.exists(lp) and lp not in hid_map_paths_to_check:
                hid_map_paths_to_check.append(lp)
        except Exception:
            pass

    for map_file in hid_map_paths_to_check:
        try:
            with open(map_file, 'r', encoding='utf-8') as f:
                map_json = json.load(f)
                reports = map_json.get("reports", {})
                if isinstance(reports, dict):
                    for rep in reports.values():
                        if isinstance(rep, dict):
                            inputs = rep.get("inputs", {})
                            if isinstance(inputs, dict):
                                for input_name in inputs.keys():
                                    inp_lower = str(input_name).strip().lower()
                                    if (inp_lower and
                                            inp_lower not in STANDARD_INPUT_KEYS and
                                            inp_lower not in extra_buttons):
                                        extra_buttons.append(inp_lower)
        except Exception:
            pass

    return extra_buttons


class ButtonMatrix(QWidget):
    """
    Master widget containing StandardButtonArray and ExtraButtonArray inside a vertical layout.
    """
    def __init__(self, parent=None):
        super().__init__(parent)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(10)

        self.standard_array = StandardButtonArray(self)
        self.extra_array = ExtraButtonArray(self)

        main_layout.addWidget(self.standard_array)
        main_layout.addWidget(self.extra_array)

    @Slot(dict)
    def update_button_states(self, state_dict: Dict[str, Any]) -> None:
        """Receives ControllerState or telemetry dict and illuminates matching buttons."""
        self.standard_array.update_states(state_dict)
        self.extra_array.update_states(state_dict)

    def load_profile_schema(self, config_obj: Any, backend_mode: str = "auto") -> None:
        """Parses configuration object and rebuilds ExtraButtonArray."""
        config_data = {}
        if hasattr(config_obj, 'data') and isinstance(config_obj.data, dict):
            config_data = config_obj.data
        elif isinstance(config_obj, dict):
            config_data = config_obj

        extra_buttons = get_extra_button_actions(config_data, backend_mode=backend_mode)
        self.extra_array.rebuild_extra_buttons(extra_buttons)
