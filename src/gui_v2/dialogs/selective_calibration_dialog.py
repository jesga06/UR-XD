"""
Selective Calibration Selection Dialog (selective_calibration_dialog.py)
Modal dialog allowing users to pick specific inputs to recalibrate and declare new extra buttons.
"""

import os
from typing import Dict, Any, Optional, List, Set

from PySide6.QtWidgets import (
    QDialog, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QCheckBox, QLineEdit, QPushButton, QLabel, QScrollArea, QFrame
)
from PySide6.QtGui import QFont
from PySide6.QtCore import Qt


class SelectiveCalibrationDialog(QDialog):
    """
    Modal dialog providing checkboxes for all standard and extra controller inputs,
    plus an entry field for typing new extra button names.
    """
    def __init__(self, device_info: dict, existing_profile: Optional[dict] = None, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.device_info = device_info
        self.existing_profile = existing_profile or {}
        self.setWindowTitle("🎯 Selective Input Calibration")
        self.setMinimumSize(560, 520)

        self.checkboxes: Dict[str, QCheckBox] = {}
        self.selected_inputs: List[str] = []
        self.new_extra_buttons: List[str] = []

        self._setup_ui()
        self._setup_theme_sync()

    def _setup_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(14)

        # Header Title
        title = QLabel("🎯 Selective Input Calibration")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        main_layout.addWidget(title)

        subtitle = QLabel("Select specific inputs to recalibrate, or type new extra button names below:")
        subtitle.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px;")
        main_layout.addWidget(subtitle)

        # Scroll Area for Input Selection Grid
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(12)

        # 1. Face Buttons Group
        grp_face = QGroupBox("Face Buttons")
        grp_face_layout = QGridLayout(grp_face)
        face_btns = [("a", "Button A (Bottom)"), ("b", "Button B (Right)"), ("x", "Button X (Left)"), ("y", "Button Y (Top)")]
        for idx, (key, label) in enumerate(face_btns):
            cb = QCheckBox(label)
            self.checkboxes[key] = cb
            grp_face_layout.addWidget(cb, idx // 2, idx % 2)
        container_layout.addWidget(grp_face)

        # 2. Bumpers & Triggers Group
        grp_shoulder = QGroupBox("Bumpers & Triggers")
        grp_shoulder_layout = QGridLayout(grp_shoulder)
        shoulder_btns = [("lb", "LB (Left Bumper)"), ("rb", "RB (Right Bumper)"), ("lt", "LT (Left Trigger)"), ("rt", "RT (Right Trigger)")]
        for idx, (key, label) in enumerate(shoulder_btns):
            cb = QCheckBox(label)
            self.checkboxes[key] = cb
            grp_shoulder_layout.addWidget(cb, idx // 2, idx % 2)
        container_layout.addWidget(grp_shoulder)

        # 3. Thumbsticks Group
        grp_sticks = QGroupBox("Analog Thumbsticks (Requires X & Y Axis)")
        grp_sticks_layout = QGridLayout(grp_sticks)
        stick_btns = [("left_stick", "Left Stick (LX / LY + Radar)"), ("right_stick", "Right Stick (RX / RY + Radar)")]
        for idx, (key, label) in enumerate(stick_btns):
            cb = QCheckBox(label)
            self.checkboxes[key] = cb
            grp_sticks_layout.addWidget(cb, 0, idx)
        container_layout.addWidget(grp_sticks)

        # 4. Stick Clicks & D-Pad Group
        grp_misc = QGroupBox("Stick Clicks, Menu & D-Pad")
        grp_misc_layout = QGridLayout(grp_misc)
        misc_btns = [("l3", "L3 (Left Stick Click)"), ("r3", "R3 (Right Stick Click)"),
                     ("select", "Select / Share"), ("start", "Start / Options"),
                     ("home", "Home / Guide"), ("dpad", "D-Pad UP (Hat Switch)")]
        for idx, (key, label) in enumerate(misc_btns):
            cb = QCheckBox(label)
            self.checkboxes[key] = cb
            grp_misc_layout.addWidget(cb, idx // 2, idx % 2)
        container_layout.addWidget(grp_misc)

        # 5. Existing Extra Buttons Group (Loaded dynamically from profile)
        existing_extras = self._extract_existing_extra_buttons()
        if existing_extras:
            grp_extra = QGroupBox("Existing Extra Buttons")
            grp_extra_layout = QGridLayout(grp_extra)
            for idx, eb in enumerate(existing_extras):
                cb = QCheckBox(f"{eb.upper()} Extra Button")
                self.checkboxes[eb.lower()] = cb
                grp_extra_layout.addWidget(cb, idx // 2, idx % 2)
            container_layout.addWidget(grp_extra)

        scroll.setWidget(container)
        main_layout.addWidget(scroll, 1)

        # 6. Type New Extra Buttons Row
        extra_row = QHBoxLayout()
        extra_label = QLabel("New Extra Buttons:")
        extra_label.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.ent_new_extra_buttons = QLineEdit()
        self.ent_new_extra_buttons.setPlaceholderText("Type extra buttons here (comma-separated): e.g. c, z, p1, p2")
        extra_row.addWidget(extra_label)
        extra_row.addWidget(self.ent_new_extra_buttons, 1)
        main_layout.addLayout(extra_row)

        # Quick Selection Bar
        quick_bar = QHBoxLayout()
        btn_select_all = QPushButton("Select All")
        btn_select_all.clicked.connect(self._select_all)
        btn_clear = QPushButton("Clear Selection")
        btn_clear.clicked.connect(self._clear_selection)
        quick_bar.addWidget(btn_select_all)
        quick_bar.addWidget(btn_clear)
        quick_bar.addStretch()
        main_layout.addLayout(quick_bar)

        # Action Button Row
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_start = QPushButton("🚀 Start Selective Calibration")
        self.btn_start.setDefault(True)
        self.btn_start.clicked.connect(self._on_start_clicked)
        btn_row.addWidget(self.btn_cancel)
        btn_row.addWidget(self.btn_start)
        main_layout.addLayout(btn_row)

    def _extract_existing_extra_buttons(self) -> List[str]:
        try:
            from button_matrix import get_extra_button_actions
            return get_extra_button_actions(self.existing_profile)
        except Exception:
            extras: Set[str] = set()
            eb_dict = self.existing_profile.get("extra_buttons", {})
            if isinstance(eb_dict, dict):
                for k in eb_dict.keys():
                    extras.add(str(k).strip().lower())

            reports = self.existing_profile.get("reports", {})
            standard_keys = {
                'a', 'b', 'x', 'y', 'lb', 'rb', 'lt', 'rt',
                'select', 'start', 'home', 'l3', 'r3',
                'dpad', 'lx', 'ly', 'rx', 'ry'
            }
            if isinstance(reports, dict):
                for r in reports.values():
                    inputs = r.get("inputs", {})
                    if isinstance(inputs, dict):
                        for in_name in inputs.keys():
                            k = str(in_name).strip().lower()
                            if k not in standard_keys:
                                extras.add(k)
            return sorted(list(extras))

    def _select_all(self) -> None:
        for cb in self.checkboxes.values():
            cb.setChecked(True)

    def _clear_selection(self) -> None:
        for cb in self.checkboxes.values():
            cb.setChecked(False)

    def _on_start_clicked(self) -> None:
        self.selected_inputs = [k for k, cb in self.checkboxes.items() if cb.isChecked()]
        raw_extra = self.ent_new_extra_buttons.text().strip().lower()
        if raw_extra:
            self.new_extra_buttons = [x.strip() for x in raw_extra.split(",") if x.strip()]

        standard_keys = {
            'a', 'b', 'x', 'y', 'lb', 'rb', 'lt', 'rt',
            'select', 'start', 'home', 'l3', 'r3',
            'dpad', 'lx', 'ly', 'rx', 'ry', 'left_stick', 'right_stick'
        }
        for k in self.selected_inputs:
            if k not in standard_keys and k not in self.new_extra_buttons:
                self.new_extra_buttons.append(k)

        if not self.selected_inputs and not self.new_extra_buttons:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "No Selection", "Please select at least one input or type a new extra button to calibrate.")
            return

        self.accept()

    def _setup_theme_sync(self) -> None:
        try:
            from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str
            tm = ThemeManager.get_instance()
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")
            bg = tm.get_color("background")

            self.setStyleSheet(f"""
                QDialog {{
                    background-color: {color_to_rgba_str(bg, alpha_override=0.96)};
                    color: #ffffff;
                }}
                QGroupBox {{
                    font-weight: bold;
                    border: 1px solid {color_to_rgba_str(accent_1, alpha_override=0.3)};
                    border-radius: 8px;
                    margin-top: 8px;
                    padding-top: 12px;
                }}
                QGroupBox::title {{
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 4px;
                    color: {accent_1.name()};
                }}
                QCheckBox {{
                    color: #ffffff;
                    font-size: 11px;
                }}
                QLineEdit {{
                    background-color: rgba(255, 255, 255, 0.08);
                    border: 1px solid {color_to_rgba_str(accent_1, alpha_override=0.5)};
                    border-radius: 6px;
                    color: #ffffff;
                    padding: 6px 10px;
                }}
                QPushButton {{
                    background-color: rgba(255, 255, 255, 0.1);
                    border: 1px solid rgba(255, 255, 255, 0.2);
                    border-radius: 6px;
                    color: #ffffff;
                    padding: 6px 14px;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    background-color: {accent_1.name()};
                    color: #000000;
                }}
                QPushButton#btn_start {{
                    background-color: {accent_1.name()};
                    color: #000000;
                }}
            """)
        except Exception:
            pass
