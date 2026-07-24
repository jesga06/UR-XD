"""
Remapping View for PySide6 GUI (remapping_view.py)
Multiple Shift Remapping Layer QTabBar manager, Shift Layer activation chord configurator,
Block XInput opt-out checkboxes, interactive Key Combo Recorder with target layer saving,
multi-key combo capture, and Advanced Mouse Scroll Wheel Remap options.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea,
    QComboBox, QDialog, QCheckBox, QRadioButton, QButtonGroup,
    QMessageBox, QLineEdit, QTabBar
)
from PySide6.QtCore import Qt
import pynput.keyboard
import pynput.mouse


ALL_GAMEPAD_BUTTONS = [
    "A", "B", "X", "Y", "LB", "RB", "LT", "RT", "L3", "R3",
    "SELECT", "START", "HOME", "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT",
    "M1", "M2", "L4", "R4"
]

SPECIAL_KEY_TRANSLATIONS = {
    "MEDIA_PLAY_PAUSE": "MEDIA_PLAY",
    "PRINT_SCREEN": "PRINT_SCREEN",
    "CAPS_LOCK": "CAPS_LOCK",
    "PAGE_UP": "PAGE_UP",
    "PAGE_DOWN": "PAGE_DOWN"
}


class ScrollTesterWidget(QFrame):
    """Interactive mouse wheel notch tester widget capturing wheelEvent."""

    def __init__(self, on_scroll_cb, parent=None):
        super().__init__(parent)
        self.on_scroll_cb = on_scroll_cb
        self.setObjectName("GlassCard")
        self.setMinimumHeight(60)

    def wheelEvent(self, event):
        angle = event.angleDelta().y()
        if angle != 0:
            direction = "SCROLL_UP" if angle > 0 else "SCROLL_DOWN"
            self.on_scroll_cb(direction)


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
        self.scroll_direction = "SCROLL_UP"

        self.setWindowTitle(f"Record Binding: {button_name}")
        self.setFixedSize(460, 360)
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
        self.scroll_frame = ScrollTesterWidget(self.on_widget_scroll, self)
        scroll_layout = QVBoxLayout(self.scroll_frame)
        scroll_layout.setContentsMargins(10, 10, 10, 10)

        lbl_scroll = QLabel("🖱️ Interactive Mouse Scroll Tester (Scroll inside box to set notches):")
        lbl_scroll.setStyleSheet("font-weight: bold; font-size: 11px; color: #a992cb;")
        scroll_layout.addWidget(lbl_scroll)

        s_box = QHBoxLayout()
        self.radio_continuous = QRadioButton("Continuous (Hold)")
        self.radio_oneshot = QRadioButton("Oneshot")
        self.radio_oneshot.setChecked(True)

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
        self.update_scroll_binding()

    def on_widget_scroll(self, direction):
        self.scroll_direction = direction
        self.notch_count += 1
        self.lbl_notch_val.setText(f"{self.notch_count} Notches")
        self.update_scroll_binding()

    def update_scroll_binding(self):
        mode = "oneshot" if self.radio_oneshot.isChecked() else "continuous"
        self.recorded_binding = f"{self.scroll_direction.lower()}:{self.notch_count}:{mode}:0.05"
        self.lbl_key.setText(f"[ {self.recorded_binding} ]")
        self.btn_save_std.setEnabled(True)
        self.btn_save_shift.setEnabled(True)

    def save_target(self, target_layer):
        self.target_layer = target_layer
        self.accept()

    def on_kb_press(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                k_name = key.char.upper()
            else:
                k_name = key.name.upper() if hasattr(key, 'name') else str(key).upper()

            k_name = SPECIAL_KEY_TRANSLATIONS.get(k_name, k_name)
            self.pressed_keys.add(k_name)
            combo_str = " + ".join(sorted(self.pressed_keys))
            self.recorded_binding = combo_str
            self.lbl_key.setText(f"[ {combo_str} ]")
            self.btn_save_std.setEnabled(True)
            self.btn_save_shift.setEnabled(True)
        except Exception:
            pass

    def on_kb_release(self, key):
        try:
            k_name = key.char.upper() if hasattr(key, 'char') and key.char else key.name.upper()
            if k_name in self.pressed_keys:
                self.pressed_keys.remove(k_name)
        except Exception:
            pass

    def on_mouse_click(self, x, y, button, pressed):
        if pressed and button != pynput.mouse.Button.left:
            b_name = f"MOUSE_{button.name.upper()}"
            if button == pynput.mouse.Button.x1:
                b_name = "MOUSE_XBUTTON1"
            elif button == pynput.mouse.Button.x2:
                b_name = "MOUSE_XBUTTON2"
            elif button == pynput.mouse.Button.middle:
                b_name = "MOUSE_MIDDLE"

            self.recorded_binding = b_name
            self.lbl_key.setText(f"[ {b_name} ]")
            self.btn_save_std.setEnabled(True)
            self.btn_save_shift.setEnabled(True)

    def on_mouse_scroll(self, x, y, dx, dy):
        self.scroll_direction = "SCROLL_UP" if dy > 0 else "SCROLL_DOWN"
        self.scroll_frame.show()
        self.update_scroll_binding()

    def closeEvent(self, event):
        if self.kb_listener.running:
            self.kb_listener.stop()
        if self.mouse_listener.running:
            self.mouse_listener.stop()
        super().closeEvent(event)


class RemappingView(QWidget):
    """
    Remapping Tab View displaying clean button names, side-by-side standard & shift maps,
    QTabBar shift layer management, search filter, and config persistence.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.active_layer_idx = 0
        self.remap_row_widgets = {}
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 1. Multiple Shift Layers QTabBar Navigation Header
        shift_header_card = QFrame()
        shift_header_card.setObjectName("GlassCard")
        shift_header_layout = QVBoxLayout(shift_header_card)

        top_shift_row = QHBoxLayout()
        lbl_shift_title = QLabel("⚡ SHIFT LAYER CONFIGURATOR")
        lbl_shift_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        self.edit_filter = QLineEdit()
        self.edit_filter.setPlaceholderText("🔍 Filter buttons...")
        self.edit_filter.setFixedWidth(160)
        self.edit_filter.textChanged.connect(self.filter_buttons)

        btn_add_shift = QPushButton("+ Add Shift Layer")
        btn_add_shift.setObjectName("PrimaryBtn")
        btn_add_shift.clicked.connect(self.add_new_shift_layer)

        btn_del_shift = QPushButton("- Delete Layer")
        btn_del_shift.setObjectName("SecondaryBtn")
        btn_del_shift.clicked.connect(self.delete_current_shift_layer)

        btn_reset_all = QPushButton("❌ Reset All")
        btn_reset_all.setObjectName("SecondaryBtn")
        btn_reset_all.clicked.connect(self.reset_all_remappings)

        top_shift_row.addWidget(lbl_shift_title)
        top_shift_row.addStretch()
        top_shift_row.addWidget(self.edit_filter)
        top_shift_row.addWidget(btn_add_shift)
        top_shift_row.addWidget(btn_del_shift)
        top_shift_row.addWidget(btn_reset_all)
        shift_header_layout.addLayout(top_shift_row)

        # TabBar Navigation Bar
        self.tab_bar = QTabBar()
        self.tab_bar.setExpanding(False)
        self.tab_bar.currentChanged.connect(self.on_shift_tab_changed)
        shift_header_layout.addWidget(self.tab_bar)

        # Shift Layer Configuration Parameters Row
        act_row = QHBoxLayout()
        act_row.addWidget(QLabel("Layer Name:"))
        self.edit_layer_name = QLineEdit("Shift Layer 1")
        self.edit_layer_name.setFixedWidth(120)
        self.edit_layer_name.editingFinished.connect(self.save_active_layer_params)
        act_row.addWidget(self.edit_layer_name)

        act_row.addWidget(QLabel("Shift Key:"))
        self.combo_shift_key = QComboBox()
        self.combo_shift_key.addItems(ALL_GAMEPAD_BUTTONS)
        self.combo_shift_key.currentIndexChanged.connect(self.save_active_layer_params)
        act_row.addWidget(self.combo_shift_key)

        act_row.addWidget(QLabel("Modifier Key:"))
        self.combo_shift_mod = QComboBox()
        self.combo_shift_mod.addItem("None")
        self.combo_shift_mod.addItems(ALL_GAMEPAD_BUTTONS)
        self.combo_shift_mod.currentIndexChanged.connect(self.save_active_layer_params)
        act_row.addWidget(self.combo_shift_mod)

        self.radio_hold = QRadioButton("Hold")
        self.radio_toggle = QRadioButton("Toggle")
        self.radio_hold.setChecked(True)
        self.radio_hold.toggled.connect(self.save_active_layer_params)

        act_row.addWidget(self.radio_hold)
        act_row.addWidget(self.radio_toggle)

        act_row.addWidget(QLabel("Haptic Profile:"))
        self.combo_haptic_prof = QComboBox()
        self.combo_haptic_prof.addItems(["Default Rumble", "Soft Pulse", "Heavy Rumble", "Disabled"])
        self.combo_haptic_prof.currentIndexChanged.connect(self.save_active_layer_params)
        act_row.addWidget(self.combo_haptic_prof)

        self.chk_passthrough = QCheckBox("Pass-Through")
        self.chk_passthrough.stateChanged.connect(self.save_active_layer_params)
        act_row.addWidget(self.chk_passthrough)

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
            chk_block.stateChanged.connect(lambda state, name=bname: self.on_block_xinput_changed(name, state))

            btn_remap = QPushButton("🖊️ Record")
            btn_remap.setObjectName("PrimaryBtn")
            btn_remap.clicked.connect(lambda ch=False, name=bname, l1=lbl_std, l2=lbl_shift: self.open_recorder(name, l1, l2))

            btn_clear = QPushButton("❌ Reset")
            btn_clear.setObjectName("SecondaryBtn")
            btn_clear.clicked.connect(lambda ch=False, name=bname, l1=lbl_std, l2=lbl_shift: self.reset_row(name, l1, l2))

            row_layout.addWidget(lbl_btn)
            row_layout.addWidget(lbl_std)
            row_layout.addWidget(lbl_shift)
            row_layout.addWidget(chk_block)
            row_layout.addStretch()
            row_layout.addWidget(btn_remap)
            row_layout.addWidget(btn_clear)

            scroll_layout.addWidget(row_card)
            self.remap_row_widgets[bname] = (row_card, lbl_std, lbl_shift, chk_block)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

        self.refresh_shift_tabs()

    def refresh_shift_tabs(self):
        self.tab_bar.blockSignals(True)
        self.tab_bar.clear()
        config = getattr(self.app, 'controller_config', None)
        if config:
            layers = config.get_shift_layers()
            for l in layers:
                self.tab_bar.addTab(l.get("name", "Shift Layer"))
        else:
            self.tab_bar.addTab("Shift Layer 1")
        self.tab_bar.blockSignals(False)

    def on_shift_tab_changed(self, index):
        if index < 0:
            return
        self.active_layer_idx = index
        config = getattr(self.app, 'controller_config', None)
        if config:
            layers = config.get_shift_layers()
            if index < len(layers):
                l = layers[index]
                self.edit_layer_name.setText(l.get("name", ""))
                self.combo_shift_key.setCurrentText(l.get("trigger_button", "A").upper())
                self.combo_shift_mod.setCurrentText(l.get("modifier_button", "None").upper())
                self.radio_hold.setChecked(l.get("mode", "hold") == "hold")
                self.radio_toggle.setChecked(l.get("mode", "hold") == "toggle")

    def save_active_layer_params(self):
        config = getattr(self.app, 'controller_config', None)
        if not config:
            return
        layers = config.get_shift_layers()
        if self.active_layer_idx < len(layers):
            l = layers[self.active_layer_idx]
            l["name"] = self.edit_layer_name.text()
            l["trigger_button"] = self.combo_shift_key.currentText().lower()
            l["modifier_button"] = self.combo_shift_mod.currentText().lower()
            l["mode"] = "hold" if self.radio_hold.isChecked() else "toggle"
            l["haptic_profile"] = self.combo_haptic_prof.currentText()
            l["passthrough"] = self.chk_passthrough.isChecked()
            config.set_shift_layers(layers)
            self.app.save_config()
            self.refresh_shift_tabs()

    def filter_buttons(self, text):
        query = text.lower().strip()
        for bname, (row_card, _, _, _) in self.remap_row_widgets.items():
            row_card.setVisible(query in bname.lower())

    def on_block_xinput_changed(self, button_name, state):
        config = getattr(self.app, 'controller_config', None)
        if config:
            val = (state == Qt.CheckState.Checked.value or state is True)
            config.set("block_xinput", button_name.lower(), str(val).lower())
            self.app.save_config()

    def reset_row(self, button_name, lbl_std, lbl_shift):
        lbl_std.setText("Gamepad Default")
        lbl_shift.setText("Unmapped")
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.remove_option("mappings", button_name.lower())
            layers = config.get_shift_layers()
            if self.active_layer_idx < len(layers):
                layers[self.active_layer_idx].get("mappings", {}).pop(button_name.lower(), None)
                config.set_shift_layers(layers)
            self.app.save_config()

    def reset_all_remappings(self):
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.data["mappings"] = {}
            config.save()
            for _, (_, lbl_std, lbl_shift, _) in self.remap_row_widgets.items():
                lbl_std.setText("Gamepad Default")
                lbl_shift.setText("Unmapped")

    def add_new_shift_layer(self):
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.add_shift_layer(name=f"Shift Layer {self.tab_bar.count() + 1}")
            self.app.save_config()
            self.refresh_shift_tabs()
            self.tab_bar.setCurrentIndex(self.tab_bar.count() - 1)

    def delete_current_shift_layer(self):
        if self.tab_bar.count() > 1:
            config = getattr(self.app, 'controller_config', None)
            if config:
                layers = config.get_shift_layers()
                if self.active_layer_idx < len(layers):
                    layer_id = layers[self.active_layer_idx].get("id", "")
                    config.remove_shift_layer(layer_id)
                    self.app.save_config()
                    self.refresh_shift_tabs()
        else:
            QMessageBox.information(self, "Shift Layers", "Cannot delete the default Shift Layer.")

    def open_recorder(self, button_name, lbl_std, lbl_shift):
        dlg = KeyRecorderDialog(button_name, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.recorded_binding:
            config = getattr(self.app, 'controller_config', None)
            if dlg.target_layer == "Standard":
                lbl_std.setText(f"[ {dlg.recorded_binding} ]")
                if config:
                    config.set("mappings", button_name.lower(), dlg.recorded_binding)
                    self.app.save_config()
            else:
                lbl_shift.setText(f"[ {dlg.recorded_binding} ]")
                if config:
                    layers = config.get_shift_layers()
                    if self.active_layer_idx < len(layers):
                        layers[self.active_layer_idx].setdefault("mappings", {})[button_name.lower()] = dlg.recorded_binding
                        config.set_shift_layers(layers)
                        self.app.save_config()
