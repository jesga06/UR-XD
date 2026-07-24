"""
Remapping View for PySide6 GUI (remapping_view.py)
Button remapping matrix cards, key combo recorder modal, macro editor table,
hardware chord engine configurations, and Shift layer trigger assignments.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea,
    QComboBox, QTableWidget, QTableWidgetItem, QDialog, QLineEdit, QHeaderView
)
from PySide6.QtCore import Qt, QTimer
import pynput.keyboard


class KeyRecorderDialog(QDialog):
    """Interactive Key Combo Recorder Modal capturing keyboard/mouse keys via pynput."""

    def __init__(self, button_name, parent=None):
        super().__init__(parent)
        self.button_name = button_name
        self.recorded_key = None
        self.setWindowTitle(f"Record Binding: {button_name}")
        self.setFixedSize(380, 180)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        lbl_info = QLabel(f"Press any key or shortcut for [{button_name}]...")
        lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #f3e8ff;")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)

        self.lbl_key = QLabel("Listening...")
        self.lbl_key.setStyleSheet("font-size: 18px; font-weight: bold; color: #00f5a0;")
        self.lbl_key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_key)

        btn_box = QHBoxLayout()
        self.btn_save = QPushButton("Save Binding")
        self.btn_save.setObjectName("PrimaryBtn")
        self.btn_save.setEnabled(False)
        self.btn_save.clicked.connect(self.accept)

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("SecondaryBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(self.btn_save)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

        # Start pynput listener
        self.listener = pynput.keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                key_str = key.char.upper()
            else:
                key_str = key.name.upper()
            self.recorded_key = key_str
            self.lbl_key.setText(f"[ {key_str} ]")
            self.btn_save.setEnabled(True)
        except Exception:
            pass
        return False  # Stop listener after one key press

    def closeEvent(self, event):
        if self.listener.running:
            self.listener.stop()
        super().closeEvent(event)


class RemappingView(QWidget):
    """
    Remapping Tab View handling button mappings, macros, chords, and shift layers.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 1. Header Control Card
        header_card = QFrame()
        header_card.setObjectName("GlassCard")
        header_layout = QHBoxLayout(header_card)

        title = QLabel("🎮 BUTTON REMAPPING & MACRO MATRIX")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        self.btn_reset_all = QPushButton("Reset All Mappings")
        self.btn_reset_all.setObjectName("SecondaryBtn")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(self.btn_reset_all)
        main_layout.addWidget(header_card)

        # 2. Scrollable Remapping Card List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)

        self.remap_rows = {}
        button_list = ["A", "B", "X", "Y", "LB", "RB", "L3", "R3", "SELECT", "START", "HOME", "M1", "M2"]

        for bname in button_list:
            row_card = QFrame()
            row_card.setObjectName("GlassCard")
            row_layout = QHBoxLayout(row_card)
            row_layout.setContentsMargins(12, 8, 12, 8)

            lbl_btn = QLabel(f"Button [{bname}]")
            lbl_btn.setStyleSheet("font-weight: bold; font-size: 13px; min-width: 120px;")

            lbl_mapping = QLabel("Gamepad Default")
            lbl_mapping.setStyleSheet("color: #00f5a0; font-weight: 600; min-width: 180px;")

            btn_remap = QPushButton("🖊️ Record Key")
            btn_remap.setObjectName("PrimaryBtn")
            btn_remap.clicked.connect(lambda ch=False, name=bname, lbl=lbl_mapping: self.open_recorder(name, lbl))

            btn_clear = QPushButton("❌ Reset")
            btn_clear.setObjectName("SecondaryBtn")
            btn_clear.clicked.connect(lambda ch=False, lbl=lbl_mapping: lbl.setText("Gamepad Default"))

            row_layout.addWidget(lbl_btn)
            row_layout.addWidget(lbl_mapping)
            row_layout.addStretch()
            row_layout.addWidget(btn_remap)
            row_layout.addWidget(btn_clear)

            scroll_layout.addWidget(row_card)
            self.remap_rows[bname] = lbl_mapping

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def open_recorder(self, button_name, target_label):
        dlg = KeyRecorderDialog(button_name, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.recorded_key:
            target_label.setText(f"Key: [ {dlg.recorded_key} ]")
