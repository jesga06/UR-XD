"""
Remapping View Module for PySide6 UI (gui_v2).

Provides a complete button remapping interface with:
  - Shift layer management (add / rename / delete / select)
  - Categorised button mapping grids (Face, Shoulder, D-Pad, System)
  - Per-button: standard mapping field, standard XInput block checkbox ("Blk"),
    per-shift-layer mapping field, and shift XInput block checkbox ("S.Blk")
  - Debounced (300 ms) config disk writes

All config mutations write through the live ControllerConfig instance.
"""

import sys
import os
import logging
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
from button_matrix import get_extra_button_actions

logger = logging.getLogger('remapping_view')


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
_HEADER_LABEL = "color: rgba(255,255,255,0.5); font-size: 10px; font-weight: bold;"
_BTN_DANGER = "QPushButton { background-color: rgba(220,38,38,0.2); border: 1px solid rgba(220,38,38,0.4); border-radius: 5px; color: #ffffff; padding: 2px 8px; font-size: 11px; } QPushButton:hover { background-color: rgba(220,38,38,0.4); }"


class RemappingView(QWidget):
    """
    Primary remapping tab view. Exposes shift layer management,
    per-button standard mapping/block, and shift mapping/block controls.
    """

    _has_shown_block_warning: bool = False

    def __init__(self, config_manager: Any, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self._cards: List[QGroupBox] = []

        # Debounced write: fires 300 ms after the last change
        self.save_timer = QTimer(self)
        self.save_timer.setSingleShot(True)
        self.save_timer.setInterval(300)
        self.save_timer.timeout.connect(self._do_save)

        # Track per-button UI widget references for programmatic updates
        self._row_widgets: Dict[str, Dict[str, QWidget]] = {}

        self.setup_ui()
        self._setup_theme_sync()

    def _setup_theme_sync(self) -> None:
        try:
            from gui_v2.services.theme_manager import ThemeManager
            tm = ThemeManager.get_instance()
            tm.theme_changed.connect(self.on_theme_changed)
            self.on_theme_changed(tm.tokens)
        except Exception:
            pass

    @Slot(dict)
    def on_theme_changed(self, tokens: dict = None):
        try:
            from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex8
            tm = ThemeManager.get_instance()
            bg_color = tm.get_color("background")
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")

            bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
            bg_inner = color_to_rgba_str(bg_color, alpha_override=0.60)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)
            accent_1_hex = color_to_hex8(accent_1)
            accent_1_subtle = color_to_rgba_str(accent_1, alpha_override=0.20)
            accent_1_border = color_to_rgba_str(accent_1, alpha_override=0.50)

            card_qss = f"""
            QGroupBox {{
                background-color: {bg_glass};
                border: 1px solid {border_glass};
                border-radius: 10px;
                margin-top: 12px;
                color: {accent_1_hex};
                font-weight: bold;
                font-size: 11px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 6px;
                color: {accent_1_hex};
            }}
            """
            for card in getattr(self, '_cards', []):
                if card:
                    card.setStyleSheet(card_qss)

            input_qss = f"""
            QLineEdit, QComboBox, QSpinBox {{
                background-color: {bg_inner};
                border: 1.5px solid {border_glass};
                border-radius: 6px;
                color: #ffffff;
                padding: 3px 6px;
            }}
            QLineEdit:focus, QComboBox:focus {{
                border: 1.5px solid {accent_1_hex};
            }}
            QLineEdit::placeholder {{ color: rgba(255,255,255,0.4); font-style: italic; }}
            QComboBox QAbstractItemView {{ background: {color_to_rgba_str(bg_color, alpha_override=1.0)}; color: #ffffff; }}
            """

            cb_qss = f"""
            QCheckBox {{ color: rgba(255, 255, 255, 0.7); }}
            QCheckBox::indicator {{ width: 16px; height: 16px; border-radius: 4px;
                border: 1px solid {border_glass}; background: {bg_inner}; }}
            QCheckBox::indicator:checked {{ background: {accent_1_hex}; border-color: {accent_1_hex}; }}
            """

            btn_qss = f"""
            QPushButton {{
                background-color: {accent_1_subtle};
                border: 1px solid {accent_1_border};
                border-radius: 5px; color: #ffffff; padding: 2px 8px; font-size: 11px;
            }}
            QPushButton:hover {{ background-color: {color_to_rgba_str(accent_1, alpha_override=0.40)}; }}
            QPushButton:pressed {{ background-color: {accent_1_hex}; }}
            """

            btn_name_qss = f"""
            QLabel#btn_name_label {{
                color: {accent_1_hex};
                font-weight: bold;
                font-size: 12px;
            }}
            """

            # Update QSS globally on child inputs, buttons, checkboxes, card titles & labels
            self.setStyleSheet(card_qss + input_qss + cb_qss + btn_qss + btn_name_qss)
        except RuntimeError:
            pass

    def _get_dynamic_extra_buttons(self) -> List[str]:
        """
        Dynamically inspects config data to resolve extra hardware buttons
        or hardware chords (e.g. M1, M2, L4, R4).
        """
        data = getattr(self.config, 'data', {}) if self.config else {}
        extra_buttons = get_extra_button_actions(data)
        logger.debug(f"[REMAP] _get_dynamic_extra_buttons() -> {extra_buttons}")
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

        # 1. Shift layer management card (compact 2-row layout)
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
        """Builds the shift layer configuration card (compact 2-row layout)."""
        group = QGroupBox("SHIFT LAYERS CONFIGURATION & MANAGEMENT")
        self._cards.append(group)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(10, 6, 10, 8)
        layout.setSpacing(4)

        # Row 1: Layer selector + management buttons
        row1 = QHBoxLayout()
        row1.setSpacing(6)
        row1.addWidget(QLabel("Active Layer:"))

        self.layer_selector = QComboBox()
        self.layer_selector.setMinimumWidth(180)
        self._populate_layer_selector()
        self.layer_selector.currentIndexChanged.connect(self._on_layer_changed)
        row1.addWidget(self.layer_selector)

        btn_add = QPushButton("＋ Add Layer")
        btn_add.clicked.connect(self._add_layer)

        btn_rename = QPushButton("✏️ Rename")
        btn_rename.clicked.connect(self._rename_layer)

        btn_delete = QPushButton("🗑 Delete")
        btn_delete.setStyleSheet(_BTN_DANGER)
        btn_delete.clicked.connect(self._delete_layer)

        for btn in (btn_add, btn_rename, btn_delete):
            row1.addWidget(btn)
        row1.addStretch()
        layout.addLayout(row1)

        # Row 2: Trigger + Modifier + Mode (consolidated layout)
        row2 = QHBoxLayout()
        row2.setSpacing(6)
        row2.addWidget(QLabel("Shift Trigger Key:"))

        trigger_items = list(BASE_TRIGGER_BUTTONS)
        for eb in self._get_dynamic_extra_buttons():
            eb_l = eb.lower()
            if eb_l not in trigger_items:
                trigger_items.append(eb_l)

        self.trigger_combo = QComboBox()
        self.trigger_combo.addItems(trigger_items)
        self.trigger_combo.currentTextChanged.connect(self._on_trigger_changed)
        row2.addWidget(self.trigger_combo)

        row2.addSpacing(10)
        row2.addWidget(QLabel("Shift Modifier:"))

        self.modifier_combo = QComboBox()
        self.modifier_combo.addItems(trigger_items)
        self.modifier_combo.currentTextChanged.connect(self._on_modifier_changed)
        row2.addWidget(self.modifier_combo)

        row2.addSpacing(10)
        row2.addWidget(QLabel("Shift Mode:"))

        self._mode_group = QButtonGroup(self)
        rb_toggle = QRadioButton("Toggle")
        rb_hold = QRadioButton("Hold")
        rb_toggle.setStyleSheet("color: #ffffff; font-size: 11px;")
        rb_hold.setStyleSheet("color: #ffffff; font-size: 11px;")
        self._mode_group.addButton(rb_toggle, 0)
        self._mode_group.addButton(rb_hold, 1)
        rb_hold.setChecked(True)

        self._mode_group.idToggled.connect(self._on_mode_changed)
        row2.addWidget(rb_toggle)
        row2.addWidget(rb_hold)
        row2.addStretch()
        layout.addLayout(row2)

        # Sync UI to current layer
        self._sync_layer_settings()
        return group

    def _build_mapping_grid(self, title: str, buttons: List[Tuple[str, str]]) -> QGroupBox:
        """Builds a categorised grid card for a set of buttons with dual block controls."""
        group = QGroupBox(title.upper())
        self._cards.append(group)

        layout = QGridLayout(group)
        layout.setSpacing(4)
        layout.setColumnStretch(1, 3)
        layout.setColumnStretch(3, 3)

        # Header row
        for col, text in enumerate(("Button", "Mapping", "Blk", "Shift Map", "S.Blk")):
            lbl = QLabel(text)
            lbl.setStyleSheet(_HEADER_LABEL)
            layout.addWidget(lbl, 0, col, Qt.AlignmentFlag.AlignCenter)

        for row_idx, (key, display) in enumerate(buttons, start=1):
            # Button label
            btn_lbl = QLabel(display)
            btn_lbl.setObjectName("btn_name_label")
            layout.addWidget(btn_lbl, row_idx, 0, Qt.AlignmentFlag.AlignCenter)

            # Standard mapping field + record button
            std_container = QWidget()
            std_h = QHBoxLayout(std_container)
            std_h.setContentsMargins(0, 0, 0, 0)
            std_h.setSpacing(3)

            std_edit = QLineEdit()
            std_edit.setPlaceholderText("none")
            std_edit.setText(self._get_base_mapping(key))
            std_edit.textChanged.connect(
                lambda text, k=key: self._on_std_mapping_changed(k, text)
            )
            std_h.addWidget(std_edit)

            rec_btn = QPushButton("R")
            rec_btn.setFixedWidth(26)
            rec_btn.setToolTip("Record standard key/mouse input")
            rec_btn.clicked.connect(
                lambda checked, k=key: self.open_recorder_dialog(k, is_shift=False)
            )
            std_h.addWidget(rec_btn)
            layout.addWidget(std_container, row_idx, 1)

            # Standard Block XInput checkbox
            std_blk_cb = QCheckBox()
            std_blk_cb.setToolTip("Block XInput for standard mapping")
            std_blk_cb.setChecked(self._get_base_block_state(key))
            std_blk_cb.stateChanged.connect(
                lambda state, k=key: self._on_std_block_changed(k, bool(state))
            )
            layout.addWidget(std_blk_cb, row_idx, 2, Qt.AlignmentFlag.AlignCenter)

            # Shift mapping field + record button
            shift_container = QWidget()
            shift_h = QHBoxLayout(shift_container)
            shift_h.setContentsMargins(0, 0, 0, 0)
            shift_h.setSpacing(3)

            shift_edit = QLineEdit()
            shift_edit.setPlaceholderText("none")
            shift_edit.setText(self._get_shift_mapping(key))
            shift_edit.textChanged.connect(
                lambda text, k=key: self._on_shift_mapping_changed(k, text)
            )
            shift_h.addWidget(shift_edit)

            shift_rec_btn = QPushButton("R")
            shift_rec_btn.setFixedWidth(26)
            shift_rec_btn.setToolTip("Record shift-layer key/mouse input")
            shift_rec_btn.clicked.connect(
                lambda checked, k=key: self.open_recorder_dialog(k, is_shift=True)
            )
            shift_h.addWidget(shift_rec_btn)
            layout.addWidget(shift_container, row_idx, 3)

            # Shift Block XInput checkbox
            shift_blk_cb = QCheckBox()
            shift_blk_cb.setToolTip("Block XInput for active shift layer mapping")
            shift_blk_cb.setChecked(self._get_shift_block_state(key))
            shift_blk_cb.stateChanged.connect(
                lambda state, k=key: self._on_shift_block_changed(k, bool(state))
            )
            layout.addWidget(shift_blk_cb, row_idx, 4, Qt.AlignmentFlag.AlignCenter)

            # Store widget refs for later programmatic updates
            self._row_widgets[key] = {
                "std": std_edit,
                "std_blk": std_blk_cb,
                "shift": shift_edit,
                "shift_blk": shift_blk_cb,
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
        data = getattr(self.config, 'data', {})
        base_map: Dict[str, Any] = {}
        base_map.update(data.get("extra_buttons", {}))
        base_map.update(data.get("layer_base", {}))
        val = str(base_map.get(key.lower(), ""))
        logger.debug(f"[REMAP] _get_base_mapping({key!r}) -> {val!r}")
        return val

    def _get_base_block_state(self, key: str) -> bool:
        data = getattr(self.config, 'data', {})
        bx: Dict[str, Any] = data.get("block_xinput", {})
        val = bx.get(key.lower(), "false")
        blocked = str(val).lower() in ("true", "1", "yes")
        logger.debug(f"[REMAP] _get_base_block_state({key!r}) -> {blocked} (raw={val!r})")
        return blocked

    def _get_shift_mapping(self, key: str) -> str:
        layer = self._active_layer()
        if layer:
            val = str(layer.get("mappings", {}).get(key.lower(), ""))
            logger.debug(f"[REMAP] _get_shift_mapping({key!r}) layer={layer.get('id')!r} -> {val!r}")
            return val
        return ""

    def _get_shift_block_state(self, key: str) -> bool:
        layer = self._active_layer()
        if layer:
            bx: Dict[str, Any] = layer.get("block_xinput", {})
            val = bx.get(key.lower(), "false")
            blocked = str(val).lower() in ("true", "1", "yes")
            logger.debug(f"[REMAP] _get_shift_block_state({key!r}) -> {blocked} (raw={val!r})")
            return blocked
        return False

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
        logger.debug(f"[REMAP] _set_base_mapping({key!r}, {value!r}) — layer_base={self.config.data.get('layer_base')}")

    def _set_base_block_state(self, key: str, blocked: bool) -> None:
        if "block_xinput" not in self.config.data:
            self.config.data["block_xinput"] = {}
        self.config.data["block_xinput"][key.lower()] = "true" if blocked else "false"
        logger.debug(f"[REMAP] _set_base_block_state({key!r}, {blocked}) — block_xinput={self.config.data.get('block_xinput')}")

    def _set_shift_mapping(self, key: str, value: str) -> None:
        layer = self._active_layer()
        if layer is None:
            logger.warning(f"[REMAP] _set_shift_mapping({key!r}) called but no active layer")
            return
        if "mappings" not in layer:
            layer["mappings"] = {}
        if value:
            layer["mappings"][key.lower()] = value
        else:
            layer["mappings"].pop(key.lower(), None)
        logger.debug(f"[REMAP] _set_shift_mapping({key!r}, {value!r}) — layer={layer.get('id')!r} mappings={layer.get('mappings')}")

    def _set_shift_block_state(self, key: str, blocked: bool) -> None:
        layer = self._active_layer()
        if layer is None:
            logger.warning(f"[REMAP] _set_shift_block_state({key!r}) called but no active layer")
            return
        if "block_xinput" not in layer:
            layer["block_xinput"] = {}
        layer["block_xinput"][key.lower()] = "true" if blocked else "false"
        logger.debug(f"[REMAP] _set_shift_block_state({key!r}, {blocked}) — layer={layer.get('id')!r} block_xinput={layer.get('block_xinput')}")

    # ------------------------------------------------------------------
    # Auto-blocking & Warning Notification
    # ------------------------------------------------------------------
    def _show_double_input_warning_once(self) -> None:
        """Shows double input warning notice once per GUI session."""
        if not RemappingView._has_shown_block_warning:
            RemappingView._has_shown_block_warning = True
            QMessageBox.information(
                self,
                "Block XInput Auto-Activated",
                "Block XInput has been automatically enabled for this remapped button.\n\n"
                "If Block XInput is disabled on a remapped button, games will receive "
                "both native controller input and remapped key/macro input simultaneously (double inputs)."
            )

    def _auto_enable_std_block(self, key: str) -> None:
        """Auto-enables Standard Block XInput checkbox when base mapping is set."""
        widgets = self._row_widgets.get(key.lower(), {})
        std_blk_cb: Optional[QCheckBox] = widgets.get("std_blk")
        if std_blk_cb and not std_blk_cb.isChecked():
            std_blk_cb.blockSignals(True)
            std_blk_cb.setChecked(True)
            std_blk_cb.blockSignals(False)
            self._set_base_block_state(key, True)
            self.mark_config_dirty()
            self._show_double_input_warning_once()

    def _auto_enable_shift_block(self, key: str) -> None:
        """Auto-enables Shift Block XInput checkbox when shift mapping is set."""
        widgets = self._row_widgets.get(key.lower(), {})
        shift_blk_cb: Optional[QCheckBox] = widgets.get("shift_blk")
        if shift_blk_cb and not shift_blk_cb.isChecked():
            shift_blk_cb.blockSignals(True)
            shift_blk_cb.setChecked(True)
            shift_blk_cb.blockSignals(False)
            self._set_shift_block_state(key, True)
            self.mark_config_dirty()
            self._show_double_input_warning_once()

    # ------------------------------------------------------------------
    # Shift Key Home Button + Hold Warning
    # ------------------------------------------------------------------
    def _is_home_hold_warning_condition(self) -> bool:
        """Returns True if the active shift layer trigger is Home/Guide and mode is Hold."""
        layer = self._active_layer()
        if layer is None:
            return False
        trig = str(layer.get("trigger_button", "")).strip().lower()
        mode = str(layer.get("mode", "")).strip().lower()
        return trig in ("home", "guide") and mode == "hold"

    def _check_home_hold_warning(self) -> None:
        """Shows warning notice if shift trigger is Home/Guide in Hold mode."""
        if self._is_home_hold_warning_condition():
            QMessageBox.warning(
                self,
                "Recommended Setting Notice",
                "Holding the Home button for several seconds may force turn off your controller or trigger OS shortcuts.\n\n"
                "It is strongly recommended to set the Shift Mode to 'toggle' instead of 'hold' when using the Home button as your Shift Key."
            )

    # ------------------------------------------------------------------
    # Debounced save
    # ------------------------------------------------------------------
    def mark_config_dirty(self) -> None:
        """Restarts the 300 ms debounced save timer."""
        logger.debug("[REMAP] mark_config_dirty() — debounce timer restarted")
        self.save_timer.start()

    def _do_save(self) -> None:
        """Called when the debounce timer fires."""
        logger.debug(f"[REMAP] _do_save() — writing config to disk: {getattr(self.config, 'filepath', '?')}")
        try:
            self.config.save()
            logger.debug("[REMAP] config saved OK")
        except Exception as e:
            logger.error(f"[REMAP] Config save error: {e}", exc_info=True)

    # ------------------------------------------------------------------
    # Slot implementations – mapping fields
    # ------------------------------------------------------------------
    @Slot(str)
    def _on_std_mapping_changed(self, key: str, text: str) -> None:
        clean_text = text.strip()
        self._set_base_mapping(key, clean_text)
        self.mark_config_dirty()
        if clean_text:
            self._auto_enable_std_block(key)

    @Slot(int)
    def _on_std_block_changed(self, key: str, checked: bool) -> None:
        self._set_base_block_state(key, checked)
        self.mark_config_dirty()
        if not checked:
            base_map = self._get_base_mapping(key)
            if base_map:
                self._show_double_input_warning_once()

    @Slot(str)
    def _on_shift_mapping_changed(self, key: str, text: str) -> None:
        clean_text = text.strip()
        self._set_shift_mapping(key, clean_text)
        self.mark_config_dirty()
        if clean_text:
            self._auto_enable_shift_block(key)

    @Slot(int)
    def _on_shift_block_changed(self, key: str, checked: bool) -> None:
        self._set_shift_block_state(key, checked)
        self.mark_config_dirty()
        if not checked:
            shift_map = self._get_shift_mapping(key)
            if shift_map:
                self._show_double_input_warning_once()

    # ------------------------------------------------------------------
    # Key recorder dialog
    # ------------------------------------------------------------------
    def open_recorder_dialog(self, button_name: str, is_shift: bool = False) -> None:
        """Instantiates and executes KeyRecorderDialog modally."""
        logger.debug(f"[REMAP] open_recorder_dialog(button_name={button_name!r} is_shift={is_shift})")
        dlg = KeyRecorderDialog(button_name, parent=self)

        def _handle_recorded(target: str, mapping_str: str) -> None:
            logger.debug(f"[REMAP] input_recorded signal: target={target!r} mapping={mapping_str!r} for button={button_name!r}")
            widgets = self._row_widgets.get(button_name.lower(), {})
            if is_shift or target == "shift":
                self._set_shift_mapping(button_name.lower(), mapping_str)
                shift_edit: Optional[QLineEdit] = widgets.get("shift")
                if shift_edit:
                    shift_edit.blockSignals(True)
                    shift_edit.setText(mapping_str)
                    shift_edit.blockSignals(False)
                self._auto_enable_shift_block(button_name.lower())
            else:
                self._set_base_mapping(button_name.lower(), mapping_str)
                std_edit: Optional[QLineEdit] = widgets.get("std")
                if std_edit:
                    std_edit.blockSignals(True)
                    std_edit.setText(mapping_str)
                    std_edit.blockSignals(False)
                self._auto_enable_std_block(button_name.lower())
            self.mark_config_dirty()

        dlg.input_recorded.connect(_handle_recorded)

        # Connect live UDP telemetry worker if available on main window
        main_win = self.window()
        udp_worker = getattr(main_win, 'udp_worker', None)
        logger.debug(f"[REMAP] UDP worker found: {udp_worker is not None} has telemetry_received: {hasattr(udp_worker, 'telemetry_received') if udp_worker else False}")
        if udp_worker and hasattr(udp_worker, 'telemetry_received'):
            udp_worker.telemetry_received.connect(dlg.update_telemetry)
            logger.debug("[REMAP] Connected telemetry_received -> dlg.update_telemetry")

        try:
            dlg.exec()
        finally:
            if udp_worker and hasattr(udp_worker, 'telemetry_received'):
                try:
                    udp_worker.telemetry_received.disconnect(dlg.update_telemetry)
                    logger.debug("[REMAP] Disconnected telemetry_received")
                except Exception:
                    pass

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
                layer.get("name", layer.get("id", "")),
                userData=layer["id"]
            )
        target_idx = max(0, min(prev_idx, self.layer_selector.count() - 1))
        self.layer_selector.setCurrentIndex(target_idx)
        self.layer_selector.blockSignals(False)

    def _sync_layer_settings(self) -> None:
        """Updates Trigger, Modifier, Mode, and shift mapping/block fields for active layer."""
        layer = self._active_layer()
        if layer is None:
            return

        trig = layer.get("trigger_button", "")
        self.trigger_combo.blockSignals(True)
        idx = self.trigger_combo.findText(trig, Qt.MatchFlag.MatchExactly)
        self.trigger_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.trigger_combo.blockSignals(False)

        mod = layer.get("modifier_button", "")
        self.modifier_combo.blockSignals(True)
        idx = self.modifier_combo.findText(mod, Qt.MatchFlag.MatchExactly)
        self.modifier_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.modifier_combo.blockSignals(False)

        mode = layer.get("mode", "hold")
        btn_id = 0 if mode == "toggle" else 1
        self._mode_group.blockSignals(True)
        btn = self._mode_group.button(btn_id)
        if btn:
            btn.setChecked(True)
        self._mode_group.blockSignals(False)

        # Refresh shift mapping fields and shift block checkboxes
        for key, widgets in self._row_widgets.items():
            shift_edit: Optional[QLineEdit] = widgets.get("shift")
            if shift_edit:
                shift_edit.blockSignals(True)
                shift_edit.setText(self._get_shift_mapping(key))
                shift_edit.blockSignals(False)

            shift_blk_cb: Optional[QCheckBox] = widgets.get("shift_blk")
            if shift_blk_cb:
                shift_blk_cb.blockSignals(True)
                shift_blk_cb.setChecked(self._get_shift_block_state(key))
                shift_blk_cb.blockSignals(False)

    @Slot(int)
    def _on_layer_changed(self, idx: int) -> None:
        self._sync_layer_settings()

    @Slot(str)
    def _on_trigger_changed(self, text: str) -> None:
        layer = self._active_layer()
        if layer is not None:
            layer["trigger_button"] = text
            self.mark_config_dirty()
            self._check_home_hold_warning()

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
            self._check_home_hold_warning()

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
