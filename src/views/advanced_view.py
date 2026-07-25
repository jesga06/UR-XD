"""
Advanced View for PySide6 GUI (advanced_view.py)
Hardware Chords Engine Manager matching legacy Screenshot 6 layout (Chord, Delayed, Action, Mode combo, Guide button)
and Standalone Macro Sequence Builder & Recorder matching Screenshot 7 layout.
Includes 100% two-way persistence to config.data and macros.json.
"""

import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox, QCheckBox,
    QPushButton, QSpinBox, QGridLayout, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox, QLineEdit, QDialog
)
from PySide6.QtCore import Qt
from views.remapping_view import KeyRecorderDialog


class AdvancedView(QWidget):
    """
    Advanced Tab View handling hardware chords engine and macro builder.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.chord_cards = []  # List of dicts for chord rows
        self.macro_cards = []  # List of dicts for macro cards
        self.setup_ui()
        self.load_config_values()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)

        # ---------------------------------------------------------------------
        # SECTION 1: HARDWARE CHORDS ENGINE MANAGER (Matching Legacy Screenshot 6 1:1)
        # ---------------------------------------------------------------------
        chords_card = QFrame()
        chords_card.setObjectName("GlassCard")
        chords_layout = QVBoxLayout(chords_card)
        chords_layout.setContentsMargins(16, 14, 16, 14)
        chords_layout.setSpacing(12)

        # Header Row: "Hardware Chords (Input Suppression)" + "? Hardware Chords Guide" button
        chords_header = QHBoxLayout()
        lbl_chords = QLabel("Hardware Chords (Input Suppression)")
        lbl_chords.setStyleSheet("font-weight: bold; font-size: 16px;")

        btn_chords_guide = QPushButton("? Hardware Chords Guide")
        btn_chords_guide.setObjectName("SecondaryBtn")
        btn_chords_guide.setToolTip("Click to view Hardware Chords syntax and delayed chord examples.")
        btn_chords_guide.clicked.connect(self.show_chords_guide)

        chords_header.addWidget(lbl_chords)
        chords_header.addWidget(btn_chords_guide)
        chords_header.addStretch()
        chords_layout.addLayout(chords_header)

        # Container for Chord Rows
        self.chord_items_container = QVBoxLayout()
        self.chord_items_container.setSpacing(10)
        chords_layout.addLayout(self.chord_items_container)

        # Add Hardware Chord Button
        bot_chord_btn_box = QHBoxLayout()
        btn_add_chord = QPushButton("+ Add Hardware Chord")
        btn_add_chord.setObjectName("PrimaryBtn")
        btn_add_chord.setToolTip("Add a new hardware input suppression chord rule.")
        btn_add_chord.clicked.connect(lambda: self.add_chord_card_row("", "", "", "auto"))

        bot_chord_btn_box.addStretch()
        bot_chord_btn_box.addWidget(btn_add_chord)
        bot_chord_btn_box.addStretch()
        chords_layout.addLayout(bot_chord_btn_box)

        scroll_layout.addWidget(chords_card)

        # ---------------------------------------------------------------------
        # SECTION 2: MACROS BUILDER (Matching Legacy Screenshot 7 1:1)
        # ---------------------------------------------------------------------
        macro_card = QFrame()
        macro_card.setObjectName("GlassCard")
        macro_layout = QVBoxLayout(macro_card)
        macro_layout.setContentsMargins(16, 14, 16, 14)
        macro_layout.setSpacing(12)

        # Header Row: "Macros" + "? Macros Guide" button
        macro_header = QHBoxLayout()
        lbl_macro_title = QLabel("Macros")
        lbl_macro_title.setStyleSheet("font-weight: bold; font-size: 16px;")

        btn_macro_guide = QPushButton("? Macros Guide")
        btn_macro_guide.setObjectName("SecondaryBtn")
        btn_macro_guide.setToolTip("Click to view Macro syntax and output formatting guide.")
        btn_macro_guide.clicked.connect(self.show_macros_guide)

        macro_header.addWidget(lbl_macro_title)
        macro_header.addWidget(btn_macro_guide)
        macro_header.addStretch()
        macro_layout.addLayout(macro_header)

        # Container layout for macro items
        self.macro_items_container = QVBoxLayout()
        self.macro_items_container.setSpacing(12)
        macro_layout.addLayout(self.macro_items_container)

        # Action Buttons at Bottom: + Add Macro & Save Settings
        bot_btn_box = QVBoxLayout()
        bot_btn_box.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bot_btn_box.setSpacing(8)

        btn_add_macro = QPushButton("+ Add Macro")
        btn_add_macro.setObjectName("PrimaryBtn")
        btn_add_macro.setFixedWidth(200)
        btn_add_macro.setToolTip("Create a new macro sequence card.")
        btn_add_macro.clicked.connect(lambda: self.add_macro_card_row("", ""))

        btn_save_macros = QPushButton("Save Settings")
        btn_save_macros.setObjectName("PrimaryBtn")
        btn_save_macros.setFixedWidth(200)
        btn_save_macros.setToolTip("Save macro sequences to macros.json.")
        btn_save_macros.clicked.connect(self.save_macros)

        bot_btn_box.addWidget(btn_add_macro)
        bot_btn_box.addWidget(btn_save_macros)
        macro_layout.addLayout(bot_btn_box)

        scroll_layout.addWidget(macro_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    # ---------------------------------------------------------------------
    # Hardware Chords Logic (Matching Screenshot 6)
    # ---------------------------------------------------------------------
    def add_chord_card_row(self, chord="", delayed="", action="", mode="auto"):
        """Create a hardware chord row card matching Screenshot 6 layout."""
        card_frame = QFrame()
        card_frame.setStyleSheet("background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 6px;")
        row_layout = QHBoxLayout(card_frame)
        row_layout.setContentsMargins(8, 6, 8, 6)
        row_layout.setSpacing(8)

        # 1. Chord: [ QLineEdit: e.g. dpad_up ]
        lbl_c = QLabel("Chord:")
        edit_c = QLineEdit()
        edit_c.setObjectName("OutlinedEdit")
        edit_c.setPlaceholderText("e.g. dpad_up")
        edit_c.setText(chord)
        edit_c.setToolTip("Primary chord button trigger combo (e.g. dpad_up, lb+start).")
        edit_c.editingFinished.connect(self.save_hardware_chords)

        # 2. Delayed: [ QLineEdit: e.g. dpad_left ]
        lbl_d = QLabel("Delayed:")
        edit_d = QLineEdit()
        edit_d.setObjectName("OutlinedEdit")
        edit_d.setPlaceholderText("e.g. dpad_left")
        edit_d.setText(delayed)
        edit_d.setToolTip("Optional secondary delayed button trigger.")
        edit_d.editingFinished.connect(self.save_hardware_chords)

        # 3. Action: [ QLineEdit: e.g. M1 ]
        lbl_a = QLabel("Action:")
        edit_a = QLineEdit()
        edit_a.setObjectName("OutlinedEdit")
        edit_a.setPlaceholderText("e.g. M1")
        edit_a.setText(action)
        edit_a.setToolTip("Target paddle action or remapped button output (e.g. M1, L4, macro:combo1).")
        edit_a.editingFinished.connect(self.save_hardware_chords)

        # 4. Mode: [ Dropdown: auto, 0ms, 50ms, 100ms ]
        lbl_m = QLabel("Mode:")
        combo_m = QComboBox()
        combo_m.addItems(["auto", "0ms", "50ms", "100ms"])
        combo_m.setCurrentText(mode if mode in ["auto", "0ms", "50ms", "100ms"] else "auto")
        combo_m.setToolTip("Chord suppression timing mode (auto detection or explicit delay).")
        combo_m.currentTextChanged.connect(self.save_hardware_chords)

        # 5. [X] Delete Button
        btn_del = QPushButton("X")
        btn_del.setFixedSize(24, 24)
        btn_del.setStyleSheet("background-color: #ef4444; color: #ffffff; font-weight: bold; border-radius: 4px; border: none;")
        btn_del.setToolTip("Delete this hardware chord rule.")

        row_layout.addWidget(lbl_c)
        row_layout.addWidget(edit_c)
        row_layout.addWidget(lbl_d)
        row_layout.addWidget(edit_d)
        row_layout.addWidget(lbl_a)
        row_layout.addWidget(edit_a)
        row_layout.addWidget(lbl_m)
        row_layout.addWidget(combo_m)
        row_layout.addWidget(btn_del)

        card_dict = {
            "frame": card_frame,
            "edit_c": edit_c,
            "edit_d": edit_d,
            "edit_a": edit_a,
            "combo_m": combo_m
        }
        btn_del.clicked.connect(lambda: self.remove_chord_card_row(card_dict))

        self.chord_cards.append(card_dict)
        self.chord_items_container.addWidget(card_frame)
        self.save_hardware_chords()

    def remove_chord_card_row(self, card_dict):
        if card_dict in self.chord_cards:
            self.chord_cards.remove(card_dict)
            card_dict["frame"].setParent(None)
            card_dict["frame"].deleteLater()
            self.save_hardware_chords()

    def save_hardware_chords(self):
        chords_list = []
        for c in self.chord_cards:
            trig_val = c["edit_c"].text().strip()
            del_val = c["edit_d"].text().strip()
            act_val = c["edit_a"].text().strip()
            mode_val = c["combo_m"].currentText()
            if trig_val and act_val:
                chords_list.append({
                    "trigger": trig_val,
                    "delayed": del_val,
                    "action": act_val,
                    "mode": mode_val,
                    "suppress": True
                })
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.data["hardware_chords"] = chords_list
            self.app.save_config()
            if hasattr(self.app, 'view_dashboard') and self.app.view_dashboard:
                self.app.view_dashboard.refresh_button_indicators()

    def show_chords_guide(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Hardware Chords Guide")
        msg.setText(
            "• Hardware Chords Syntax & Suppression:\n\n"
            "   - Chord: Primary trigger combo (e.g. dpad_up, lb+start)\n"
            "   - Delayed: Optional secondary trigger pressed in sequence (e.g. dpad_left)\n"
            "   - Action: Target paddle or remapped button output (e.g. M1, L4, R4)\n"
            "   - Mode: Timing mode:\n"
            "       • auto: Automatically detects chord press timing\n"
            "       • 0ms / 50ms / 100ms: Explicit suppression window delay\n\n"
            "• Hardware chords suppress physical inputs while emitting the target action."
        )
        msg.exec()

    # ---------------------------------------------------------------------
    # Macro Builder Logic (Matching Screenshot 7)
    # ---------------------------------------------------------------------
    def add_macro_card_row(self, name="", outputs=""):
        """Create a macro card entry row matching Screenshot 7 layout."""
        card_frame = QFrame()
        card_frame.setStyleSheet("background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 8px; padding: 8px;")
        layout = QVBoxLayout(card_frame)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(6)

        # Row 1: Name: [ QLineEdit: e.g. macro1 ] ... [X] Red Delete Button
        row1 = QHBoxLayout()
        lbl_name = QLabel("Name:")
        lbl_name.setFixedWidth(60)

        edit_name = QLineEdit()
        edit_name.setObjectName("OutlinedEdit")
        edit_name.setPlaceholderText("e.g. macro1")
        edit_name.setText(name)
        edit_name.setToolTip("Unique identifier name for this macro sequence.")

        btn_del_macro = QPushButton("X")
        btn_del_macro.setFixedSize(24, 24)
        btn_del_macro.setStyleSheet("background-color: #ef4444; color: #ffffff; font-weight: bold; border-radius: 4px; border: none;")
        btn_del_macro.setToolTip("Delete this macro card.")

        row1.addWidget(lbl_name)
        row1.addWidget(edit_name)
        row1.addWidget(btn_del_macro)
        layout.addLayout(row1)

        # Row 2: Outputs: [ QLineEdit: e.g. gamepad:a, wait:50, keyboard:h, mouse:left ] [Rec]
        row2 = QHBoxLayout()
        lbl_out = QLabel("Outputs:")
        lbl_out.setFixedWidth(60)

        edit_out = QLineEdit()
        edit_out.setObjectName("OutlinedEdit")
        edit_out.setPlaceholderText("e.g. gamepad:a, wait:50, keyboard:h, mouse:left")
        edit_out.setText(outputs)
        edit_out.setToolTip("Comma-separated list of output steps (gamepad, keyboard, mouse, wait:ms).")

        btn_rec = QPushButton("[Rec]")
        btn_rec.setObjectName("PrimaryBtn")
        btn_rec.setFixedWidth(50)
        btn_rec.setToolTip("Record input steps interactively.")
        btn_rec.clicked.connect(lambda: self.record_for_macro(edit_out))

        row2.addWidget(lbl_out)
        row2.addWidget(edit_out)
        row2.addWidget(btn_rec)
        layout.addLayout(row2)

        card_dict = {
            "frame": card_frame,
            "edit_name": edit_name,
            "edit_out": edit_out
        }
        btn_del_macro.clicked.connect(lambda: self.remove_macro_card_row(card_dict))

        self.macro_cards.append(card_dict)
        self.macro_items_container.addWidget(card_frame)

    def remove_macro_card_row(self, card_dict):
        if card_dict in self.macro_cards:
            self.macro_cards.remove(card_dict)
            card_dict["frame"].setParent(None)
            card_dict["frame"].deleteLater()

    def record_for_macro(self, target_edit: QLineEdit):
        dlg = KeyRecorderDialog("Macro Step", self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.recorded_binding:
            curr = target_edit.text().strip()
            new_step = f"keyboard:{dlg.recorded_binding}" if not dlg.recorded_binding.startswith(("gamepad:", "mouse:", "wait:", "scroll_")) else dlg.recorded_binding
            if curr:
                target_edit.setText(f"{curr}, {new_step}")
            else:
                target_edit.setText(new_step)

    def save_macros(self):
        """Serialize all macro card entries to macros.json and save to disk."""
        macros_dict = {}
        for c in self.macro_cards:
            m_name = c["edit_name"].text().strip()
            m_out = c["edit_out"].text().strip()
            if m_name and m_out:
                steps = []
                parts = [p.strip() for p in m_out.split(",") if p.strip()]
                for p in parts:
                    if ":" in p:
                        stype, sval = p.split(":", 1)
                        if stype == "wait":
                            try:
                                steps.append({"type": "wait", "delay": float(sval) / 1000.0})
                            except ValueError:
                                steps.append({"type": "wait", "delay": 0.05})
                        else:
                            steps.append({"type": "key_press", "key": sval, "delay": 0.05})
                            steps.append({"type": "key_release", "key": sval, "delay": 0.05})
                    else:
                        steps.append({"type": "key_press", "key": p, "delay": 0.05})
                        steps.append({"type": "key_release", "key": p, "delay": 0.05})
                macros_dict[m_name] = steps

        try:
            with open("macros.json", "w", encoding="utf-8") as f:
                json.dumps(macros_dict, indent=2)
                f.write(json.dumps(macros_dict, indent=2))

            config = getattr(self.app, 'controller_config', None)
            if config:
                config.data["macros"] = macros_dict
                self.app.save_config()

            QMessageBox.information(self, "Save Settings", f"✓ Saved {len(macros_dict)} macro sequences to macros.json.")
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"❌ Failed to save macros: {e}")

    def show_macros_guide(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Macros Guide")
        msg.setText(
            "• Format macro outputs separated by commas:\n"
            "   e.g. gamepad:a, wait:50, keyboard:h, mouse:left\n\n"
            "• Step Types:\n"
            "   - gamepad:button (e.g. gamepad:a, gamepad:lb)\n"
            "   - keyboard:key (e.g. keyboard:space, keyboard:h)\n"
            "   - mouse:button (e.g. mouse_left, mouse_right)\n"
            "   - wait:ms (e.g. wait:50 for 50ms delay)\n\n"
            "• Click [Rec] to record key presses interactively."
        )
        msg.exec()

    def load_config_values(self):
        config = getattr(self.app, 'controller_config', None)

        # 1. Load Hardware Chords into Card Rows
        for c in list(self.chord_cards):
            self.remove_chord_card_row(c)

        chords = []
        if config:
            chords = config.data.get("hardware_chords", [])
        if not chords:
            chords = [{"trigger": "LB + START", "delayed": "", "action": "Virtual Paddle M1", "mode": "auto"}]

        for c in chords:
            self.add_chord_card_row(
                c.get("trigger", ""),
                c.get("delayed", ""),
                c.get("action", ""),
                c.get("mode", "auto")
            )

        # 2. Load Macros from macros.json or config
        for c in list(self.macro_cards):
            self.remove_macro_card_row(c)

        loaded_macros = {}
        if os.path.exists("macros.json"):
            try:
                with open("macros.json", "r", encoding="utf-8") as f:
                    loaded_macros = json.load(f)
            except Exception:
                pass

        if not loaded_macros and config:
            loaded_macros = config.data.get("macros", {})

        if loaded_macros:
            for m_name, steps in loaded_macros.items():
                out_parts = []
                if isinstance(steps, list):
                    for st in steps:
                        st_type = st.get("type", "")
                        if st_type == "wait":
                            ms = int(st.get("delay", 0.05) * 1000)
                            out_parts.append(f"wait:{ms}")
                        elif st_type == "key_press":
                            out_parts.append(f"{st.get('key', '')}")
                    out_str = ", ".join([p for i, p in enumerate(out_parts) if i == 0 or p != out_parts[i-1]])
                elif isinstance(steps, str):
                    out_str = steps
                else:
                    out_str = ""
                self.add_macro_card_row(m_name, out_str)
        else:
            self.add_macro_card_row("macro1", "gamepad:a, wait:50, keyboard:h, mouse:left")
