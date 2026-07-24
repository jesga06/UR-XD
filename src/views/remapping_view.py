"""
Remapping View for PySide6 GUI (remapping_view.py)
Multiple Shift Remapping Layer tabs manager, Shift Layer activation chord configurator,
Block XInput opt-out checkboxes, interactive Key Combo Recorder with target layer saving,
and Advanced Mouse Scroll Wheel Remap options (Oneshot/Continuous, notch tester, repeat speed).
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea,
    QComboBox, QDialog, QCheckBox, QTabWidget, QSpinBox, QRadioButton, QButtonGroup,
    QMessageBox
)
from PySide6.QtCore import Qt
import pynput.keyboard


class KeyRecorderDialog(QDialog):
    """Interactive Key Combo Recorder Modal capturing keyboard/mouse keys via pynput."""

    def __init__(self, button_name, parent=None):
        super().__init__(parent)
        self.button_name = button_name
        self.recorded_key = None
        self.target_layer = "Standard"
        self.setWindowTitle(f"Record Binding: {button_name}")
        self.setFixedSize(420, 220)
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

        # Target Layer Selection Buttons
        btn_box = QHBoxLayout()
        self.btn_save_std = QPushButton("Save Standard Map")
        self.btn_save_std.setObjectName("PrimaryBtn")
        self.btn_save_std.setEnabled(False)
        self.btn_save_std.clicked.connect(lambda: self.save_target("Standard"))

        self.btn_save_shift = QPushButton("Save Shift Map")
        self.btn_save_shift.setObjectName("PrimaryBtn")
        self.btn_save_shift.setEnabled(False)
        self.btn_save_shift.clicked.connect(lambda: self.save_target("Shift"))

        btn_cancel = QPushButton("Cancel")
        btn_cancel.setObjectName("SecondaryBtn")
        btn_cancel.clicked.connect(self.reject)

        btn_box.addWidget(self.btn_save_std)
        btn_box.addWidget(self.btn_save_shift)
        btn_box.addWidget(btn_cancel)
        layout.addLayout(btn_box)

        # Start pynput listener
        self.listener = pynput.keyboard.Listener(on_press=self.on_press)
        self.listener.start()

    def save_target(self, target_layer):
        self.target_layer = target_layer
        self.accept()

    def on_press(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                key_str = key.char.upper()
            else:
                key_str = key.name.upper()
            self.recorded_key = key_str
            self.lbl_key.setText(f"[ {key_str} ]")
            self.btn_save_std.setEnabled(True)
            self.btn_save_shift.setEnabled(True)
        except Exception:
            pass
        return False

    def closeEvent(self, event):
        if self.listener.running:
            self.listener.stop()
        super().closeEvent(event)


class RemappingView(QWidget):
    """
    Remapping Tab View handling multi-shift layer navigation, scroll customization, and block checkboxes.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 1. Multiple Shift Layers Navigation Bar
        shift_header_card = QFrame()
        shift_header_card.setObjectName("GlassCard")
        shift_header_layout = QVBoxLayout(shift_header_card)

        top_shift_row = QHBoxLayout()
        lbl_shift_title = QLabel("⚡ SHIFT LAYER CONFIGURATOR")
        lbl_shift_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_add_shift = QPushButton("+ Add Shift Layer")
        btn_add_shift.setObjectName("PrimaryBtn")
        btn_add_shift.clicked.connect(self.add_new_shift_layer)

        top_shift_row.addWidget(lbl_shift_title)
        top_shift_row.addStretch()
        top_shift_row.addWidget(btn_add_shift)
        shift_header_layout.addLayout(top_shift_row)

        # Shift Layer Activation Parameters
        act_row = QHBoxLayout()
        act_row.addWidget(QLabel("Active Layer:"))
        self.combo_shift_layers = QComboBox()
        self.combo_shift_layers.addItems(["Base Mapping", "Shift Layer 1", "Shift Layer 2 (Sniper Mode)"])
        act_row.addWidget(self.combo_shift_layers)

        act_row.addWidget(QLabel("Primary Shift Trigger:"))
        self.combo_shift_key = QComboBox()
        self.combo_shift_key.addItems(["M1 Paddle", "M2 Paddle", "LB Bumper", "RB Bumper", "L3 Click"])
        act_row.addWidget(self.combo_shift_key)

        act_row.addWidget(QLabel("Modifier Key:"))
        self.combo_shift_mod = QComboBox()
        self.combo_shift_mod.addItems(["None", "A", "B", "X", "Y", "LT", "RT"])
        act_row.addWidget(self.combo_shift_mod)

        self.radio_hold = QRadioButton("Hold Mode")
        self.radio_toggle = QRadioButton("Toggle Mode")
        self.radio_hold.setChecked(True)

        act_row.addWidget(self.radio_hold)
        act_row.addWidget(self.radio_toggle)

        shift_header_layout.addLayout(act_row)
        main_layout.addWidget(shift_header_card)

        # 2. Advanced Scroll Remapping Customization Card
        scroll_custom_card = QFrame()
        scroll_custom_card.setObjectName("GlassCard")
        scroll_custom_layout = QHBoxLayout(scroll_custom_card)

        lbl_scroll_title = QLabel("🖱️ Mouse Scroll Settings:")
        lbl_scroll_title.setStyleSheet("font-weight: bold;")

        self.radio_oneshot = QRadioButton("Oneshot")
        self.radio_continuous = QRadioButton("Continuous (Hold)")
        self.radio_continuous.setChecked(True)

        lbl_notch = QLabel("Notches per Trigger:")
        self.spin_notches = QSpinBox()
        self.spin_notches.setRange(1, 20)
        self.spin_notches.setValue(3)

        btn_test_notch = QPushButton("Notch Tester (Scroll Here)")
        btn_test_notch.setObjectName("SecondaryBtn")

        scroll_custom_layout.addWidget(lbl_scroll_title)
        scroll_custom_layout.addWidget(self.radio_oneshot)
        scroll_custom_layout.addWidget(self.radio_continuous)
        scroll_custom_layout.addWidget(lbl_notch)
        scroll_custom_layout.addWidget(self.spin_notches)
        scroll_custom_layout.addWidget(btn_test_notch)

        main_layout.addWidget(scroll_custom_card)

        # 3. Scrollable Button Remapping Matrix Cards
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

            chk_block = QCheckBox("Block XInput")
            chk_block.setChecked(True)

            btn_remap = QPushButton("🖊️ Record Key")
            btn_remap.setObjectName("PrimaryBtn")
            btn_remap.clicked.connect(lambda ch=False, name=bname, lbl=lbl_mapping: self.open_recorder(name, lbl))

            btn_clear = QPushButton("❌ Reset")
            btn_clear.setObjectName("SecondaryBtn")
            btn_clear.clicked.connect(lambda ch=False, lbl=lbl_mapping: lbl.setText("Gamepad Default"))

            row_layout.addWidget(lbl_btn)
            row_layout.addWidget(lbl_mapping)
            row_layout.addWidget(chk_block)
            row_layout.addStretch()
            row_layout.addWidget(btn_remap)
            row_layout.addWidget(btn_clear)

            scroll_layout.addWidget(row_card)
            self.remap_rows[bname] = lbl_mapping

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def add_new_shift_layer(self):
        new_name = f"Shift Layer {self.combo_shift_layers.count()}"
        self.combo_shift_layers.addItem(new_name)
        self.combo_shift_layers.setCurrentText(new_name)

    def open_recorder(self, button_name, target_label):
        dlg = KeyRecorderDialog(button_name, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.recorded_key:
            target_label.setText(f"Key: [ {dlg.recorded_key} ] ({dlg.target_layer})")
