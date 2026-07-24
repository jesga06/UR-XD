"""
Remapping View for PySide6 GUI (remapping_view.py)
Multiple Shift Remapping Layer tabs manager, Shift Layer activation chord configurator,
Block XInput opt-out checkboxes, interactive Key Combo Recorder with target layer saving,
multi-key combo capture, and Advanced Mouse Scroll Wheel Remap options.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea,
    QComboBox, QDialog, QCheckBox, QSpinBox, QRadioButton, QButtonGroup,
    QMessageBox, QLineEdit
)
from PySide6.QtCore import Qt
import pynput.keyboard
import pynput.mouse


ALL_GAMEPAD_BUTTONS = [
    "A", "B", "X", "Y", "LB", "RB", "LT", "RT", "L3", "R3",
    "SELECT", "START", "HOME", "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT",
    "M1", "M2", "L4", "R4"
]


class KeyRecorderDialog(QDialog):
    """
    Interactive Key Combo Recorder Modal capturing multi-key shortcuts and mouse scroll gestures.
    """

    def __init__(self, button_name, parent=None):
        super().__init__(parent)
        self.button_name = button_name
        self.recorded_binding = None
        self.target_layer = "Standard"
        self.pressed_keys = set()
        self.notch_count = 1

        self.setWindowTitle(f"Record Binding: {button_name}")
        self.setFixedSize(460, 320)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        lbl_info = QLabel(f"Press shortcut or scroll mouse wheel for [{button_name}]...")
        lbl_info.setStyleSheet("font-size: 14px; font-weight: bold; color: #f3e8ff;")
        lbl_info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_info)

        self.lbl_key = QLabel("Listening for input...")
        self.lbl_key.setStyleSheet("font-size: 16px; font-weight: bold; color: #00f5a0;")
        self.lbl_key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_key)

        # Mouse Scroll Customization Frame (Shown when scroll is detected)
        self.scroll_frame = QFrame()
        self.scroll_frame.setObjectName("GlassCard")
        scroll_layout = QVBoxLayout(self.scroll_frame)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        lbl_scroll = QLabel("🖱️ Interactive Mouse Scroll Tester (Scroll inside box to set notches):")
        lbl_scroll.setStyleSheet("font-weight: bold; font-size: 11px; color: #a992cb;")
        scroll_layout.addWidget(lbl_scroll)

        s_box = QHBoxLayout()
        self.radio_continuous = QRadioButton("Continuous (Hold)")
        self.radio_oneshot = QRadioButton("Oneshot")
        self.radio_continuous.setChecked(True)

        s_box.addWidget(self.radio_continuous)
        s_box.addWidget(self.radio_oneshot)
        scroll_layout.addLayout(s_box)

        n_box = QHBoxLayout()
        n_box.addWidget(QLabel("Notches:"))
        self.lbl_notch_val = QLabel("1 Notch")
        self.lbl_notch_val.setStyleSheet("font-weight: bold; color: #00f5a0;")
        n_box.addWidget(self.lbl_notch_val)

        btn_reset_notches = QPushButton("Reset Notches")
        btn_reset_notches.setObjectName("SecondaryBtn")
        btn_reset_notches.clicked.connect(self.reset_notches)
        n_box.addWidget(btn_reset_notches)
        scroll_layout.addLayout(n_box)

        self.scroll_frame.hide()
        layout.addWidget(self.scroll_frame)

        # Save Target Layer Buttons
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

        # Start pynput Listeners
        self.kb_listener = pynput.keyboard.Listener(on_press=self.on_kb_press, on_release=self.on_kb_release)
        self.mouse_listener = pynput.mouse.Listener(on_click=self.on_mouse_click, on_scroll=self.on_mouse_scroll)
        self.kb_listener.start()
        self.mouse_listener.start()

    def reset_notches(self):
        self.notch_count = 1
        self.lbl_notch_val.setText("1 Notch")

    def save_target(self, target_layer):
        self.target_layer = target_layer
        self.accept()

    def on_kb_press(self, key):
        try:
            k_name = key.char.upper() if hasattr(key, 'char') and key.char else key.name.upper()
            self.pressed_keys.add(k_name)
            combo_str = " + ".join(sorted(self.pressed_keys))
            self.recorded_binding = combo_str
            self.lbl_key.setText(f"[ {combo_str} ]")
            self.btn_save_std.setEnabled(True)
            self.btn_save_shift.setEnabled(True)
        except Exception:
            pass

    def on_kb_release(self, key):
        pass

    def on_mouse_click(self, x, y, button, pressed):
        if pressed and button != pynput.mouse.Button.left:
            b_name = f"MOUSE_{button.name.upper()}"
            self.recorded_binding = b_name
            self.lbl_key.setText(f"[ {b_name} ]")
            self.btn_save_std.setEnabled(True)
            self.btn_save_shift.setEnabled(True)

    def on_mouse_scroll(self, x, y, dx, dy):
        direction = "SCROLL_UP" if dy > 0 else "SCROLL_DOWN"
        self.notch_count += 1
        self.recorded_binding = f"{direction} ({self.notch_count} notches)"
        self.lbl_key.setText(f"[ {self.recorded_binding} ]")
        self.lbl_notch_val.setText(f"{self.notch_count} Notches")
        self.scroll_frame.show()
        self.btn_save_std.setEnabled(True)
        self.btn_save_shift.setEnabled(True)

    def closeEvent(self, event):
        if self.kb_listener.running:
            self.kb_listener.stop()
        if self.mouse_listener.running:
            self.mouse_listener.stop()
        super().closeEvent(event)


class RemappingView(QWidget):
    """
    Remapping Tab View displaying clean button names, side-by-side standard & shift maps,
    dynamic extra buttons, shift key selectors, and shift layer deletion.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 1. Multiple Shift Layers Navigation Header
        shift_header_card = QFrame()
        shift_header_card.setObjectName("GlassCard")
        shift_header_layout = QVBoxLayout(shift_header_card)

        top_shift_row = QHBoxLayout()
        lbl_shift_title = QLabel("⚡ SHIFT LAYER CONFIGURATOR")
        lbl_shift_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_add_shift = QPushButton("+ Add Shift Layer")
        btn_add_shift.setObjectName("PrimaryBtn")
        btn_add_shift.clicked.connect(self.add_new_shift_layer)

        btn_del_shift = QPushButton("- Delete Shift Layer")
        btn_del_shift.setObjectName("SecondaryBtn")
        btn_del_shift.clicked.connect(self.delete_current_shift_layer)

        top_shift_row.addWidget(lbl_shift_title)
        top_shift_row.addStretch()
        top_shift_row.addWidget(btn_add_shift)
        top_shift_row.addWidget(btn_del_shift)
        shift_header_layout.addLayout(top_shift_row)

        # Shift Layer Configuration Parameters
        act_row = QHBoxLayout()
        act_row.addWidget(QLabel("Active Layer:"))
        self.combo_shift_layers = QComboBox()
        self.combo_shift_layers.addItems(["Shift Layer 1"])
        act_row.addWidget(self.combo_shift_layers)

        act_row.addWidget(QLabel("Shift Key:"))
        self.combo_shift_key = QComboBox()
        self.combo_shift_key.addItems(ALL_GAMEPAD_BUTTONS)
        act_row.addWidget(self.combo_shift_key)

        act_row.addWidget(QLabel("Modifier Key:"))
        self.combo_shift_mod = QComboBox()
        self.combo_shift_mod.addItem("None")
        self.combo_shift_mod.addItems(ALL_GAMEPAD_BUTTONS)
        act_row.addWidget(self.combo_shift_mod)

        self.radio_hold = QRadioButton("Hold Mode")
        self.radio_toggle = QRadioButton("Toggle Mode")
        self.radio_hold.setChecked(True)

        act_row.addWidget(self.radio_hold)
        act_row.addWidget(self.radio_toggle)

        shift_header_layout.addLayout(act_row)
        main_layout.addWidget(shift_header_card)

        # 2. Scrollable Button Remapping Matrix Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(8)

        # Header Legend Row
        leg_card = QFrame()
        leg_card.setObjectName("GlassCard")
        leg_layout = QHBoxLayout(leg_card)
        leg_layout.setContentsMargins(12, 6, 12, 6)

        lbl_h1 = QLabel("Button")
        lbl_h1.setStyleSheet("font-weight: bold; color: #a992cb; min-width: 80px;")
        lbl_h2 = QLabel("Standard Mapping")
        lbl_h2.setStyleSheet("font-weight: bold; color: #00f5a0; min-width: 140px;")
        lbl_h3 = QLabel("Shift Mapping")
        lbl_h3.setStyleSheet("font-weight: bold; color: #a855f7; min-width: 140px;")
        lbl_h4 = QLabel("Block XInput")
        lbl_h4.setStyleSheet("font-weight: bold; color: #a992cb; min-width: 90px;")

        leg_layout.addWidget(lbl_h1)
        leg_layout.addWidget(lbl_h2)
        leg_layout.addWidget(lbl_h3)
        leg_layout.addWidget(lbl_h4)
        leg_layout.addStretch()
        scroll_layout.addWidget(leg_card)

        self.remap_rows = {}
        # Dynamic button list (Standard + Extra paddles)
        button_list = ["A", "B", "X", "Y", "LB", "RB", "L3", "R3", "SELECT", "START", "HOME", "M1", "M2", "L4", "R4"]

        for bname in button_list:
            row_card = QFrame()
            row_card.setObjectName("GlassCard")
            row_layout = QHBoxLayout(row_card)
            row_layout.setContentsMargins(12, 8, 12, 8)

            lbl_btn = QLabel(bname)
            lbl_btn.setStyleSheet("font-weight: bold; font-size: 13px; min-width: 80px;")

            lbl_std = QLabel("Gamepad Default")
            lbl_std.setStyleSheet("color: #00f5a0; font-weight: 600; min-width: 140px;")

            lbl_shift = QLabel("Unmapped")
            lbl_shift.setStyleSheet("color: #a855f7; font-weight: 600; min-width: 140px;")

            chk_block = QCheckBox()
            chk_block.setChecked(True)

            btn_remap = QPushButton("🖊️ Record")
            btn_remap.setObjectName("PrimaryBtn")
            btn_remap.clicked.connect(lambda ch=False, name=bname, l1=lbl_std, l2=lbl_shift: self.open_recorder(name, l1, l2))

            btn_clear = QPushButton("❌ Reset")
            btn_clear.setObjectName("SecondaryBtn")
            btn_clear.clicked.connect(lambda ch=False, l1=lbl_std, l2=lbl_shift: self.reset_row(l1, l2))

            row_layout.addWidget(lbl_btn)
            row_layout.addWidget(lbl_std)
            row_layout.addWidget(lbl_shift)
            row_layout.addWidget(chk_block)
            row_layout.addStretch()
            row_layout.addWidget(btn_remap)
            row_layout.addWidget(btn_clear)

            scroll_layout.addWidget(row_card)
            self.remap_rows[bname] = (lbl_std, lbl_shift)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def reset_row(self, lbl_std, lbl_shift):
        lbl_std.setText("Gamepad Default")
        lbl_shift.setText("Unmapped")

    def add_new_shift_layer(self):
        new_name = f"Shift Layer {self.combo_shift_layers.count() + 1}"
        self.combo_shift_layers.addItem(new_name)
        self.combo_shift_layers.setCurrentText(new_name)

    def delete_current_shift_layer(self):
        if self.combo_shift_layers.count() > 1:
            curr_idx = self.combo_shift_layers.currentIndex()
            self.combo_shift_layers.removeItem(curr_idx)
        else:
            QMessageBox.information(self, "Shift Layers", "Cannot delete the default Shift Layer.")

    def open_recorder(self, button_name, lbl_std, lbl_shift):
        dlg = KeyRecorderDialog(button_name, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.recorded_binding:
            if dlg.target_layer == "Standard":
                lbl_std.setText(f"[ {dlg.recorded_binding} ]")
            else:
                lbl_shift.setText(f"[ {dlg.recorded_binding} ]")
