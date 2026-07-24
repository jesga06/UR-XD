"""
Remapping View for PySide6 GUI (remapping_view.py)
Fully-featured, interactive button remapping matrix view organized into 4 logical groups:
Face Buttons, Shoulders & Sticks, D-Pad, System & Extras.
Supports direct manual typing into outlined QLineEdits OR interactive [R] key recording,
individual native input block toggles (Block), shift layer mapping QLineEdits, and shift block toggles (S. Blk).
"""

import sys
import os
import pynput.keyboard
import pynput.mouse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QCheckBox,
    QLineEdit, QComboBox, QGridLayout, QScrollArea, QDialog, QRadioButton, QMessageBox
)
from PySide6.QtCore import Qt


ALL_GAMEPAD_BUTTONS = [
    "A", "B", "X", "Y", "LB", "RB", "LT", "RT",
    "LS", "RS", "DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT",
    "SELECT", "START", "HOME", "M1", "M2", "L4", "R4"
]

SPECIAL_KEY_MAP = {
    pynput.keyboard.Key.space: "space",
    pynput.keyboard.Key.enter: "enter",
    pynput.keyboard.Key.tab: "tab",
    pynput.keyboard.Key.esc: "escape",
    pynput.keyboard.Key.backspace: "backspace",
    pynput.keyboard.Key.delete: "delete",
    pynput.keyboard.Key.shift: "shift",
    pynput.keyboard.Key.shift_r: "shift",
    pynput.keyboard.Key.ctrl: "ctrl",
    pynput.keyboard.Key.ctrl_r: "ctrl",
    pynput.keyboard.Key.alt: "alt",
    pynput.keyboard.Key.alt_r: "alt",
    pynput.keyboard.Key.cmd: "win",
    pynput.keyboard.Key.cmd_r: "win",
    pynput.keyboard.Key.up: "up",
    pynput.keyboard.Key.down: "down",
    pynput.keyboard.Key.left: "left",
    pynput.keyboard.Key.right: "right",
}


class ScrollTesterWidget(QFrame):
    """Interactive Scroll Wheel Tester Area."""

    def __init__(self, callback, parent=None):
        super().__init__(parent)
        self.callback = callback
        self.setObjectName("GlassCard")
        self.setMinimumHeight(60)

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.callback("scroll_up")
        elif delta < 0:
            self.callback("scroll_down")


class KeyRecorderDialog(QDialog):
    """Modal dialog to capture keyboard press, mouse click, or scroll wheel notch count."""

    def __init__(self, button_name, parent=None):
        super().__init__(parent)
        self.button_name = button_name
        self.recorded_binding = ""
        self.pressed_modifiers = set()
        self.notch_count = 1
        self.scroll_direction = "scroll_up"

        self.setWindowTitle(f"Record Input for [{button_name}]")
        self.resize(420, 260)
        self.setModal(True)

        layout = QVBoxLayout(self)
        layout.setSpacing(12)

        lbl_title = QLabel(f"Press Key / Combo for Gamepad Button [{button_name}]")
        lbl_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #f3e8ff;")
        layout.addWidget(lbl_title)

        self.lbl_key = QLabel("⚡ Listening for input... Press any key or scroll mouse wheel")
        self.lbl_key.setStyleSheet(
            "font-size: 13px; font-weight: bold; color: #00f5a0; "
            "background: rgba(0,0,0,0.5); padding: 12px; border-radius: 8px; border: 1px solid #a855f7;"
        )
        self.lbl_key.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.lbl_key)

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
        self.btn_save.setEnabled(True)

    def on_kb_press(self, key):
        if key in (pynput.keyboard.Key.shift, pynput.keyboard.Key.shift_r):
            self.pressed_modifiers.add("shift")
            return
        elif key in (pynput.keyboard.Key.ctrl, pynput.keyboard.Key.ctrl_r):
            self.pressed_modifiers.add("ctrl")
            return
        elif key in (pynput.keyboard.Key.alt, pynput.keyboard.Key.alt_r):
            self.pressed_modifiers.add("alt")
            return

        key_str = ""
        if isinstance(key, pynput.keyboard.KeyCode):
            if key.char:
                key_str = key.char.lower()
        elif key in SPECIAL_KEY_MAP:
            key_str = SPECIAL_KEY_MAP[key]

        if key_str:
            mods = sorted(list(self.pressed_modifiers))
            combo = "+".join(mods + [key_str]) if mods else key_str
            self.recorded_binding = combo
            self.lbl_key.setText(f"[ {combo} ]")
            self.btn_save.setEnabled(True)

    def on_kb_release(self, key):
        if key in (pynput.keyboard.Key.shift, pynput.keyboard.Key.shift_r):
            self.pressed_modifiers.discard("shift")
        elif key in (pynput.keyboard.Key.ctrl, pynput.keyboard.Key.ctrl_r):
            self.pressed_modifiers.discard("ctrl")
        elif key in (pynput.keyboard.Key.alt, pynput.keyboard.Key.alt_r):
            self.pressed_modifiers.discard("alt")

    def on_mouse_click(self, x, y, button, pressed):
        if not pressed:
            return
        btn_map = {
            pynput.mouse.Button.left: "mouse_left",
            pynput.mouse.Button.right: "mouse_right",
            pynput.mouse.Button.middle: "mouse_middle",
            pynput.mouse.Button.x1: "mouse_x1",
            pynput.mouse.Button.x2: "mouse_x2",
        }
        if button in btn_map:
            self.recorded_binding = btn_map[button]
            self.lbl_key.setText(f"[ {self.recorded_binding} ]")
            self.btn_save.setEnabled(True)

    def on_mouse_scroll(self, x, y, dx, dy):
        self.scroll_frame.show()
        if dy > 0:
            self.on_widget_scroll("scroll_up")
        elif dy < 0:
            self.on_widget_scroll("scroll_down")

    def closeEvent(self, event):
        self.kb_listener.stop()
        self.mouse_listener.stop()
        super().closeEvent(event)


class RemappingView(QWidget):
    """
    Button Remapping View providing 4 logical card groups (Face Buttons, Shoulders & Sticks, D-Pad, System & Extras).
    Offers outlined QLineEdits for typing mappings directly, [R] record buttons, and individual Block / S. Blk toggles.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.active_layer_idx = 0
        self.row_widgets = {}  # btn_name -> (edit_std, btn_rec_std, chk_block, edit_shift, btn_rec_shift, chk_sblock)
        self.setup_ui()
        self.load_config_values()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # 1. Shift Layer Management Header Card
        shift_card = QFrame()
        shift_card.setObjectName("GlassCard")
        shift_layout = QVBoxLayout(shift_card)
        shift_layout.setContentsMargins(12, 10, 12, 10)

        # Shift Navigation Bar Row
        nav_row = QHBoxLayout()
        lbl_shift_title = QLabel("❖ SHIFT LAYERS:")
        lbl_shift_title.setStyleSheet("font-weight: bold; font-size: 13px; color: #a855f7;")

        self.combo_layers = QComboBox()
        self.combo_layers.setMinimumWidth(180)
        self.combo_layers.currentIndexChanged.connect(self.on_layer_selected)

        btn_add_layer = QPushButton("+ Add Layer")
        btn_add_layer.setObjectName("PrimaryBtn")
        btn_add_layer.clicked.connect(self.add_shift_layer)

        btn_del_layer = QPushButton("❌ Delete Layer")
        btn_del_layer.setObjectName("SecondaryBtn")
        btn_del_layer.clicked.connect(self.delete_shift_layer)

        nav_row.addWidget(lbl_shift_title)
        nav_row.addWidget(self.combo_layers)
        nav_row.addWidget(btn_add_layer)
        nav_row.addWidget(btn_del_layer)
        nav_row.addStretch()

        # Shift Trigger & Mode Controls
        act_row = QHBoxLayout()
        act_row.addWidget(QLabel("Shift Key:"))
        self.combo_shift_trig = QComboBox()
        self.combo_shift_trig.addItem("None")
        self.combo_shift_trig.addItems(ALL_GAMEPAD_BUTTONS)
        self.combo_shift_trig.currentIndexChanged.connect(self.save_shift_layer_params)
        act_row.addWidget(self.combo_shift_trig)

        act_row.addWidget(QLabel("Modifier Key:"))
        self.combo_shift_mod = QComboBox()
        self.combo_shift_mod.addItem("None")
        self.combo_shift_mod.addItems(ALL_GAMEPAD_BUTTONS)
        self.combo_shift_mod.currentIndexChanged.connect(self.save_shift_layer_params)
        act_row.addWidget(self.combo_shift_mod)

        self.radio_hold = QRadioButton("Hold")
        self.radio_toggle = QRadioButton("Toggle")
        self.radio_hold.setChecked(True)
        self.radio_hold.toggled.connect(self.save_shift_layer_params)
        act_row.addWidget(self.radio_hold)
        act_row.addWidget(self.radio_toggle)

        self.chk_passthrough = QCheckBox("Pass-Through")
        self.chk_passthrough.stateChanged.connect(self.save_shift_layer_params)
        act_row.addWidget(self.chk_passthrough)
        act_row.addStretch()

        shift_layout.addLayout(nav_row)
        shift_layout.addLayout(act_row)
        main_layout.addWidget(shift_card)

        # 2. Scrollable 2x2 Grid of Button Remapping Cards
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background: transparent; border: none;")

        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)

        grid = QGridLayout()
        grid.setSpacing(14)

        # Group 1: Face Buttons
        card_face = self.create_button_group_card("Face Buttons", ["A", "B", "X", "Y"])
        grid.addWidget(card_face, 0, 0)

        # Group 2: Shoulders & Sticks
        card_shoulders = self.create_button_group_card("Shoulders & Sticks", ["LB", "RB", "LT", "RT", "LS", "RS"])
        grid.addWidget(card_shoulders, 0, 1)

        # Group 3: D-Pad
        card_dpad = self.create_button_group_card("D-Pad", ["DPAD_UP", "DPAD_DOWN", "DPAD_LEFT", "DPAD_RIGHT"])
        grid.addWidget(card_dpad, 1, 0)

        # Group 4: System & Extras
        card_system = self.create_button_group_card("System & Extras", ["SELECT", "START", "HOME", "M1", "M2", "L4", "R4"])
        grid.addWidget(card_system, 1, 1)

        scroll_layout.addLayout(grid)

        # Bottom Action Bar
        bot_box = QHBoxLayout()
        btn_guide = QPushButton("? Remapping Guide")
        btn_guide.setObjectName("SecondaryBtn")
        btn_guide.clicked.connect(self.show_remapping_guide)

        btn_reset_all = QPushButton("Reset All Remappings")
        btn_reset_all.setObjectName("SecondaryBtn")
        btn_reset_all.clicked.connect(self.reset_all_remappings)

        bot_box.addStretch()
        bot_box.addWidget(btn_guide)
        bot_box.addWidget(btn_reset_all)
        bot_box.addStretch()

        scroll_layout.addLayout(bot_box)

        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def create_button_group_card(self, title: str, button_names: list) -> QFrame:
        """Create a card container for a group of buttons with headers matching the screenshot."""
        card = QFrame()
        card.setObjectName("GlassCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(12, 10, 12, 10)

        # Group Title
        lbl_title = QLabel(title)
        lbl_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")
        lbl_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(lbl_title)

        # Column Header Legend Row
        leg_row = QHBoxLayout()
        leg_row.setContentsMargins(50, 0, 0, 4)
        lbl_h_map = QLabel("Mapping")
        lbl_h_map.setStyleSheet("font-weight: bold; font-size: 11px; color: #a992cb;")

        lbl_h_blk = QLabel("Block")
        lbl_h_blk.setStyleSheet("font-weight: bold; font-size: 11px; color: #00f5a0;")

        lbl_h_smap = QLabel("Shift Map")
        lbl_h_smap.setStyleSheet("font-weight: bold; font-size: 11px; color: #a855f7;")

        lbl_h_sblk = QLabel("S. Blk")
        lbl_h_sblk.setStyleSheet("font-weight: bold; font-size: 11px; color: #a992cb;")

        leg_row.addWidget(lbl_h_map, stretch=3)
        leg_row.addSpacing(40)
        leg_row.addWidget(lbl_h_blk, stretch=1)
        leg_row.addWidget(lbl_h_smap, stretch=3)
        leg_row.addSpacing(40)
        leg_row.addWidget(lbl_h_sblk, stretch=1)
        layout.addLayout(leg_row)

        for bname in button_names:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(6)

            # Button Name Label
            lbl_btn = QLabel(bname)
            lbl_btn.setStyleSheet("font-weight: bold; font-size: 12px; min-width: 50px;")

            # Standard Mapping QLineEdit with Sleek Outline
            edit_std = QLineEdit()
            edit_std.setPlaceholderText("Gamepad Default")
            edit_std.editingFinished.connect(lambda name=bname, edit=edit_std: self.on_std_mapping_edited(name, edit.text()))

            # Record [R] button for Standard Map
            btn_rec_std = QPushButton("[R]")
            btn_rec_std.setFixedWidth(32)
            btn_rec_std.setObjectName("PrimaryBtn")
            btn_rec_std.clicked.connect(lambda ch=False, name=bname, edit=edit_std: self.record_for_edit(name, edit, "Standard"))

            # Native Block Checkbox
            chk_block = QCheckBox()
            chk_block.setChecked(True)
            chk_block.stateChanged.connect(lambda state, name=bname: self.on_block_xinput_changed(name, state))

            # Shift Mapping QLineEdit with Sleek Outline
            edit_shift = QLineEdit()
            edit_shift.setPlaceholderText("Unmapped")
            edit_shift.editingFinished.connect(lambda name=bname, edit=edit_shift: self.on_shift_mapping_edited(name, edit.text()))

            # Record [R] button for Shift Map
            btn_rec_shift = QPushButton("[R]")
            btn_rec_shift.setFixedWidth(32)
            btn_rec_shift.setObjectName("PrimaryBtn")
            btn_rec_shift.clicked.connect(lambda ch=False, name=bname, edit=edit_shift: self.record_for_edit(name, edit, "Shift"))

            # Shift Block Checkbox
            chk_sblock = QCheckBox()
            chk_sblock.setChecked(True)
            chk_sblock.stateChanged.connect(lambda state, name=bname: self.on_shift_block_changed(name, state))

            row_layout.addWidget(lbl_btn)
            row_layout.addWidget(edit_std)
            row_layout.addWidget(btn_rec_std)
            row_layout.addWidget(chk_block)
            row_layout.addWidget(edit_shift)
            row_layout.addWidget(btn_rec_shift)
            row_layout.addWidget(chk_sblock)

            layout.addLayout(row_layout)
            self.row_widgets[bname] = (edit_std, btn_rec_std, chk_block, edit_shift, btn_rec_shift, chk_sblock)

        return card

    def refresh_shift_layer_combobox(self):
        self.combo_layers.blockSignals(True)
        self.combo_layers.clear()
        config = getattr(self.app, 'controller_config', None)
        if config:
            layers = config.get_shift_layers()
            for l in layers:
                self.combo_layers.addItem(l.get("name", "Shift Layer"))
        else:
            self.combo_layers.addItem("Shift Layer 1")
        self.combo_layers.blockSignals(False)

    def on_layer_selected(self, index):
        if index < 0:
            return
        self.active_layer_idx = index
        self.load_config_values()

    def save_shift_layer_params(self):
        config = getattr(self.app, 'controller_config', None)
        if not config:
            return
        layers = config.get_shift_layers()
        if self.active_layer_idx < len(layers):
            trig = self.combo_shift_trig.currentText()
            mod = self.combo_shift_mod.currentText()
            mode = "toggle" if self.radio_toggle.isChecked() else "hold"
            layers[self.active_layer_idx]["trigger_button"] = "" if trig == "None" else trig
            layers[self.active_layer_idx]["modifier_button"] = "" if mod == "None" else mod
            layers[self.active_layer_idx]["mode"] = mode
            config.set_shift_layers(layers)
            self.app.save_config()

    def on_std_mapping_edited(self, button_name: str, new_val: str):
        config = getattr(self.app, 'controller_config', None)
        if config:
            val = new_val.strip()
            if val:
                config.set("mappings", button_name.lower(), val)
            else:
                config.remove_option("mappings", button_name.lower())
            self.app.save_config()

    def on_shift_mapping_edited(self, button_name: str, new_val: str):
        config = getattr(self.app, 'controller_config', None)
        if config:
            val = new_val.strip()
            layers = config.get_shift_layers()
            if self.active_layer_idx < len(layers):
                if val:
                    layers[self.active_layer_idx]["mappings"][button_name.lower()] = val
                else:
                    layers[self.active_layer_idx]["mappings"].pop(button_name.lower(), None)
                config.set_shift_layers(layers)
                self.app.save_config()

    def on_block_xinput_changed(self, button_name: str, state):
        config = getattr(self.app, 'controller_config', None)
        if config:
            val = (state == Qt.CheckState.Checked.value or state is True)
            config.set("block_xinput", button_name.lower(), str(val).lower())
            self.app.save_config()

    def on_shift_block_changed(self, button_name: str, state):
        config = getattr(self.app, 'controller_config', None)
        if config:
            val = (state == Qt.CheckState.Checked.value or state is True)
            layers = config.get_shift_layers()
            if self.active_layer_idx < len(layers):
                layers[self.active_layer_idx]["block_xinput"][button_name.lower()] = val
                config.set_shift_layers(layers)
                self.app.save_config()

    def record_for_edit(self, button_name: str, target_edit: QLineEdit, target_layer: str):
        dlg = KeyRecorderDialog(button_name, self)
        if dlg.exec() == QDialog.DialogCode.Accepted and dlg.recorded_binding:
            target_edit.setText(dlg.recorded_binding)
            if target_layer == "Standard":
                self.on_std_mapping_edited(button_name, dlg.recorded_binding)
            else:
                self.on_shift_mapping_edited(button_name, dlg.recorded_binding)

    def add_shift_layer(self):
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.add_shift_layer(name=f"Shift Layer {self.combo_layers.count() + 1}")
            self.app.save_config()
            self.refresh_shift_layer_combobox()
            self.combo_layers.setCurrentIndex(self.combo_layers.count() - 1)

    def delete_shift_layer(self):
        if self.combo_layers.count() > 1:
            config = getattr(self.app, 'controller_config', None)
            if config:
                layers = config.get_shift_layers()
                if self.active_layer_idx < len(layers):
                    config.remove_shift_layer(layers[self.active_layer_idx].get("id", ""))
                    self.app.save_config()
                    self.refresh_shift_layer_combobox()
                    self.combo_layers.setCurrentIndex(0)

    def reset_all_remappings(self):
        config = getattr(self.app, 'controller_config', None)
        if config:
            config.data["mappings"] = {}
            layers = config.get_shift_layers()
            for l in layers:
                l["mappings"] = {}
            config.set_shift_layers(layers)
            self.app.save_config()
            self.load_config_values()

    def load_config_values(self):
        self.refresh_shift_layer_combobox()
        config = getattr(self.app, 'controller_config', None)
        if not config:
            return

        layers = config.get_shift_layers()
        if self.active_layer_idx >= len(layers):
            self.active_layer_idx = 0

        active_layer = layers[self.active_layer_idx] if layers else {}

        # Set Shift Key / Modifier / Mode
        trig = active_layer.get("trigger_button", "")
        mod = active_layer.get("modifier_button", "")
        mode = active_layer.get("mode", "hold")
        pass_through = active_layer.get("pass_through", False)

        self.combo_shift_trig.blockSignals(True)
        self.combo_shift_trig.setCurrentText(trig if trig else "None")
        self.combo_shift_trig.blockSignals(False)

        self.combo_shift_mod.blockSignals(True)
        self.combo_shift_mod.setCurrentText(mod if mod else "None")
        self.combo_shift_mod.blockSignals(False)

        self.radio_hold.blockSignals(True)
        self.radio_toggle.blockSignals(True)
        self.radio_hold.setChecked(mode == "hold")
        self.radio_toggle.setChecked(mode == "toggle")
        self.radio_hold.blockSignals(False)
        self.radio_toggle.blockSignals(False)

        self.chk_passthrough.blockSignals(True)
        self.chk_passthrough.setChecked(bool(pass_through))
        self.chk_passthrough.blockSignals(False)

        # Fill Each Row
        std_mappings = config.data.get("mappings", {})
        block_xinput = config.data.get("block_xinput", {})

        shift_mappings = active_layer.get("mappings", {})
        shift_block_xinput = active_layer.get("block_xinput", {})

        for bname, (edit_std, btn_rec_std, chk_block, edit_shift, btn_rec_shift, chk_sblock) in self.row_widgets.items():
            b_key = bname.lower()

            # Standard
            edit_std.blockSignals(True)
            edit_std.setText(std_mappings.get(b_key, ""))
            edit_std.blockSignals(False)

            chk_block.blockSignals(True)
            chk_block.setChecked(config.getboolean("block_xinput", b_key, True))
            chk_block.blockSignals(False)

            # Shift
            edit_shift.blockSignals(True)
            edit_shift.setText(shift_mappings.get(b_key, ""))
            edit_shift.blockSignals(False)

            chk_sblock.blockSignals(True)
            chk_sblock.setChecked(bool(shift_block_xinput.get(b_key, True)))
            chk_sblock.blockSignals(False)

    def show_remapping_guide(self):
        msg = QMessageBox(self)
        msg.setWindowTitle("Remapping Guide")
        msg.setText(
            "• Type keyboard keys or mouse bindings directly into the outlined text boxes, OR click [R] to record.\n"
            "• Single Key: e.g. 'a', 'space', 'shift', 'tab'\n"
            "• Combo Keys: e.g. 'ctrl+c', 'alt+tab', 'shift+space'\n"
            "• Mouse Clicks: e.g. 'mouse_left', 'mouse_right', 'mouse_middle', 'mouse_x1'\n"
            "• Scroll Wheel: e.g. 'scroll_up:1:oneshot:0.05' or 'scroll_down:3:continuous:0.05'\n\n"
            "• Block Checkbox: Suppresses the native gamepad input when pressed.\n"
            "• S. Blk Checkbox: Suppresses the native gamepad input when the Shift Layer is active."
        )
        msg.exec()
