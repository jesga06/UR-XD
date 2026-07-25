"""
Remapping View Module for PySide6 UI (gui_v2).

Provides a complete button remapping interface with:
  - Shift layer management (add / rename / delete / select)
  - Categorised button mapping grids (Face, Shoulder, D-Pad, System)
  - Per-button: standard mapping field, interactive key recorder, XInput
    block checkbox, and per-shift-layer mapping field
  - Debounced (300 ms) config disk writes

All config mutations write through the live ControllerConfig instance.
"""

import sys
import os
from typing import Dict, Optional, Any, List, Tuple

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QLabel,
    QPushButton, QLineEdit, QCheckBox, QComboBox, QGroupBox,
    QRadioButton, QButtonGroup, QScrollArea, QFrame, QInputDialog,
    QMessageBox, QApplication
)
from PySide6.QtCore import Qt, Slot, QTimer

# Add root src to path so sibling imports resolve when run standalone
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from gui_v2.dialogs.key_recorder_dialog import KeyRecorderDialog


# ---------------------------------------------------------------------------
# Button groups & display names
# ---------------------------------------------------------------------------
BUTTON_GROUPS: Dict[str, List[Tuple[str, str]]] = {
    "Face Buttons": [
        ("a", "A"), ("b", "B"), ("x", "X"), ("y", "Y"),
    ],
    "Shoulders & Sticks": [
        ("lb", "LB"), ("rb", "RB"), ("lt", "LT"), ("rt", "RT"),
        ("l3", "L3"), ("r3", "R3"),
    ],
    "D-Pad": [
        ("dpad_up", "UP"), ("dpad_down", "DOWN"),
        ("dpad_left", "LEFT"), ("dpad_right", "RIGHT"),
    ],
    "System": [
        ("select", "SELECT"), ("start", "START"), ("home", "HOME"),
    ],
}

BASE_TRIGGER_BUTTONS = [
    "", "a", "b", "x", "y",
    "lb", "rb", "lt", "rt",
    "l3", "r3", "select", "start", "home",
    "dpad_up", "dpad_down", "dpad_left", "dpad_right",
]


# ---------------------------------------------------------------------------
# QSS helpers
# ---------------------------------------------------------------------------
_CARD_STYLE = """
QGroupBox {
    background-color: rgba(22, 16, 36, 0.85);
    border: 1px solid rgba(168, 85, 247, 0.35);
    border-radius: 10px;
    margin-top: 12px;
    color: #a855f7;
    font-weight: bold;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
}
"""

_INPUT_STYLE = """
QLineEdit, QComboBox, QSpinBox {
    background-color: #161024;
    border: 1.5px solid #a855f7;
    border-radius: 6px;
    color: #ffffff;
    padding: 3px 6px;
}
QLineEdit::placeholder { color: rgba(255,255,255,0.4); font-style: italic; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background: #161024; color: #ffffff; }
"""

_CB_STYLE = """
QCheckBox { color: #64748b; }
QCheckBox::indicator { width: 16px; height: 16px; border-radius: 4px;
    border: 1px solid rgba(168,85,247,0.4); background: #161024; }
QCheckBox::indicator:checked { background: #a855f7; border-color: #a855f7; }
"""

_BTN_STYLE = """
QPushButton {
    background-color: rgba(168, 85, 247, 0.2);
    border: 1px solid rgba(168, 85, 247, 0.4);
    border-radius: 5px; color: #ffffff; padding: 2px 8px; font-size: 11px;
}
QPushButton:hover { background-color: rgba(168, 85, 247, 0.4); }
QPushButton:pressed { background-color: #7500ab; }
"""

_BTN_DANGER = """
QPushButton {
    background-color: rgba(220,38,38,0.2); border: 1px solid rgba(220,38,38,0.4);
    border-radius: 5px; color: #ffffff; padding: 2px 8px; font-size: 11px;
}
QPushButton:hover { background-color: rgba(220,38,38,0.4); }
"""

_HEADER_LABEL = "color: rgba(255,255,255,0.5); font-size: 10px; font-weight: bold;"
_BTN_LABEL = "color: #a855f7; font-weight: bold; font-size: 12px;"


class RemappingView(QWidget):
    """
    Primary remapping tab view.  Exposes shift layer management and
    per-button mapping, block, and shift-map controls.
    """

    def __init__(self, config_manager: Any, parent=None):
        super().__init__(parent)
        self.config = config_manager

        # Debounced write: fires 300 ms after the last change
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(300)
        self.save_timer.timeout.connect(self._do_save)

        # Track per-button UI widget references for programmatic updates
        # key → { 'std': QLineEdit, 'blk': QCheckBox, 'shift': QLineEdit }
        self._row_widgets: Dict[str, Dict[str, QWidget]] = {}

        self.setup_ui()

    def _get_dynamic_extra_buttons(self) -> List[str]:
        """
        Dynamically inspects config data to resolve extra hardware buttons
        or hardware chords (e.g. M1, M2, L4, R4).
        """
        extra_buttons: List[str] = []
        data = getattr(self.config, 'data', {}) if self.config else {}
        if not isinstance(data, dict):
            return extra_buttons

        eb_dict = data.get("extra_buttons", {})
        if isinstance(eb_dict, dict) and eb_dict:
            extra_buttons.extend(list(eb_dict.keys()))
        else:
            eb_settings = data.get("settings", {}).get("extra_inputs", [])
            if isinstance(eb_settings, list):
                extra_buttons.extend([str(x) for x in eb_settings])
            elif isinstance(eb_settings, dict):
                extra_buttons.extend(list(eb_settings.keys()))

        hw_chords = data.get("hardware_chords", {})
        if isinstance(hw_chords, dict):
            for chord_name in hw_chords.keys():
                if chord_name not in extra_buttons:
                    extra_buttons.append(chord_name)

        return extra_buttons

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def setup_ui(self) -> None:
        """Assembles the complete remapping view."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(12)

        # Wrap in scroll area so low-resolution screens don't clip content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        inner_widget = QWidget()
        inner_layout = QVBoxLayout(inner_widget)
        inner_layout.setContentsMargins(0, 0, 0, 0)
        inner_layout.setSpacing(12)

        # 1. Shift layer management card
        inner_layout.addWidget(self._build_shift_layer_panel())

        # 2. Button mapping grids (2-column layout)
        grids_layout = QHBoxLayout()
        grids_layout.setSpacing(12)

        left_col = QVBoxLayout()
        right_col = QVBoxLayout()

        group_names = list(BUTTON_GROUPS.keys())
        for i, name in enumerate(group_names):
            grid_card = self._build_mapping_grid(name, BUTTON_GROUPS[name])
            if i % 2 == 0:
                left_col.addWidget(grid_card)
            else:
                right_col.addWidget(grid_card)

        # Dynamic Extra Buttons card
        extra_btns = self._get_dynamic_extra_buttons()
        if extra_btns:
            extra_tuples = [(b.lower(), b.upper()) for b in extra_btns]
            extra_card = self._build_mapping_grid("Extra Buttons", extra_tuples)
            right_col.addWidget(extra_card)

        left_col.addStretch()
        right_col.addStretch()
        grids_layout.addLayout(left_col)
        grids_layout.addLayout(right_col)
        inner_layout.addLayout(grids_layout)
        inner_layout.addStretch()

        scroll.setWidget(inner_widget)
        outer.addWidget(scroll)

    def _build_shift_layer_panel(self) -> QGroupBox:
        """Builds the shift layer configuration card."""
        group = QGroupBox("SHIFT LAYERS CONFIGURATION & MANAGEMENT")
        group.setStyleSheet(_CARD_STYLE)
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Row 1: Layer selector + management buttons
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Active Layer:"))

        self.layer_selector = QComboBox()
        self.layer_selector.setStyleSheet(_INPUT_STYLE)
        self.layer_selector.setMinimumWidth(200)
        self._populate_layer_selector()
        self.layer_selector.currentIndexChanged.connect(self._on_layer_changed)
        row1.addWidget(self.layer_selector)

        btn_add = QPushButton("＋ Add Layer")
        btn_add.setStyleSheet(_BTN_STYLE)
        btn_add.clicked.connect(self._add_layer)

        btn_rename = QPushButton("✏️ Rename")
        btn_rename.setStyleSheet(_BTN_STYLE)
        btn_rename.clicked.connect(self._rename_layer)

        btn_delete = QPushButton("🗑 Delete")
        btn_delete.setStyleSheet(_BTN_DANGER)
        btn_delete.clicked.connect(self._delete_layer)

        for btn in (btn_add, btn_rename, btn_delete):
            row1.addWidget(btn)
        row1.addStretch()
        layout.addLayout(row1)

        # Row 2: Trigger + Modifier buttons
        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Shift Trigger Key:"))

        trigger_items = list(BASE_TRIGGER_BUTTONS)
        for eb in self._get_dynamic_extra_buttons():
            eb_l = eb.lower()
            if eb_l not in trigger_items:
                trigger_items.append(eb_l)

        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(trigger_items)
        self.trigger_combo.setStyleSheet(_INPUT_STYLE)
        self.trigger_combo.currentTextChanged.connect(self._on_trigger_changed)
        row2.addWidget(self.trigger_combo)

        row2.addSpacing(20)
        row2.addWidget(QLabel("Shift Modifier:"))

        self.modifier_combo = QComboBox()
        self.modifier_combo.addItems(trigger_items)
        self.modifier_combo.setStyleSheet(_INPUT_STYLE)
        self.modifier_combo.currentTextChanged.connect(self._on_modifier_changed)
        row2.addWidget(self.modifier_combo)
        row2.addStretch()
        layout.addLayout(row2)

        # Row 3: Trigger Mode radio buttons
        row3 = QHBoxLayout()
        row3.addWidget(QLabel("Shift Trigger Mode:"))

        self._mode_group = QButtonGroup(self)
        rb_toggle = QRadioButton("Toggle")
        rb_hold = QRadioButton("Hold")
        rb_toggle.setStyleSheet("color: #ffffff; font-size: 11px;")
        rb_hold.setStyleSheet("color: #ffffff; font-size: 11px;")
        self._mode_group.addButton(rb_toggle, 0)
        self._mode_group.addButton(rb_hold, 1)
        rb_hold.setChecked(True)

        self._mode_group.idToggled.connect(self._on_mode_changed)
        row3.addWidget(rb_toggle)
        row3.addWidget(rb_hold)
        row3.addStretch()
        layout.addLayout(row3)

        # Sync UI to current layer
        self._sync_layer_settings()
        return group

    def _build_mapping_grid(self, title: str, buttons: List[Tuple[str, str]]) -> QGroupBox:
        """Builds a categorised grid card for a set of buttons."""
        group = QGroupBox(title.upper())
        group.setStyleSheet(_CARD_STYLE)

        layout = QGridLayout(group)
        layout.setSpacing(4)
        layout.setColumnStretch(1, 3)
        layout.setColumnStretch(3, 3)

        # Header row
        for col, text in enumerate(("Button", "Mapping", "Blk", "Shift Map")):
            lbl = QLabel(text)
            lbl.setStyleSheet(_HEADER_LABEL)
            layout.addWidget(lbl, 0, col, Qt.AlignmentFlag.AlignCenter)

        for row_idx, (key, display) in enumerate(buttons, start=1):
            # Button label
            btn_lbl = QLabel(display)
            btn_lbl.setStyleSheet(_BTN_LABEL)
            layout.addWidget(btn_lbl, row_idx, 0, Qt.AlignmentFlag.AlignCenter)

            # Standard mapping field + record button
            std_container = QWidget()
            std_h = QHBoxLayout(std_container)
            std_h.setContentsMargins(0, 0, 0, 0)
            std_h.setSpacing(3)

            std_edit = QLineEdit()
            std_edit.setPlaceholderText("none")
            std_edit.setStyleSheet(_INPUT_STYLE)
            std_edit.setText(self._get_base_mapping(key))
            std_edit.textChanged.connect(
                lambda text, k=key: self._on_std_mapping_changed(k, text)
            )
            std_h.addWidget(std_edit)

            rec_btn = QPushButton("R")
            rec_btn.setFixedWidth(26)
            rec_btn.setStyleSheet(_BTN_STYLE)
            rec_btn.setToolTip("Record key/mouse input")
            rec_btn.clicked.connect(
                lambda checked, k=key: self.open_recorder_dialog(k, is_shift=False)
            )
            std_h.addWidget(rec_btn)
            layout.addWidget(std_container, row_idx, 1)

            # Block XInput checkbox
            blk_cb = QCheckBox()
            blk_cb.setStyleSheet(_CB_STYLE)
            blk_cb.setChecked(self._get_block_state(key))
            blk_cb.stateChanged.connect(
                lambda state, k=key: self._on_block_changed(k, bool(state))
            )
            layout.addWidget(blk_cb, row_idx, 2, Qt.AlignmentFlag.AlignCenter)

            # Shift mapping field + record button
            shift_container = QWidget()
            shift_h = QHBoxLayout(shift_container)
            shift_h.setContentsMargins(0, 0, 0, 0)
            shift_h.setSpacing(3)

            shift_edit = QLineEdit()
            shift_edit.setPlaceholderText("none")
            shift_edit.setStyleSheet(_INPUT_STYLE)
            shift_edit.setText(self._get_shift_mapping(key))
            shift_edit.textChanged.connect(
                lambda text, k=key: self._on_shift_mapping_changed(k, text)
            )
            shift_h.addWidget(shift_edit)

            shift_rec_btn = QPushButton("R")
            shift_rec_btn.setFixedWidth(26)
            shift_rec_btn.setStyleSheet(_BTN_STYLE)
            shift_rec_btn.setToolTip("Record shift-layer key/mouse input")
            shift_rec_btn.clicked.connect(
                lambda checked, k=key: self.open_recorder_dialog(k, is_shift=True)
            )
            shift_h.addWidget(shift_rec_btn)
            layout.addWidget(shift_container, row_idx, 3)

            # Store widget refs for later programmatic updates
            self._row_widgets[key] = {
                "std": std_edit,
                "blk": blk_cb,
                "shift": shift_edit,
            }

        return group

    # ------------------------------------------------------------------
    # Config read helpers
    # ------------------------------------------------------------------
    def _active_layer(self) -> Optional[Dict[str, Any]]:
        """Returns the currently selected shift layer dict, or None."""
        layers = self.config.get_shift_layers()
        idx = self.layer_selector.currentIndex()
        if 0 <= idx < len(layers):
            return layers[idx]
        return None

    def _get_base_mapping(self, key: str) -> str:
        data = self.config.data
        base_map: Dict[str, Any] = {}
        base_map.update(data.get("extra_buttons", {}))
        base_map.update(data.get("layer_base", {}))
        return str(base_map.get(key.lower(), ""))

    def _get_block_state(self, key: str) -> bool:
        data = self.config.data
        bx: Dict[str, Any] = data.get("block_xinput", {})
        val = bx.get(key.lower(), "false")
        return str(val).lower() in ("true", "1", "yes")

    def _get_shift_mapping(self, key: str) -> str:
        layer = self._active_layer()
        if layer:
            return str(layer.get("mappings", {}).get(key.lower(), ""))
        return ""

    # ------------------------------------------------------------------
    # Config write helpers
    # ------------------------------------------------------------------
    def _set_base_mapping(self, key: str, value: str) -> None:
        if "layer_base" not in self.config.data:
            self.config.data["layer_base"] = {}
        if value:
            self.config.data["layer_base"][key.lower()] = value
        else:
            self.config.data["layer_base"].pop(key.lower(), None)

    def _set_block_state(self, key: str, blocked: bool) -> None:
        if "block_xinput" not in self.config.data:
            self.config.data["block_xinput"] = {}
        self.config.data["block_xinput"][key.lower()] = "true" if blocked else "false"

    def _set_shift_mapping(self, key: str, value: str) -> None:
        layer = self._active_layer()
        if layer is None:
            return
        if "mappings" not in layer:
            layer["mappings"] = {}
        if value:
            layer["mappings"][key.lower()] = value
        else:
            layer["mappings"].pop(key.lower(), None)

    # ------------------------------------------------------------------
    # Debounced save
    # ------------------------------------------------------------------
    def mark_config_dirty(self) -> None:
        """Restarts the 300 ms debounced save timer."""
        self.save_timer.start()

    def _do_save(self) -> None:
        """Called when the debounce timer fires."""
        try:
            self.config.save()
        except Exception as e:
            print(f"[RemappingView] Config save error: {e}")

    # ------------------------------------------------------------------
    # Slot implementations – mapping fields
    # ------------------------------------------------------------------
    @Slot(str)
    def _on_std_mapping_changed(self, key: str, text: str) -> None:
        self._set_base_mapping(key, text.strip())
        self.mark_config_dirty()

    @Slot(int)
    def _on_block_changed(self, key: str, checked: bool) -> None:
        self._set_block_state(key, checked)
        self.mark_config_dirty()

    @Slot(str)
    def _on_shift_mapping_changed(self, key: str, text: str) -> None:
        self._set_shift_mapping(key, text.strip())
        self.mark_config_dirty()

    # ------------------------------------------------------------------
    # Key recorder dialog
    # ------------------------------------------------------------------
    def open_recorder_dialog(self, button_name: str, is_shift: bool = False) -> None:
        """Instantiates and executes KeyRecorderDialog modally."""
        dlg = KeyRecorderDialog(button_name, parent=self)

        def _handle_recorded(target: str, mapping_str: str) -> None:
            widgets = self._row_widgets.get(button_name.lower(), {})
            if is_shift or target == "shift":
                self._set_shift_mapping(button_name.lower(), mapping_str)
                shift_edit: Optional[QLineEdit] = widgets.get("shift")
                if shift_edit:
                    shift_edit.blockSignals(True)
                    shift_edit.setText(mapping_str)
                    shift_edit.blockSignals(False)
            else:
                self._set_base_mapping(button_name.lower(), mapping_str)
                std_edit: Optional[QLineEdit] = widgets.get("std")
                if std_edit:
                    std_edit.blockSignals(True)
                    std_edit.setText(mapping_str)
                    std_edit.blockSignals(False)
            self.mark_config_dirty()

        dlg.input_recorded.connect(_handle_recorded)
        dlg.exec()

    # ------------------------------------------------------------------
    # Shift layer management
    # ------------------------------------------------------------------
    def _populate_layer_selector(self) -> None:
        """Fills the layer dropdown from config without triggering signals."""
        self.layer_selector.blockSignals(True)
        prev_idx = self.layer_selector.currentIndex()
        self.layer_selector.clear()
        for layer in self.config.get_shift_layers():
            self.layer_selector.addItem(
                layer.get("name", layer.get("id", "?")),
                userData=layer.get("id")
            )
        # Restore previous selection if still valid
        new_count = self.layer_selector.count()
        target = max(0, min(prev_idx, new_count - 1))
        self.layer_selector.setCurrentIndex(target)
        self.layer_selector.blockSignals(False)

    def _sync_layer_settings(self) -> None:
        """Syncs trigger / modifier / mode UI to the currently selected layer."""
        layer = self._active_layer()
        if layer is None:
            return

        trigger = layer.get("trigger_button", "") or ""
        modifier = layer.get("modifier_button", "") or ""
        mode = layer.get("mode", "hold") or "hold"

        # Trigger combo
        idx = self.trigger_combo.findText(trigger)
        self.trigger_combo.blockSignals(True)
        self.trigger_combo.setCurrentIndex(max(0, idx))
        self.trigger_combo.blockSignals(False)

        # Modifier combo
        idx2 = self.modifier_combo.findText(modifier)
        self.modifier_combo.blockSignals(True)
        self.modifier_combo.setCurrentIndex(max(0, idx2))
        self.modifier_combo.blockSignals(False)

        # Mode radio
        self._mode_group.blockSignals(True)
        btn = self._mode_group.button(0 if mode == "toggle" else 1)
        if btn:
            btn.setChecked(True)
        self._mode_group.blockSignals(False)

        # Refresh shift mapping fields
        for key, widgets in self._row_widgets.items():
            shift_edit: Optional[QLineEdit] = widgets.get("shift")
            if shift_edit:
                shift_edit.blockSignals(True)
                shift_edit.setText(self._get_shift_mapping(key))
                shift_edit.blockSignals(False)

    @Slot(int)
    def _on_layer_changed(self, idx: int) -> None:
        self._sync_layer_settings()

    @Slot(str)
    def _on_trigger_changed(self, text: str) -> None:
        layer = self._active_layer()
        if layer is not None:
            layer["trigger_button"] = text
            self.mark_config_dirty()

    @Slot(str)
    def _on_modifier_changed(self, text: str) -> None:
        layer = self._active_layer()
        if layer is not None:
            layer["modifier_button"] = text
            self.mark_config_dirty()

    @Slot(int, bool)
    def _on_mode_changed(self, btn_id: int, checked: bool) -> None:
        if not checked:
            return
        layer = self._active_layer()
        if layer is not None:
            layer["mode"] = "toggle" if btn_id == 0 else "hold"
            self.mark_config_dirty()

    def _add_layer(self) -> None:
        name, ok = QInputDialog.getText(self, "Add Shift Layer", "Layer name:")
        if ok and name.strip():
            self.config.add_shift_layer(name=name.strip())
            self._populate_layer_selector()
            self.layer_selector.setCurrentIndex(self.layer_selector.count() - 1)
            self._sync_layer_settings()
            self.mark_config_dirty()

    def _rename_layer(self) -> None:
        layer = self._active_layer()
        if layer is None:
            return
        current_name = layer.get("name", "")
        name, ok = QInputDialog.getText(
            self, "Rename Layer", "New name:", text=current_name
        )
        if ok and name.strip():
            layer["name"] = name.strip()
            self._populate_layer_selector()
            self.mark_config_dirty()

    def _delete_layer(self) -> None:
        layers = self.config.get_shift_layers()
        if len(layers) <= 1:
            QMessageBox.warning(self, "Cannot Delete",
                                "At least one shift layer must remain.")
            return
        layer = self._active_layer()
        if layer is None:
            return
        confirm = QMessageBox.question(
            self, "Delete Layer",
            f"Delete layer \"{layer.get('name', layer['id'])}\"?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.config.remove_shift_layer(layer["id"])
            self._populate_layer_selector()
            self._sync_layer_settings()
            self.mark_config_dirty()


if __name__ == "__main__":
    import json
    from config_manager import ControllerConfig

    app = QApplication(sys.argv)
    app.setStyleSheet("background-color: #0c0914; color: #ffffff;")

    # Use an in-memory config for standalone testing
    cfg = ControllerConfig()
    cfg.data["layer_base"] = {
        "a": "keyboard:space", "b": "keyboard:c", "x": "keyboard:r",
        "y": "keyboard:e", "dpad_up": "keyboard:w", "dpad_down": "keyboard:s",
        "dpad_left": "keyboard:a", "dpad_right": "keyboard:d",
    }

    view = RemappingView(cfg)
    view.setWindowTitle("RemappingView Standalone Test")
    view.resize(1100, 750)
    view.show()

    sys.exit(app.exec())
