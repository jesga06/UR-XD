"""
Advanced Settings & Macros Studio View for PySide6 UI (gui_v2).

Provides hardware-level chord input suppression configuration, synthetic extra button creation,
and Macros Studio sequence editing (one-shot, toggle, hold/loop modes) with interactive recording support.
"""

import json
import os
import logging
from typing import Optional, Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QLineEdit, QComboBox, QRadioButton, QButtonGroup, QScrollArea,
    QMessageBox, QGroupBox, QGridLayout
)
from PySide6.QtCore import Qt, Slot

from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6
from gui_v2.utils.debounced_saver import DebouncedConfigSaver
from gui_v2.dialogs.chords_guide_dialog import ChordsGuideDialog
from gui_v2.dialogs.key_recorder_dialog import KeyRecorderDialog

logger = logging.getLogger("advanced_view")


class AdvancedView(QWidget):
    """
    Advanced View controlling Firmware Hardware Chords (Input Suppression)
    and Macros Studio sequence management.
    """

    def __init__(self, config_manager=None, theme_manager: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.theme_mgr = theme_manager

        # Local state storage for rows
        self.hw_chord_rows: List[Dict[str, QWidget]] = []
        self.macro_rows: List[Dict[str, QWidget]] = []

        # 300ms Debounced Saver for configuration & macros disk updates
        self.debounced_saver = DebouncedConfigSaver(
            save_callback=self.save_advanced_config,
            delay_ms=300,
            parent=self
        )

        self.setup_ui()
        self.load_data()
        self.apply_theme()

        if self.theme_mgr and hasattr(self.theme_mgr, "theme_changed"):
            self.theme_mgr.theme_changed.connect(self._on_theme_changed)

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scroll Area Wrapper
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.NoFrame)

        self.container_widget = QWidget(self.scroll_area)
        self.container_layout = QVBoxLayout(self.container_widget)
        self.container_layout.setContentsMargins(16, 16, 16, 16)
        self.container_layout.setSpacing(20)

        # Page Header
        hdr_layout = QHBoxLayout()
        title_lbl = QLabel("Advanced Settings & Macros Studio", self.container_widget)
        title_lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        hdr_layout.addWidget(title_lbl)
        hdr_layout.addStretch()

        self.container_layout.addLayout(hdr_layout)

        # -------------------------------------------------------------------
        # 1. HARDWARE CHORDS BUILDER (INPUT SUPPRESSION)
        # -------------------------------------------------------------------
        self.hw_card = QGroupBox("Hardware Chords (Input Suppression)", self.container_widget)
        self.hw_card_layout = QVBoxLayout(self.hw_card)
        self.hw_card_layout.setContentsMargins(16, 16, 16, 16)
        self.hw_card_layout.setSpacing(12)

        hw_hdr_layout = QHBoxLayout()
        hw_desc = QLabel(
            "Synthesize virtual extra buttons (M1, M2, L4, R4) from physical button combinations while suppressing base inputs in-game.",
            self.hw_card
        )
        hw_desc.setWordWrap(True)
        hw_hdr_layout.addWidget(hw_desc, stretch=1)

        self.btn_hw_guide = QPushButton("? Hardware Chords Guide", self.hw_card)
        self.btn_hw_guide.setFixedWidth(170)
        self.btn_hw_guide.clicked.connect(self.open_chords_guide)
        hw_hdr_layout.addWidget(self.btn_hw_guide)
        self.hw_card_layout.addLayout(hw_hdr_layout)

        # Backend Mode Notice
        self.lbl_backend_notice = QLabel(self.hw_card)
        self.lbl_backend_notice.setWordWrap(True)
        self.check_backend_mode()
        self.hw_card_layout.addWidget(self.lbl_backend_notice)

        # Container for Hardware Chord Rows
        self.hw_rows_container = QWidget(self.hw_card)
        self.hw_rows_layout = QVBoxLayout(self.hw_rows_container)
        self.hw_rows_layout.setContentsMargins(0, 0, 0, 0)
        self.hw_rows_layout.setSpacing(8)
        self.hw_card_layout.addWidget(self.hw_rows_container)

        # Add Chord Row Action Button
        hw_action_layout = QHBoxLayout()
        self.btn_add_hw = QPushButton("+ Add Hardware Chord", self.hw_card)
        self.btn_add_hw.setFixedWidth(180)
        self.btn_add_hw.clicked.connect(lambda: self.add_hw_chord_row())
        hw_action_layout.addWidget(self.btn_add_hw)
        hw_action_layout.addStretch()
        self.hw_card_layout.addLayout(hw_action_layout)

        self.container_layout.addWidget(self.hw_card)

        # -------------------------------------------------------------------
        # 2. MACROS STUDIO
        # -------------------------------------------------------------------
        self.macros_card = QGroupBox("Macros Studio", self.container_widget)
        self.macros_card_layout = QVBoxLayout(self.macros_card)
        self.macros_card_layout.setContentsMargins(16, 16, 16, 16)
        self.macros_card_layout.setSpacing(12)

        macros_hdr_layout = QHBoxLayout()
        macros_desc = QLabel(
            "Create named macro sequences (keyboard keys, mouse clicks, delays) to map in the Remapping tab using 'macro:Name'.",
            self.macros_card
        )
        macros_desc.setWordWrap(True)
        macros_hdr_layout.addWidget(macros_desc, stretch=1)

        self.btn_macros_guide = QPushButton("? Macros Guide", self.macros_card)
        self.btn_macros_guide.setFixedWidth(150)
        self.btn_macros_guide.clicked.connect(self.open_remapping_guide)
        macros_hdr_layout.addWidget(self.btn_macros_guide)
        self.macros_card_layout.addLayout(macros_hdr_layout)

        # Container for Macro Rows
        self.macro_rows_container = QWidget(self.macros_card)
        self.macro_rows_layout = QVBoxLayout(self.macro_rows_container)
        self.macro_rows_layout.setContentsMargins(0, 0, 0, 0)
        self.macro_rows_layout.setSpacing(10)
        self.macros_card_layout.addWidget(self.macro_rows_container)

        # Add Macro Row Action Button
        macros_action_layout = QHBoxLayout()
        self.btn_add_macro = QPushButton("+ Add Macro", self.macros_card)
        self.btn_add_macro.setFixedWidth(140)
        self.btn_add_macro.clicked.connect(lambda: self.add_macro_row())
        macros_action_layout.addWidget(self.btn_add_macro)
        macros_action_layout.addStretch()
        self.macros_card_layout.addLayout(macros_action_layout)

        self.container_layout.addWidget(self.macros_card)

        # Save Settings Bottom Bar
        save_layout = QHBoxLayout()
        save_layout.addStretch()
        self.btn_save = QPushButton("Save Settings", self.container_widget)
        self.btn_save.setFixedWidth(160)
        self.btn_save.setFixedHeight(36)
        self.btn_save.clicked.connect(self.save_advanced_config_immediate)
        save_layout.addWidget(self.btn_save)

        self.container_layout.addLayout(save_layout)

        self.scroll_area.setWidget(self.container_widget)
        main_layout.addWidget(self.scroll_area)

    def check_backend_mode(self):
        """Checks backend mode and shows warning banner if not in XInput mode."""
        is_xinput = True
        if self.config and hasattr(self.config, "get"):
            mode = self.config.get("DEFAULT", "backend_mode", fallback="xinput").lower()
            if mode != "xinput":
                is_xinput = False

        if not is_xinput:
            self.lbl_backend_notice.setText(
                "⚠️ Hardware Chords are locked because the backend is not in XInput mode.\n"
                "Please use Auto-Detect calibration in Tuning to switch to XInput mode."
            )
            self.lbl_backend_notice.setStyleSheet("color: #FF5555; font-weight: bold; font-size: 12px;")
            self.lbl_backend_notice.show()
        else:
            self.lbl_backend_notice.hide()

    def open_chords_guide(self):
        """Launches ChordsGuideDialog for Hardware Chords topic."""
        dlg = ChordsGuideDialog(theme_manager=self.theme_mgr, topic="hw", parent=self)
        dlg.exec()

    def open_remapping_guide(self):
        """Launches ChordsGuideDialog for Macros Studio topic."""
        dlg = ChordsGuideDialog(theme_manager=self.theme_mgr, topic="std", parent=self)
        dlg.exec()

    # -------------------------------------------------------------------
    # HARDWARE CHORD ROW MANAGEMENT
    # -------------------------------------------------------------------
    def add_hw_chord_row(self, chord_str: str = "", delayed_str: str = "", action_str: str = "", mode_str: str = "auto"):
        """Adds a hardware chord row widget."""
        row_widget = QFrame(self.hw_rows_container)
        row_widget.setFrameShape(QFrame.StyledPanel)
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(8)

        # Chord Entry
        lbl_chord = QLabel("Chord:", row_widget)
        ent_chord = QLineEdit(chord_str, row_widget)
        ent_chord.setPlaceholderText("e.g. lb + start")
        ent_chord.textChanged.connect(self.mark_dirty)

        # Delayed Entry
        lbl_delayed = QLabel("Delayed:", row_widget)
        ent_delayed = QLineEdit(delayed_str, row_widget)
        ent_delayed.setPlaceholderText("e.g. start")
        ent_delayed.setFixedWidth(80)
        ent_delayed.textChanged.connect(self.mark_dirty)

        # Action Entry
        lbl_action = QLabel("Action:", row_widget)
        ent_action = QLineEdit(action_str, row_widget)
        ent_action.setPlaceholderText("e.g. M1 or L4")
        ent_action.setFixedWidth(90)
        ent_action.textChanged.connect(self.mark_dirty)

        # Mode Combo
        lbl_mode = QLabel("Mode:", row_widget)
        combo_mode = QComboBox(row_widget)
        combo_mode.addItems(["auto", "0ms", "50ms", "100ms"])
        idx = combo_mode.findText(mode_str.lower())
        if idx >= 0:
            combo_mode.setCurrentIndex(idx)
        combo_mode.currentTextChanged.connect(self.mark_dirty)

        # Delete Row Button
        btn_del = QPushButton("🗑️", row_widget)
        btn_del.setFixedWidth(32)

        row_layout.addWidget(lbl_chord)
        row_layout.addWidget(ent_chord, stretch=1)
        row_layout.addWidget(lbl_delayed)
        row_layout.addWidget(ent_delayed)
        row_layout.addWidget(lbl_action)
        row_layout.addWidget(ent_action)
        row_layout.addWidget(lbl_mode)
        row_layout.addWidget(combo_mode)
        row_layout.addWidget(btn_del)

        row_data = {
            "widget": row_widget,
            "ent_chord": ent_chord,
            "ent_delayed": ent_delayed,
            "ent_action": ent_action,
            "combo_mode": combo_mode
        }

        btn_del.clicked.connect(lambda: self.remove_hw_chord_row(row_data))

        self.hw_chord_rows.append(row_data)
        self.hw_rows_layout.addWidget(row_widget)
        self.mark_dirty()

    def remove_hw_chord_row(self, row_data: Dict[str, QWidget]):
        """Removes a hardware chord row widget."""
        if row_data in self.hw_chord_rows:
            self.hw_chord_rows.remove(row_data)
            row_data["widget"].deleteLater()
            self.mark_dirty()

    # -------------------------------------------------------------------
    # MACRO ROW MANAGEMENT
    # -------------------------------------------------------------------
    def add_macro_row(self, name_str: str = "", mode_str: str = "one_shot", steps_str: str = ""):
        """Adds a Macro row widget with name, execution mode, steps, and recording button."""
        row_widget = QGroupBox(f"Macro: {name_str if name_str else 'New Macro'}", self.macro_rows_container)
        row_layout = QVBoxLayout(row_widget)
        row_layout.setContentsMargins(10, 8, 10, 8)
        row_layout.setSpacing(8)

        top_layout = QHBoxLayout()

        # Name Entry
        lbl_name = QLabel("Name:", row_widget)
        ent_name = QLineEdit(name_str, row_widget)
        ent_name.setPlaceholderText("e.g. fire_combo")
        ent_name.setFixedWidth(130)
        ent_name.textChanged.connect(lambda t: self._on_macro_name_changed(row_widget, t))

        # Mode Selection Radio Buttons
        lbl_mode = QLabel("Mode:", row_widget)
        btn_group = QButtonGroup(row_widget)

        r_oneshot = QRadioButton("One-shot", row_widget)
        r_toggle = QRadioButton("Toggle", row_widget)
        r_hold = QRadioButton("Hold/Loop", row_widget)

        btn_group.addButton(r_oneshot, 0)
        btn_group.addButton(r_toggle, 1)
        btn_group.addButton(r_hold, 2)

        mode_clean = mode_str.lower()
        if mode_clean == "toggle":
            r_toggle.setChecked(True)
        elif mode_clean == "hold":
            r_hold.setChecked(True)
        else:
            r_oneshot.setChecked(True)

        btn_group.idToggled.connect(lambda id, chk: self.mark_dirty() if chk else None)

        top_layout.addWidget(lbl_name)
        top_layout.addWidget(ent_name)
        top_layout.addWidget(lbl_mode)
        top_layout.addWidget(r_oneshot)
        top_layout.addWidget(r_toggle)
        top_layout.addWidget(r_hold)
        top_layout.addStretch()

        # Delete Macro Button
        btn_del = QPushButton("🗑️ Delete Macro", row_widget)
        btn_del.setFixedWidth(120)
        top_layout.addWidget(btn_del)

        row_layout.addLayout(top_layout)

        # Steps Sequence Input Layout
        steps_layout = QHBoxLayout()
        lbl_steps = QLabel("Steps:", row_widget)
        ent_steps = QLineEdit(steps_str, row_widget)
        ent_steps.setPlaceholderText("e.g. keyboard:shift+a, wait:50ms, mouse:left")
        ent_steps.textChanged.connect(self.mark_dirty)

        # Interactive Record Button
        btn_rec = QPushButton("[Rec]", row_widget)
        btn_rec.setFixedWidth(60)
        btn_rec.setToolTip("Record input keys & clicks interactively")
        btn_rec.clicked.connect(lambda: self.record_macro_steps(ent_steps))

        steps_layout.addWidget(lbl_steps)
        steps_layout.addWidget(ent_steps, stretch=1)
        steps_layout.addWidget(btn_rec)

        row_layout.addLayout(steps_layout)

        row_data = {
            "widget": row_widget,
            "ent_name": ent_name,
            "btn_group": btn_group,
            "r_oneshot": r_oneshot,
            "r_toggle": r_toggle,
            "r_hold": r_hold,
            "ent_steps": ent_steps
        }

        btn_del.clicked.connect(lambda: self.remove_macro_row(row_data))

        self.macro_rows.append(row_data)
        self.macro_rows_layout.addWidget(row_widget)
        self.mark_dirty()

    def _on_macro_name_changed(self, group_box: QGroupBox, text: str):
        """Updates group box title when macro name is typed."""
        group_box.setTitle(f"Macro: {text.strip() if text.strip() else 'New Macro'}")
        self.mark_dirty()

    def remove_macro_row(self, row_data: Dict[str, QWidget]):
        """Removes a Macro row widget."""
        if row_data in self.macro_rows:
            self.macro_rows.remove(row_data)
            row_data["widget"].deleteLater()
            self.mark_dirty()

    def record_macro_steps(self, target_entry: QLineEdit):
        """Launches KeyRecorderDialog to interactively record macro steps."""
        dlg = KeyRecorderDialog("Macro Step", parent=self)
        if dlg.exec() == KeyRecorderDialog.Accepted:
            recorded = dlg.get_recorded_key()
            if recorded:
                current = target_entry.text().strip()
                if current:
                    target_entry.setText(f"{current}, {recorded}")
                else:
                    target_entry.setText(recorded)
                self.mark_dirty()

    # -------------------------------------------------------------------
    # DATA LOADING & PERSISTENCE
    # -------------------------------------------------------------------
    def load_data(self):
        """Loads Hardware Chords and Macros from config and macros.json."""
        # 1. Load Hardware Chords
        if self.config:
            hw_dict = {}
            if hasattr(self.config, "get_hardware_chords"):
                hw_dict = self.config.get_hardware_chords()
            elif hasattr(self.config, "data") and "hardware_chords" in self.config.data:
                hw_dict = self.config.data["hardware_chords"]
            elif hasattr(self.config, "items") and self.config.has_section("hardware_chords"):
                hw_dict = dict(self.config.items("hardware_chords"))

            for key, val in hw_dict.items():
                # Parse format: chord=lb+select; delayed=select; mode=auto; action=l4
                chord_val, delayed_val, action_val, mode_val = "", "", "", "auto"
                if isinstance(val, str) and ";" in val:
                    parts = val.split(";")
                    for p in parts:
                        p = p.strip()
                        if p.startswith("chord="):
                            chord_val = p.split("=", 1)[1]
                        elif p.startswith("delayed="):
                            delayed_val = p.split("=", 1)[1]
                        elif p.startswith("action="):
                            action_val = p.split("=", 1)[1]
                        elif p.startswith("mode="):
                            mode_val = p.split("=", 1)[1]
                else:
                    chord_val = key
                    action_val = str(val)

                self.add_hw_chord_row(chord_val, delayed_val, action_val, mode_val)

        # 2. Load Macros from macros.json
        macros_file = "macros.json"
        if os.path.exists(macros_file):
            try:
                with open(macros_file, "r", encoding="utf-8") as f:
                    macros_data = json.load(f)

                if isinstance(macros_data, dict):
                    for name, m_info in macros_data.items():
                        mode = "one_shot"
                        steps_str = ""
                        if isinstance(m_info, dict):
                            mode = m_info.get("mode", "one_shot")
                            steps = m_info.get("steps", [])
                            if isinstance(steps, list):
                                steps_str = ", ".join(str(s) for s in steps)
                            else:
                                steps_str = str(steps)
                        elif isinstance(m_info, list):
                            steps_str = ", ".join(str(s) for s in m_info)

                        self.add_macro_row(name, mode, steps_str)
            except Exception as e:
                logger.error(f"Error reading macros.json: {e}")

    def mark_dirty(self):
        """Triggers single-shot 300ms debounced disk saver."""
        self.debounced_saver.mark_dirty()

    def save_advanced_config_immediate(self):
        """Flushes and saves configuration immediately with visual user feedback."""
        self.debounced_saver.flush()
        QMessageBox.information(
            self,
            "Settings Saved",
            "Hardware Chords and Macros Studio settings saved successfully!"
        )

    def save_advanced_config(self):
        """Callback executed by DebouncedConfigSaver to batch write config and macros.json."""
        logger.debug("[AdvancedView] Saving Hardware Chords and Macros...")

        # 1. Save Hardware Chords to config
        hw_chords_dict = {}
        for idx, row in enumerate(self.hw_chord_rows):
            chord = row["ent_chord"].text().strip()
            delayed = row["ent_delayed"].text().strip()
            action = row["ent_action"].text().strip()
            mode = row["combo_mode"].currentText().strip()

            if chord and action:
                val_str = f"chord={chord}; delayed={delayed}; mode={mode}; action={action}"
                hw_chords_dict[f"hw_{idx+1}"] = val_str

        if self.config:
            if hasattr(self.config, "set_hardware_chords"):
                self.config.set_hardware_chords(hw_chords_dict)
            elif hasattr(self.config, "data"):
                self.config.data["hardware_chords"] = hw_chords_dict
            if hasattr(self.config, "save"):
                try:
                    self.config.save()
                except Exception as e:
                    logger.error(f"Failed to save config: {e}")

        # 2. Save Macros to macros.json
        macros_dict = {}
        for row in self.macro_rows:
            name = row["ent_name"].text().strip()
            if not name:
                continue

            btn_group = row["btn_group"]
            checked_id = btn_group.checkedId()
            mode = "one_shot"
            if checked_id == 1:
                mode = "toggle"
            elif checked_id == 2:
                mode = "hold"

            steps_raw = row["ent_steps"].text().strip()
            steps_list = [s.strip() for s in steps_raw.split(",") if s.strip()]

            macros_dict[name] = {
                "mode": mode,
                "steps": steps_list
            }

        try:
            with open("macros.json", "w", encoding="utf-8") as f:
                json.dump(macros_dict, f, indent=2)
            logger.debug("[AdvancedView] Saved macros.json successfully.")
        except Exception as e:
            logger.error(f"Failed to save macros.json: {e}")

    # -------------------------------------------------------------------
    # THEME STYLING
    # -------------------------------------------------------------------
    def _on_theme_changed(self, tokens: dict):
        self.apply_theme()

    def apply_theme(self):
        """Applies dynamic QSS using ThemeManager tokens."""
        if not self.theme_mgr:
            return

        bg_col = self.theme_mgr.get_color("background")
        acc1_col = self.theme_mgr.get_color("accent_1")
        acc2_col = self.theme_mgr.get_color("accent_2")

        bg_str = color_to_hex6(bg_col)
        acc1_hex = color_to_hex6(acc1_col)
        acc2_hex = color_to_hex6(acc2_col)

        acc1_bg = color_to_rgba_str(acc1_col, 0.12)
        acc1_hover = color_to_rgba_str(acc1_col, 0.25)
        border1_str = color_to_rgba_str(acc1_col, 0.4)

        acc2_bg = color_to_rgba_str(acc2_col, 0.15)
        acc2_hover = color_to_rgba_str(acc2_col, 0.3)
        border2_str = color_to_rgba_str(acc2_col, 0.5)

        qss = f"""
        QWidget {{
            background-color: {bg_str};
            color: #FFFFFF;
        }}
        QGroupBox {{
            background-color: {color_to_rgba_str(bg_col, 0.6)};
            border: 1.5px solid {border1_str};
            border-radius: 6px;
            margin-top: 10px;
            font-weight: bold;
            font-size: 13px;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 2px 8px;
            color: {acc1_hex};
        }}
        QLineEdit, QComboBox {{
            background-color: {color_to_rgba_str(bg_col, 0.9)};
            border: 1px solid {border1_str};
            border-radius: 4px;
            color: #FFFFFF;
            padding: 4px 8px;
            font-size: 11px;
        }}
        QLineEdit:focus, QComboBox:focus {{
            border: 1px solid {acc1_hex};
        }}
        QPushButton {{
            background-color: {acc1_bg};
            border: 1px solid {border1_str};
            border-radius: 4px;
            color: #FFFFFF;
            padding: 5px 12px;
            font-weight: bold;
            font-size: 11px;
        }}
        QPushButton:hover {{
            background-color: {acc1_hover};
            border-color: {acc1_hex};
        }}
        QRadioButton {{
            color: #EEEEEE;
            font-size: 11px;
        }}
        QRadioButton::indicator:checked {{
            background-color: {acc1_hex};
            border: 2px solid #FFFFFF;
            border-radius: 6px;
        }}
        """
        self.setStyleSheet(qss)

        # Style Save button specially with accent_2 (output)
        save_qss = f"""
        QPushButton {{
            background-color: {acc2_bg};
            border: 1.5px solid {border2_str};
            border-radius: 6px;
            color: #FFFFFF;
            font-weight: bold;
            font-size: 12px;
        }}
        QPushButton:hover {{
            background-color: {acc2_hover};
            border-color: {acc2_hex};
        }}
        """
        self.btn_save.setStyleSheet(save_qss)
