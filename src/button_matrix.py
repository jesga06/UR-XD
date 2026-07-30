"""
Dynamic Button Telemetry Matrix Component for PySide6 UI.
Provides strict separation between standard controller inputs and dynamic extra
hardware buttons, handling real-time button activation illumination, theme token sync, and schema rebuilding.
"""

import sys
import os
import re
from typing import Dict, List, Any, Optional

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
        self.set_active(False)

    def _setup_theme_sync(self) -> None:
        """Connects to ThemeManager.theme_changed signal for live color token updates."""
        try:
            from gui_v2.services.theme_manager import ThemeManager
            ThemeManager.get_instance().theme_changed.connect(self._safe_theme_update)
        except Exception:
            pass

    @Slot(dict)
    def _safe_theme_update(self, tokens: dict = None) -> None:
        try:
            self.update_style()
        except RuntimeError:
            pass

    def set_active(self, active: bool) -> None:
        """Updates styling based on activation state."""
        self._is_active = bool(active)
        self.update_style()

    def update_style(self) -> None:
        """Fetches active color tokens and applies QSS styling."""
        try:
            from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex8
            tm = ThemeManager.get_instance()
            accent_1 = tm.get_color("accent_1")
            bg_color = tm.get_color("background")
        except Exception:
            accent_1 = QColor("#a855f7")
            bg_color = QColor("#161024")

        if self._is_active:
            accent_active_bg = color_to_rgba_str(accent_1, alpha_override=0.65)
            accent_border = color_to_rgba_str(accent_1, alpha_override=1.0)
            self.setStyleSheet(f"""
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
            """)
        else:
            bg_card = color_to_rgba_str(bg_color, alpha_override=0.85)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.25)
            self.setStyleSheet(f"""
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
            """)


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

        header = QLabel("DYNAMIC EXTRA BUTTONS & HARDWARE CHORDS")
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
            val = state_dict.get(key_lower, extra_inputs.get(key_lower, state_dict.get(key_lower.upper(), 0)))
            if isinstance(val, (int, float, bool)):
                is_pressed = bool(val > 0.1 if isinstance(val, float) else val)
            else:
                is_pressed = False
            pill.set_active(is_pressed)


def get_extra_button_actions(config_data: Dict[str, Any]) -> List[str]:
    """
    Extracts human-configured extra button actions (e.g. L4, R4, M1, M2)
    from extra_buttons, settings.extra_inputs, and hardware_chords.
    """
    if not isinstance(config_data, dict):
        return []

    extra_buttons: List[str] = []

    eb_dict = config_data.get("extra_buttons", {})
    if isinstance(eb_dict, dict) and eb_dict:
        for k in eb_dict.keys():
            k_lower = str(k).strip().lower()
            if k_lower and k_lower not in extra_buttons:
                extra_buttons.append(k_lower)
    else:
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

        extra_buttons = get_extra_button_actions(config_data)
        self.extra_array.rebuild_extra_buttons(extra_buttons)
