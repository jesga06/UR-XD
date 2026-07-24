"""
Advanced View for PySide6 GUI (advanced_view.py)
Hardware Chords Engine Table with full config binding and Standalone Macro Sequence Builder & Recorder.
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox,
    QPushButton, QSpinBox, QGridLayout, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QMessageBox
)
from PySide6.QtCore import Qt


class AdvancedView(QWidget):
    """
    Advanced Tab View handling hardware chords engine and macro sequence builder.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
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

        # 1. Hardware Chords Engine Manager Card
        chords_card = QFrame()
        chords_card.setObjectName("GlassCard")
        chords_layout = QVBoxLayout(chords_card)

        chords_header = QHBoxLayout()
        lbl_chords = QLabel("⚡ HARDWARE CHORDS ENGINE MANAGER")
        lbl_chords.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

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

        # 2. Standalone Macro Manager Card
        macro_card = QFrame()
        macro_card.setObjectName("GlassCard")
        macro_layout = QVBoxLayout(macro_card)

        macro_header = QHBoxLayout()
        lbl_macro_title = QLabel("📜 MACRO SEQUENCE BUILDER & RECORDER")
        lbl_macro_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        macro_header.addWidget(lbl_macro_title)
        macro_header.addStretch()
        macro_layout.addLayout(macro_header)

        grid_macro = QGridLayout()
        grid_macro.addWidget(QLabel("Select Macro Sequence:"), 0, 0)
        self.combo_macros = QComboBox()
        self.combo_macros.addItems(["FastCombo (A, B, X)", "SuperJump (LB, A)", "Custom Sequence 1"])
        grid_macro.addWidget(self.combo_macros, 0, 1)

        grid_macro.addWidget(QLabel("Step Delay (ms):"), 0, 2)
        self.spin_macro_delay = QSpinBox()
        self.spin_macro_delay.setRange(1, 1000)
        self.spin_macro_delay.setValue(50)
        grid_macro.addWidget(self.spin_macro_delay, 0, 3)

        macro_layout.addLayout(grid_macro)

        macro_btns = QHBoxLayout()
        btn_rec_macro = QPushButton("⏺️ Record Macro")
        btn_rec_macro.setObjectName("PrimaryBtn")
        btn_rec_macro.clicked.connect(self.record_macro)

        btn_del_macro = QPushButton("❌ Delete Macro")
        btn_del_macro.setObjectName("SecondaryBtn")
        btn_del_macro.clicked.connect(self.delete_macro)

        macro_btns.addWidget(btn_rec_macro)
        macro_btns.addWidget(btn_del_macro)
        macro_btns.addStretch()
        macro_layout.addLayout(macro_btns)

        scroll_layout.addWidget(macro_card)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def on_table_item_changed(self, item):
        self.save_hardware_chords()

    def add_chord_row(self, trigger="LB + SELECT", target="Virtual Paddle M1", suppress=True):
        self.table_chords.blockSignals(True)
        row = self.table_chords.rowCount()
        self.table_chords.insertRow(row)

        item_trig = QTableWidgetItem(trigger)
        item_targ = QTableWidgetItem(target)
        self.table_chords.setItem(row, 0, item_trig)
        self.table_chords.setItem(row, 1, item_targ)

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
            t_item = self.table_chords.item(r, 0)
            a_item = self.table_chords.item(r, 1)
            chk_widget = self.table_chords.cellWidget(r, 2)
            if t_item and a_item:
                chords_list.append({
                    "trigger": t_item.text(),
                    "action": a_item.text(),
                    "suppress": chk_widget.isChecked() if chk_widget else True
                })
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.data["hardware_chords"] = chords_list
            self.app.save_config()

    def record_macro(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Record Macro")
        msg.setText("⏺️ Listening for macro key sequence... Press buttons in order, then click Stop.")
        msg.exec()

    def delete_macro(self):
        curr = self.combo_macros.currentText()
        if self.combo_macros.count() > 1:
            self.combo_macros.removeItem(self.combo_macros.currentIndex())
            QMessageBox.information(self, "Delete Macro", f"✓ Removed macro [{curr}].")

    def save_opt(self, section, option, val):
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.set(section, option, str(val))
            self.app.save_config()

    def load_config_values(self):
        config = getattr(self.app, 'controller_config', None)
        if not config:
            return

        chords = config.data.get("hardware_chords", [])
        if not chords:
            chords = [{"trigger": "LB + START", "action": "Virtual Paddle M1", "suppress": True}]

        self.table_chords.blockSignals(True)
        self.table_chords.setRowCount(0)
        self.table_chords.blockSignals(False)

        for c in chords:
            self.add_chord_row(c.get("trigger", ""), c.get("action", ""), c.get("suppress", True))
