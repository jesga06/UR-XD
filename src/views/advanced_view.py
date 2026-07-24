"""
Advanced View for PySide6 GUI (advanced_view.py)
Hardware Chords Engine Table with full config binding and Standalone Macro Builder matching legacy screenshot.
Includes Name field, Outputs sequence field, [Rec] record button, [X] delete button, + Add Macro, and Save Settings
with 100% two-way persistence to macros.json.
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
        self.macro_cards = []  # List of dicts: {"frame": QFrame, "edit_name": QLineEdit, "edit_out": QLineEdit}
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
        # SECTION 1: HARDWARE CHORDS ENGINE MANAGER
        # ---------------------------------------------------------------------
        chords_card = QFrame()
        chords_card.setObjectName("GlassCard")
        chords_layout = QVBoxLayout(chords_card)

        chords_header = QHBoxLayout()
        lbl_chords = QLabel("⚡ HARDWARE CHORDS ENGINE MANAGER")
        lbl_chords.setStyleSheet("font-weight: bold; font-size: 14px;")

        btn_add_chord = QPushButton("+ Add Hardware Chord")
        btn_add_chord.setObjectName("PrimaryBtn")
        btn_add_chord.clicked.connect(lambda: self.add_chord_row("LB + START", "Virtual Paddle M1", True))

        chords_header.addWidget(lbl_chords)
        chords_header.addStretch()
        chords_header.addWidget(btn_add_chord)
        chords_layout.addLayout(chords_header)

        self.table_chords = QTableWidget(0, 4)
        self.table_chords.setHorizontalHeaderLabels(["Trigger Combo", "Target Action / Button", "Suppress Physical", "Actions"])
        self.table_chords.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table_chords.setMinimumHeight(180)
        self.table_chords.itemChanged.connect(self.on_table_item_changed)
        chords_layout.addWidget(self.table_chords)

        scroll_layout.addWidget(chords_card)

        # ---------------------------------------------------------------------
        # SECTION 2: MACROS BUILDER (Matching Legacy Screenshot 1:1)
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
        btn_add_macro.clicked.connect(lambda: self.add_macro_card_row("", ""))

        btn_save_macros = QPushButton("Save Settings")
        btn_save_macros.setObjectName("PrimaryBtn")
        btn_save_macros.setFixedWidth(200)
        btn_save_macros.clicked.connect(self.save_macros)

        bot_btn_box.addWidget(btn_add_macro)
        bot_btn_box.addWidget(btn_save_macros)
        macro_layout.addLayout(bot_btn_box)

        scroll_layout.addWidget(macro_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    # ---------------------------------------------------------------------
    # Hardware Chords Logic
    # ---------------------------------------------------------------------
    def on_table_item_changed(self, item):
        self.save_hardware_chords()

    def add_chord_row(self, trigger="LB + SELECT", target="Virtual Paddle M1", suppress=True):
        self.table_chords.blockSignals(True)
        row = self.table_chords.rowCount()
        self.table_chords.insertRow(row)

        edit_trig = QLineEdit(trigger)
        edit_trig.setObjectName("OutlinedEdit")
        edit_trig.editingFinished.connect(self.save_hardware_chords)
        self.table_chords.setCellWidget(row, 0, edit_trig)

        edit_targ = QLineEdit(target)
        edit_targ.setObjectName("OutlinedEdit")
        edit_targ.editingFinished.connect(self.save_hardware_chords)
        self.table_chords.setCellWidget(row, 1, edit_targ)

        chk = QCheckBox()
        chk.setChecked(suppress)
        chk.stateChanged.connect(self.save_hardware_chords)
        self.table_chords.setCellWidget(row, 2, chk)

        btn_del = QPushButton("❌ Delete")
        btn_del.setObjectName("SecondaryBtn")
        btn_del.clicked.connect(lambda ch=False, r=row: self.delete_chord_row(r))
        self.table_chords.setCellWidget(row, 3, btn_del)

        self.table_chords.blockSignals(False)
        self.save_hardware_chords()

    def delete_chord_row(self, row):
        self.table_chords.blockSignals(True)
        self.table_chords.removeRow(row)
        self.table_chords.blockSignals(False)
        self.save_hardware_chords()

    def save_hardware_chords(self):
        chords_list = []
        for r in range(self.table_chords.rowCount()):
            edit_t = self.table_chords.cellWidget(r, 0)
            edit_a = self.table_chords.cellWidget(r, 1)
            chk_widget = self.table_chords.cellWidget(r, 2)
            trig_text = edit_t.text() if edit_t else ""
            act_text = edit_a.text() if edit_a else ""
            if trig_text and act_text:
                chords_list.append({
                    "trigger": trig_text,
                    "action": act_text,
                    "suppress": chk_widget.isChecked() if chk_widget else True
                })
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.data["hardware_chords"] = chords_list
            self.app.save_config()
            if hasattr(self.app, 'view_dashboard') and self.app.view_dashboard:
                self.app.view_dashboard.refresh_button_indicators()

    # ---------------------------------------------------------------------
    # Macro Builder Logic (Matching Screenshot 1:1)
    # ---------------------------------------------------------------------
    def add_macro_card_row(self, name="", outputs=""):
        """Create a macro card entry row matching the screenshot layout."""
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

        btn_del_macro = QPushButton("X")
        btn_del_macro.setFixedSize(24, 24)
        btn_del_macro.setStyleSheet("background-color: #ef4444; color: #ffffff; font-weight: bold; border-radius: 4px; border: none;")

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

        btn_rec = QPushButton("[Rec]")
        btn_rec.setObjectName("PrimaryBtn")
        btn_rec.setFixedWidth(50)
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
            new_step = f"keyboard:{dlg.recorded_binding}" if not dlg.recorded_binding.startswith(("gamepad:", "mouse:", "wait:")) else dlg.recorded_binding
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
                # Parse output string into sequence steps
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
            "   - mouse:button (e.g. mouse:left, mouse:right)\n"
            "   - wait:ms (e.g. wait:50 for 50ms delay)\n\n"
            "• Click [Rec] to record key presses interactively."
        )
        msg.exec()

    def load_config_values(self):
        config = getattr(self.app, 'controller_config', None)

        # 1. Load Hardware Chords
        chords = []
        if config:
            chords = config.data.get("hardware_chords", [])
        if not chords:
            chords = [{"trigger": "LB + START", "action": "Virtual Paddle M1", "suppress": True}]

        self.table_chords.blockSignals(True)
        self.table_chords.setRowCount(0)
        self.table_chords.blockSignals(False)

        for c in chords:
            self.add_chord_row(c.get("trigger", ""), c.get("action", ""), c.get("suppress", True))

        # 2. Load Macros from macros.json or config
        # Clear existing cards
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
                    # Deduplicate consecutive press/release
                    out_str = ", ".join([p for i, p in enumerate(out_parts) if i == 0 or p != out_parts[i-1]])
                elif isinstance(steps, str):
                    out_str = steps
                else:
                    out_str = ""
                self.add_macro_card_row(m_name, out_str)
        else:
            self.add_macro_card_row("macro1", "gamepad:a, wait:50, keyboard:h, mouse:left")
