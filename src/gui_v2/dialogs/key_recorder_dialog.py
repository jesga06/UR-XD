"""
Key Recorder Dialog for PySide6 UI (gui_v2).

Recording logic is a 1:1 port of v2.3-beta's start_recording() method.
- Keyboard: persistent listener & Qt event filter, appends unique key names to a list
- Mouse click: captures button name, stops both listeners immediately
- Mouse scroll: stops both listeners, shows scroll settings panel
- Gamepad: captures live UDP telemetry rising-edge button presses

All pynput events are dispatched to the Qt main thread via QTimer.singleShot(0).
Listener teardown is guaranteed via try/finally on save/cancel.
"""

import threading
import logging
from typing import Optional, List, Set

logger = logging.getLogger('key_recorder_dialog')

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QRadioButton,
    QButtonGroup, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QKeyEvent

try:
    import pynput
    from pynput import keyboard as pynput_keyboard
    from pynput import mouse as pynput_mouse
    _PYNPUT_AVAILABLE = True
except ImportError:
    _PYNPUT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Styling
# ---------------------------------------------------------------------------
_CARD_STYLE = """
QGroupBox {
    background-color: rgba(22, 16, 36, 0.85);
    border: 1px solid rgba(168, 85, 247, 0.35);
    border-radius: 10px;
    margin-top: 10px;
    color: #ffffff;
    font-weight: bold;
    font-size: 11px;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    padding: 0 6px;
    color: #a855f7;
}
"""

_INPUT_STYLE = """
QComboBox, QSpinBox, QDoubleSpinBox {
    background-color: rgba(22, 16, 36, 0.85);
    border: 1.5px solid #a855f7;
    border-radius: 6px;
    color: #ffffff;
    padding: 4px 8px;
}
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background: #161024; color: #ffffff; }
"""

_BTN_ACCENT = """
QPushButton {
    background-color: rgba(168, 85, 247, 0.2);
    border: 1px solid rgba(168, 85, 247, 0.5);
    border-radius: 6px;
    color: #ffffff;
    padding: 5px 12px;
    font-size: 11px;
}
QPushButton:hover {
    background-color: rgba(168, 85, 247, 0.4);
    border: 1px solid #a855f7;
}
QPushButton:pressed { background-color: #7500ab; }
"""

_BTN_SAVE = """
QPushButton {
    background-color: rgba(34, 197, 94, 0.2);
    border: 1px solid rgba(34, 197, 94, 0.5);
    border-radius: 6px;
    color: #ffffff;
    padding: 5px 14px;
    font-size: 11px;
}
QPushButton:hover { background-color: rgba(34, 197, 94, 0.4); }
QPushButton:pressed { background-color: #14532d; }
"""

_BTN_SHIFT = """
QPushButton {
    background-color: rgba(34, 100, 94, 0.25);
    border: 1px solid rgba(34, 197, 150, 0.5);
    border-radius: 6px;
    color: #ffffff;
    padding: 5px 14px;
    font-size: 11px;
}
QPushButton:hover { background-color: rgba(34, 197, 150, 0.35); }
"""

_BTN_CANCEL = """
QPushButton {
    background-color: rgba(100, 100, 100, 0.2);
    border: 1px solid rgba(150, 150, 150, 0.4);
    border-radius: 6px;
    color: #aaaaaa;
    padding: 5px 12px;
    font-size: 11px;
}
QPushButton:hover { background-color: rgba(150, 150, 150, 0.3); }
"""

_BTN_CLEAR = """
QPushButton {
    background-color: rgba(220, 38, 38, 0.2);
    border: 1px solid rgba(220, 38, 38, 0.4);
    border-radius: 5px;
    color: #ffffff;
    padding: 2px 8px;
    font-size: 11px;
}
QPushButton:hover { background-color: rgba(220, 38, 38, 0.4); }
"""


class KeyRecorderDialog(QDialog):
    """
    Modal dialog for recording a key/mouse/gamepad binding.

    Signals
    -------
    input_recorded(target: str, mapping: str)
        Emitted on Save Standard ("standard") or Save Shift ("shift").
    """

    input_recorded = Signal(str, str)

    def __init__(self, button_name: str, parent=None):
        super().__init__(parent)
        self.button_name = button_name
        self.setWindowTitle(f"Record Mapping — {button_name.upper()}")
        self.setMinimumWidth(420)
        self.setModal(True)
        self.setStyleSheet("QDialog { background-color: #0f0a1e; color: #ffffff; }")

        # --- state (mirrors beta's locals) ---
        self._recorded_keys: List[str] = []        # accumulated keyboard keys
        self._result: str = ""                     # final mapping string
        self._is_showing_scroll: bool = False
        self._detected_scroll_dir: Optional[str] = None
        self._accumulated_notches: int = 1
        self._capture_active: bool = False
        self._prev_gamepad_active: Set[str] = set()

        # pynput listeners
        self._kb_listener = None
        self._ms_listener = None

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()
        self._build_ui()
        self.start_listeners()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(10)

        # Instruction label
        instr = QLabel(
            "Press your key combination or mouse button…\n"
            "Pressing a gamepad button will also be captured.\n"
            "Click <b>Save</b> when done."
        )
        instr.setAlignment(Qt.AlignCenter)
        instr.setStyleSheet("color: rgba(255,255,255,0.65); font-size: 12px;")
        instr.setTextFormat(Qt.RichText)
        root.addWidget(instr)

        # Preview label
        self.preview_label = QLabel("Waiting for input…")
        self.preview_label.setAlignment(Qt.AlignCenter)
        self.preview_label.setStyleSheet(
            "color: #a855f7; font-size: 15px; font-weight: bold; "
            "background: rgba(168,85,247,0.08); border-radius: 6px; padding: 8px;"
        )
        root.addWidget(self.preview_label)

        # Quick mouse buttons
        mouse_grp = QGroupBox("QUICK MOUSE BUTTONS")
        mouse_grp.setStyleSheet(_CARD_STYLE)
        mouse_row = QHBoxLayout(mouse_grp)
        for label, action in [
            ("Left Click", "mouse:left"),
            ("Right Click", "mouse:right"),
            ("Middle Click", "mouse:middle"),
            ("Mouse 4", "mouse4"),
            ("Mouse 5", "mouse5"),
        ]:
            b = QPushButton(label)
            b.setFocusPolicy(Qt.NoFocus)
            b.setStyleSheet(_BTN_ACCENT)
            b.clicked.connect(lambda checked=False, a=action: self._set_result(a))
            mouse_row.addWidget(b)
        root.addWidget(mouse_grp)

        # Scroll settings panel (hidden by default, shown on scroll detection)
        self._scroll_panel = self._build_scroll_panel()
        self._scroll_panel.setVisible(False)
        root.addWidget(self._scroll_panel)

        # Clear + action buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)

        clear_btn = QPushButton("Clear")
        clear_btn.setFocusPolicy(Qt.NoFocus)
        clear_btn.setStyleSheet(_BTN_CLEAR)
        clear_btn.clicked.connect(self._clear)

        save_std = QPushButton("Save Standard")
        save_std.setFocusPolicy(Qt.NoFocus)
        save_std.setStyleSheet(_BTN_SAVE)
        save_std.clicked.connect(lambda: self._save_and_close("standard"))

        save_shift = QPushButton("Save Shift Map")
        save_shift.setFocusPolicy(Qt.NoFocus)
        save_shift.setStyleSheet(_BTN_SHIFT)
        save_shift.clicked.connect(lambda: self._save_and_close("shift"))

        cancel_btn = QPushButton("Cancel")
        cancel_btn.setFocusPolicy(Qt.NoFocus)
        cancel_btn.setStyleSheet(_BTN_CANCEL)
        cancel_btn.clicked.connect(self._cancel)

        btn_row.addWidget(clear_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_std)
        btn_row.addWidget(save_shift)
        btn_row.addWidget(cancel_btn)
        root.addLayout(btn_row)

        self.finished.connect(self._on_finished)

    def _build_scroll_panel(self) -> QGroupBox:
        grp = QGroupBox("SCROLL SETTINGS")
        grp.setStyleSheet(_CARD_STYLE)
        layout = QVBoxLayout(grp)

        # Mode row
        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Mode:"))
        self._scroll_oneshot = QRadioButton("oneshot")
        self._scroll_continuous = QRadioButton("continuous")
        self._scroll_continuous.setChecked(True)
        self._scroll_mode_group = QButtonGroup(self)
        self._scroll_mode_group.addButton(self._scroll_oneshot, 0)
        self._scroll_mode_group.addButton(self._scroll_continuous, 1)
        self._scroll_oneshot.toggled.connect(self._on_scroll_mode_changed)
        self._scroll_oneshot.setFocusPolicy(Qt.NoFocus)
        self._scroll_continuous.setFocusPolicy(Qt.NoFocus)
        for rb in (self._scroll_oneshot, self._scroll_continuous):
            rb.setStyleSheet("color: #ffffff;")
            mode_row.addWidget(rb)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Interval row
        interval_row = QHBoxLayout()
        interval_row.addWidget(QLabel("Interval (sec):"))
        self._scroll_interval = QDoubleSpinBox()
        self._scroll_interval.setFocusPolicy(Qt.NoFocus)
        self._scroll_interval.setRange(0.01, 5.0)
        self._scroll_interval.setSingleStep(0.01)
        self._scroll_interval.setValue(0.05)
        self._scroll_interval.setStyleSheet(_INPUT_STYLE)
        self._scroll_interval.setFixedWidth(80)
        interval_row.addWidget(self._scroll_interval)
        interval_row.addStretch()
        layout.addLayout(interval_row)

        # Notches row
        notch_row = QHBoxLayout()
        self._notches_label = QLabel("Notches: 1")
        self._notches_label.setStyleSheet("color: #a855f7; font-weight: bold;")
        notch_row.addWidget(self._notches_label)

        scroll_hint = QLabel("← Scroll here to set notches")
        scroll_hint.setStyleSheet("color: rgba(255,255,255,0.45); font-size: 11px;")
        notch_row.addWidget(scroll_hint)
        notch_row.addStretch()

        reset_btn = QPushButton("Reset")
        reset_btn.setFocusPolicy(Qt.NoFocus)
        reset_btn.setStyleSheet(_BTN_ACCENT)
        reset_btn.setFixedWidth(60)
        reset_btn.clicked.connect(self._reset_notches)
        notch_row.addWidget(reset_btn)
        layout.addLayout(notch_row)

        return grp

    # ------------------------------------------------------------------
    # Key normalization & accumulation
    # ------------------------------------------------------------------
    @staticmethod
    def _pynput_key_to_str(key) -> str:
        """Converts a pynput Key or KeyCode to a normalized string name."""
        if key is None:
            return ""

        # Pynput Key enum
        if hasattr(key, 'name') and key.name:
            name = key.name.lower()
            if name.startswith('ctrl'): return 'ctrl'
            if name.startswith('alt'): return 'alt'
            if name.startswith('shift'): return 'shift'
            if name in ('cmd', 'win', 'super'): return 'win'
            if name.startswith('media_') or name.startswith('volume_'):
                return name
            return name

        # VK codes (Windows hardware events, Media keys, OEM symbols)
        if hasattr(key, 'vk') and key.vk:
            vk = key.vk
            # Windows Media Key VK Codes
            vk_media_map = {
                173: 'media_volume_mute',
                174: 'media_volume_down',
                175: 'media_volume_up',
                176: 'media_next',
                177: 'media_previous',
                178: 'media_stop',
                179: 'media_play_pause',
            }
            if vk in vk_media_map:
                return vk_media_map[vk]

            # Standard alphanumeric VKs
            if 65 <= vk <= 90:
                return chr(vk).lower()
            if 48 <= vk <= 57:
                return chr(vk)
            if 96 <= vk <= 105:
                return chr(vk - 48)

            # OEM Symbol VK Codes
            vk_oem_map = {
                186: ';', 187: '=', 188: ',', 189: '-', 190: '.', 191: '/',
                192: '`', 219: '[', 220: '\\', 221: ']', 222: "'",
            }
            if vk in vk_oem_map:
                return vk_oem_map[vk]

        # Char check
        if hasattr(key, 'char') and key.char:
            c = key.char
            if len(c) == 1:
                # ASCII control characters (\x01 to \x1a for Ctrl+A .. Ctrl+Z)
                if 1 <= ord(c) <= 26:
                    return chr(ord(c) + 96)

                # Shifted symbol map: map back to unshifted character if shifted
                shift_symbol_map = {
                    '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
                    '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
                    '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\',
                    ':': ';', '"': "'", '<': ',', '>': '.', '?': '/'
                }
                if c in shift_symbol_map:
                    return shift_symbol_map[c]
                return c.lower()

        return ""

    def _add_recorded_key(self, key_name: str) -> None:
        """Appends a normalized key name to accumulated keys and updates preview."""
        if not key_name:
            return
        key_name = key_name.lower().strip()

        # If key is a media key, it's a standalone action -> set result directly
        if key_name.startswith('media_') or key_name.startswith('volume_'):
            self._set_result(f"keyboard:{key_name}")
            return

        if key_name and key_name not in self._recorded_keys:
            self._recorded_keys.append(key_name)
            combo = "keyboard:" + "+".join(self._recorded_keys)
            self._result = combo
            self._hide_scroll_settings()
            self.preview_label.setText(combo)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Qt keyPressEvent fallback to capture keys directly in PySide6 dialog."""
        if not self._capture_active:
            super().keyPressEvent(event)
            return

        key = event.key()
        qt_key_map = {
            Qt.Key_Control: 'ctrl',
            Qt.Key_Alt: 'alt',
            Qt.Key_Shift: 'shift',
            Qt.Key_Meta: 'win',
            Qt.Key_Space: 'space',
            Qt.Key_Return: 'enter',
            Qt.Key_Enter: 'enter',
            Qt.Key_Backspace: 'backspace',
            Qt.Key_Tab: 'tab',
            Qt.Key_Backtab: 'tab',
            Qt.Key_Escape: 'esc',
            Qt.Key_Delete: 'delete',
            Qt.Key_Up: 'up',
            Qt.Key_Down: 'down',
            Qt.Key_Left: 'left',
            Qt.Key_Right: 'right',
            # Media keys
            Qt.Key_VolumeUp: 'media_volume_up',
            Qt.Key_VolumeDown: 'media_volume_down',
            Qt.Key_VolumeMute: 'media_volume_mute',
            Qt.Key_MediaPlay: 'media_play_pause',
            Qt.Key_MediaPause: 'media_play_pause',
            Qt.Key_MediaTogglePlayPause: 'media_play_pause',
            Qt.Key_MediaStop: 'media_stop',
            Qt.Key_MediaNext: 'media_next',
            Qt.Key_MediaPrevious: 'media_previous',
        }

        # If Shift modifier is active in Qt event, record 'shift' modifier first
        if (event.modifiers() & Qt.ShiftModifier) and 'shift' not in self._recorded_keys:
            self._add_recorded_key('shift')

        key_name = ""
        if key in qt_key_map:
            key_name = qt_key_map[key]
        elif 65 <= key <= 90:
            key_name = chr(key).lower()
        elif 48 <= key <= 57:
            key_name = chr(key)
        elif event.text():
            shift_symbol_map = {
                '!': '1', '@': '2', '#': '3', '$': '4', '%': '5',
                '^': '6', '&': '7', '*': '8', '(': '9', ')': '0',
                '_': '-', '+': '=', '{': '[', '}': ']', '|': '\\',
                ':': ';', '"': "'", '<': ',', '>': '.', '?': '/'
            }
            raw_text = event.text().lower()
            key_name = shift_symbol_map.get(raw_text, raw_text)

        if key_name:
            self._add_recorded_key(key_name)
            event.accept()
        else:
            super().keyPressEvent(event)

    # ------------------------------------------------------------------
    # pynput listeners
    # ------------------------------------------------------------------
    def start_listeners(self) -> None:
        """Start keyboard and mouse pynput listeners."""
        if not _PYNPUT_AVAILABLE:
            logger.warning("[RECORDER] pynput not available — listeners skipped")
            return
        self._capture_active = True
        self._recorded_keys = []
        logger.debug(f"[RECORDER] start_listeners() for button={self.button_name!r}")

        def _on_press(key):
            """Accumulates key names — does NOT stop listener (beta behaviour)."""
            if not self._capture_active:
                return
            key_name = self._pynput_key_to_str(key)
            logger.debug(f"[RECORDER] pynput key_press raw={key!r} resolved={key_name!r} recorded_so_far={self._recorded_keys}")
            if key_name:
                QTimer.singleShot(0, lambda k=key_name: self._add_recorded_key(k))

        def _on_click(x, y, button, pressed):
            """On button press: capture, stop both listeners (beta behaviour)."""
            logger.debug(f"[RECORDER] pynput mouse_click button={button.name!r} pressed={pressed} xy=({x},{y})")
            if not pressed or not self._capture_active:
                return
            if button.name == 'x1':
                b_name = 'mouse4'
            elif button.name == 'x2':
                b_name = 'mouse5'
            else:
                b_name = f"mouse:{button.name}"

            if button.name == 'left':
                logger.debug("[RECORDER]   left click ignored (used for dialog interaction)")
                return  # ignore left click (used to interact with dialog)

            logger.debug(f"[RECORDER]   mouse capture: {b_name!r} — stopping listeners")
            self._stop_listeners()
            QTimer.singleShot(0, lambda n=b_name: self._set_result(n))

        def _on_scroll(x, y, dx, dy):
            """On scroll: stop listeners, show scroll settings panel (beta behaviour)."""
            logger.debug(f"[RECORDER] pynput scroll dx={dx} dy={dy} is_showing_scroll={self._is_showing_scroll}")
            if not self._capture_active or self._is_showing_scroll:
                return
            if dy > 0:
                direction = 'scroll_up'
            elif dy < 0:
                direction = 'scroll_down'
            elif dx > 0:
                direction = 'scroll_right'
            elif dx < 0:
                direction = 'scroll_left'
            else:
                return

            logger.debug(f"[RECORDER]   scroll capture: {direction!r} — stopping listeners")
            self._stop_listeners()
            QTimer.singleShot(0, lambda d=direction: self._show_scroll_settings(d))

        try:
            self._kb_listener = pynput_keyboard.Listener(on_press=_on_press)
            self._ms_listener = pynput_mouse.Listener(on_click=_on_click, on_scroll=_on_scroll)
            self._kb_listener.start()
            self._ms_listener.start()
            logger.debug("[RECORDER] listeners started (kb + mouse)")
        except Exception as e:
            logger.error(f"[RECORDER] Failed to start listeners: {e}", exc_info=True)

    def _stop_listeners(self) -> None:
        """Unconditionally stop and discard both pynput listeners."""
        logger.debug(f"[RECORDER] _stop_listeners() capture_active was {self._capture_active}")
        self._capture_active = False
        for listener in (self._kb_listener, self._ms_listener):
            try:
                if listener is not None:
                    listener.stop()
            except Exception:
                pass
        self._kb_listener = None
        self._ms_listener = None
        logger.debug("[RECORDER] listeners stopped")

    # ------------------------------------------------------------------
    # Gamepad telemetry slot
    # ------------------------------------------------------------------
    @Slot(dict)
    def update_telemetry(self, telemetry: dict) -> None:
        """
        Receives live UDP telemetry (ControllerState dict). Captures newly pressed gamepad buttons
        (rising edge) that are NOT the button being configured (to avoid self-mapping).
        Only active while the listeners are running (capture_active).
        """
        if not self._capture_active or not isinstance(telemetry, dict):
            return

        current_active: Set[str] = set()

        std_buttons = [
            'a', 'b', 'x', 'y', 'lb', 'rb', 'select', 'start',
            'home', 'l3', 'r3', 'dpad_up', 'dpad_down', 'dpad_left', 'dpad_right'
        ]

        # Check standard digital buttons
        for btn_name in std_buttons:
            if bool(telemetry.get(btn_name, False)) and btn_name.lower() != self.button_name.lower():
                current_active.add(btn_name.lower())

        # Check analog triggers
        for trg_name in ('lt', 'rt'):
            val = telemetry.get(trg_name, 0.0)
            if isinstance(val, (int, float)) and val > 0.5 and trg_name.lower() != self.button_name.lower():
                current_active.add(trg_name.lower())

        # Check dynamic extra inputs
        extra = telemetry.get("extra_inputs", {})
        if isinstance(extra, dict):
            for eb_name, eb_val in extra.items():
                is_pressed = bool(eb_val > 0.1 if isinstance(eb_val, (int, float)) else eb_val)
                if is_pressed and str(eb_name).lower() != self.button_name.lower():
                    current_active.add(str(eb_name).lower())

        # Check rising edge
        newly_pressed = current_active - self._prev_gamepad_active
        self._prev_gamepad_active = current_active

        if newly_pressed:
            btn = next(iter(newly_pressed))
            action_str = f"gamepad:{btn}"
            logger.debug(f"[RECORDER] gamepad button captured (rising edge): {action_str!r}")
            self._set_result(action_str)

    # ------------------------------------------------------------------
    # Scroll settings helpers
    # ------------------------------------------------------------------
    def _show_scroll_settings(self, direction: str) -> None:
        self._detected_scroll_dir = direction
        self._is_showing_scroll = True
        self._scroll_panel.setVisible(True)
        self.adjustSize()

    def _hide_scroll_settings(self) -> None:
        self._detected_scroll_dir = None
        self._is_showing_scroll = False
        self._scroll_panel.setVisible(False)
        self.adjustSize()

    def _on_scroll_mode_changed(self) -> None:
        is_oneshot = self._scroll_oneshot.isChecked()
        self._scroll_interval.setEnabled(not is_oneshot)

    def _reset_notches(self) -> None:
        self._accumulated_notches = 1
        self._notches_label.setText("Notches: 1")

    def wheelEvent(self, event) -> None:
        """Route main-window scroll to notch accumulator when panel is visible."""
        if self._is_showing_scroll:
            delta = event.angleDelta().y()
            ticks = max(1, abs(delta) // 120)
            if delta > 0:
                self._accumulated_notches += ticks
            else:
                self._accumulated_notches = max(1, self._accumulated_notches - ticks)
            self._notches_label.setText(f"Notches: {self._accumulated_notches}")
        else:
            super().wheelEvent(event)

    # ------------------------------------------------------------------
    # Result helpers
    # ------------------------------------------------------------------
    def _set_result(self, value: str) -> None:
        """Update the result string and preview label."""
        logger.debug(f"[RECORDER] _set_result({value!r})")
        if not value.startswith("keyboard:"):
            self._recorded_keys.clear()
        self._result = value
        self._hide_scroll_settings()
        self.preview_label.setText(value)

    def _clear(self) -> None:
        self._result = ""
        self._recorded_keys.clear()
        self._hide_scroll_settings()
        self._reset_notches()
        self.preview_label.setText("Waiting for input…")

    # ------------------------------------------------------------------
    # Save / Cancel
    # ------------------------------------------------------------------
    def _build_scroll_result(self) -> str:
        """Construct the mouse:scroll_* mapping string from scroll settings."""
        direction = self._detected_scroll_dir or 'scroll_down'
        notches = self._accumulated_notches
        if self._scroll_oneshot.isChecked():
            return f"mouse:{direction}:oneshot:{notches}"
        else:
            interval = self._scroll_interval.value()
            return f"mouse:{direction}:continuous:{notches}:{interval:.2f}"

    def _save_and_close(self, target: str) -> None:
        """Stop listeners, build final value, emit signal, close."""
        logger.debug(f"[RECORDER] _save_and_close(target={target!r}) result={self._result!r} is_showing_scroll={self._is_showing_scroll}")
        self._stop_listeners()

        if self._is_showing_scroll:
            val = self._build_scroll_result()
            logger.debug(f"[RECORDER]   scroll result built: {val!r}")
        else:
            val = self._result

        logger.debug(f"[RECORDER]   final val to emit: {val!r}")
        if val:
            self.input_recorded.emit(target, val)
        self.accept()

    def _cancel(self) -> None:
        logger.debug("[RECORDER] _cancel() called")
        self._stop_listeners()
        self.reject()

    @Slot()
    def _on_finished(self) -> None:
        """Safety net — always stop listeners when dialog closes for any reason."""
        self._stop_listeners()
