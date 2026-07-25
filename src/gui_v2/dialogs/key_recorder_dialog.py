"""
Key Recorder Dialog for PySide6 UI (gui_v2).

Captures keyboard combinations, mouse button presses, and scroll-wheel notch
configurations for button remapping. All pynput events are dispatched to the
Qt main thread via Qt Signals. Listener teardown is guaranteed via try/finally
blocks so OS input locks are never left dangling.
"""

import sys
import os
import threading
from typing import Optional, Set

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QComboBox, QSpinBox, QDoubleSpinBox, QRadioButton,
    QButtonGroup, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QFont

# pynput is imported lazily so the module can load even if it is not installed
try:
    from pynput import keyboard as pynput_keyboard
    from pynput import mouse as pynput_mouse
    _PYNPUT_AVAILABLE = True
except ImportError:
    _PYNPUT_AVAILABLE = False


# ---------------------------------------------------------------------------
# Styling helpers
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

_BTN_DANGER = """
QPushButton {
    background-color: rgba(220, 38, 38, 0.2);
    border: 1px solid rgba(220, 38, 38, 0.5);
    border-radius: 6px;
    color: #ffffff;
    padding: 5px 12px;
    font-size: 11px;
}
QPushButton:hover { background-color: rgba(220, 38, 38, 0.4); }
"""

_BTN_SUCCESS = """
QPushButton {
    background-color: rgba(22, 163, 74, 0.2);
    border: 1px solid rgba(22, 163, 74, 0.5);
    border-radius: 6px;
    color: #ffffff;
    padding: 5px 12px;
    font-size: 11px;
}
QPushButton:hover { background-color: rgba(22, 163, 74, 0.4); }
"""


class KeyRecorderDialog(QDialog):
    """
    Modal dialog for recording keyboard combinations, mouse buttons, and
    scroll-wheel notch actions for a single remapping slot.

    Signals
    -------
    input_recorded(target, mapping_str)
        Emitted when the user confirms an action.
        ``target`` is ``'standard'`` or ``'shift'``;
        ``mapping_str`` is the formatted action string.
    """

    input_recorded = Signal(str, str)

    def __init__(self, button_name: str, parent=None):
        super().__init__(parent)
        self.button_name: str = button_name
        self.recorded_string: str = ""

        # pynput listener state
        self._kb_listener: Optional[object] = None
        self._kb_lock = threading.Lock()
        self._held_keys: Set[str] = set()
        self._capture_active: bool = False

        self.setWindowTitle(f"Record Input — {button_name.upper()}")
        self.setModal(True)
        self.setMinimumWidth(420)
        self.setStyleSheet("background-color: #0c0914; color: #ffffff;")

        self.setup_ui()
        self.start_pynput_listeners()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def setup_ui(self) -> None:
        """Builds the dialog layout."""
        root = QVBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        # Title
        title = QLabel(f"⚡ Recording input for  <b style='color:#a855f7'>{self.button_name.upper()}</b>")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 14px; color: #ffffff; padding: 4px;")
        root.addWidget(title)

        # Preview box
        preview_frame = QFrame()
        preview_frame.setStyleSheet("""
            QFrame {
                background: rgba(168, 85, 247, 0.08);
                border: 1.5px solid rgba(168, 85, 247, 0.5);
                border-radius: 8px;
            }
        """)
        preview_layout = QVBoxLayout(preview_frame)
        preview_layout.setContentsMargins(10, 8, 10, 8)

        self.preview_label = QLabel("Press a key combination…")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font_mono = QFont("JetBrains Mono, Consolas, monospace")
        font_mono.setPointSize(14)
        self.preview_label.setFont(font_mono)
        self.preview_label.setStyleSheet("color: #a855f7; font-weight: bold;")
        self.preview_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_label)
        root.addWidget(preview_frame)

        # ---- Mouse Buttons -------------------------------------------
        mouse_group = QGroupBox("🖱️  Quick Mouse Buttons")
        mouse_group.setStyleSheet(_CARD_STYLE)
        mouse_layout = QHBoxLayout(mouse_group)
        mouse_layout.setSpacing(6)
        for label, action in [
            ("+ Left Click", "mouse:left"),
            ("+ Right Click", "mouse:right"),
            ("+ Middle", "mouse:middle"),
            ("+ Mouse4", "mouse4"),
            ("+ Mouse5", "mouse5"),
        ]:
            btn = QPushButton(label)
            btn.setStyleSheet(_BTN_ACCENT)
            btn.clicked.connect(lambda checked, a=action: self._set_preview(a))
            mouse_layout.addWidget(btn)
        root.addWidget(mouse_group)

        # ---- Scroll Wheel Notch Config --------------------------------
        scroll_group = QGroupBox("📜  Scroll Wheel Notch Settings")
        scroll_group.setStyleSheet(_CARD_STYLE)
        scroll_layout = QVBoxLayout(scroll_group)
        scroll_layout.setSpacing(6)

        row1 = QHBoxLayout()
        row1.addWidget(QLabel("Direction:"))
        self.scroll_dir = QComboBox()
        self.scroll_dir.addItems(["scroll_up", "scroll_down"])
        self.scroll_dir.setStyleSheet(_INPUT_STYLE)
        row1.addWidget(self.scroll_dir)
        row1.addSpacing(12)
        row1.addWidget(QLabel("Notches:"))
        self.scroll_notches = QSpinBox()
        self.scroll_notches.setMinimum(1)
        self.scroll_notches.setValue(1)
        self.scroll_notches.setStyleSheet(_INPUT_STYLE)
        row1.addWidget(self.scroll_notches)
        row1.addStretch()
        scroll_layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("Mode:"))
        self._scroll_mode_group = QButtonGroup(self)
        rb_oneshot = QRadioButton("Oneshot")
        rb_oneshot.setChecked(True)
        rb_cont = QRadioButton("Continuous")
        for rb in (rb_oneshot, rb_cont):
            rb.setStyleSheet("color: #ffffff; font-size: 11px;")
        self._scroll_mode_group.addButton(rb_oneshot, 0)
        self._scroll_mode_group.addButton(rb_cont, 1)
        row2.addWidget(rb_oneshot)
        row2.addWidget(rb_cont)
        row2.addSpacing(12)
        row2.addWidget(QLabel("Delay (s):"))
        self.scroll_delay = QDoubleSpinBox()
        self.scroll_delay.setMinimum(0.0)
        self.scroll_delay.setMaximum(10.0)
        self.scroll_delay.setSingleStep(0.01)
        self.scroll_delay.setValue(0.05)
        self.scroll_delay.setDecimals(2)
        self.scroll_delay.setStyleSheet(_INPUT_STYLE)
        row2.addWidget(self.scroll_delay)
        row2.addStretch()
        scroll_layout.addLayout(row2)

        apply_scroll = QPushButton("Apply Scroll Notch Binding")
        apply_scroll.setStyleSheet(_BTN_ACCENT)
        apply_scroll.clicked.connect(self._apply_scroll_binding)
        scroll_layout.addWidget(apply_scroll)
        root.addWidget(scroll_group)

        # ---- Divider -------------------------------------------------
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: rgba(168, 85, 247, 0.3);")
        root.addWidget(line)

        # ---- Bottom Actions ------------------------------------------
        actions_layout = QHBoxLayout()
        btn_clear = QPushButton("🗑  Clear")
        btn_clear.setStyleSheet(_BTN_DANGER)
        btn_clear.clicked.connect(self._clear)

        btn_std = QPushButton("💾  Save Standard")
        btn_std.setStyleSheet(_BTN_SUCCESS)
        btn_std.clicked.connect(self._save_standard)

        btn_shift = QPushButton("💾  Save Shift Map")
        btn_shift.setStyleSheet(_BTN_ACCENT)
        btn_shift.clicked.connect(self._save_shift)

        btn_cancel = QPushButton("✕  Cancel")
        btn_cancel.setStyleSheet(_BTN_DANGER)
        btn_cancel.clicked.connect(self.reject)

        actions_layout.addWidget(btn_clear)
        actions_layout.addStretch()
        actions_layout.addWidget(btn_cancel)
        actions_layout.addWidget(btn_std)
        actions_layout.addWidget(btn_shift)
        root.addLayout(actions_layout)

    # ------------------------------------------------------------------
    # pynput listener management
    # ------------------------------------------------------------------
    def start_pynput_listeners(self) -> None:
        """Spawns a pynput keyboard listener in a background thread."""
        if not _PYNPUT_AVAILABLE:
            return

        self._capture_active = True

        def _on_press(key):
            if not self._capture_active:
                return
            key_str = self._pynput_key_to_str(key)
            if key_str:
                with self._kb_lock:
                    self._held_keys.add(key_str)
                    combo = "+".join(sorted(self._held_keys))
                QTimer.singleShot(0, lambda c=combo: self._set_preview_keyboard(c))

        def _on_release(key):
            if not self._capture_active:
                return
            key_str = self._pynput_key_to_str(key)
            if key_str:
                with self._kb_lock:
                    self._held_keys.discard(key_str)

        try:
            self._kb_listener = pynput_keyboard.Listener(
                on_press=_on_press,
                on_release=_on_release
            )
            self._kb_listener.start()
        except Exception as e:
            print(f"[KeyRecorderDialog] Failed to start pynput listener: {e}")

    def stop_pynput_listeners(self) -> None:
        """Stops all pynput listeners unconditionally."""
        self._capture_active = False
        try:
            if self._kb_listener is not None:
                self._kb_listener.stop()
        except Exception:
            pass
        finally:
            self._kb_listener = None

    @staticmethod
    def _pynput_key_to_str(key) -> str:
        """Converts a pynput Key or KeyCode to a displayable string."""
        try:
            if hasattr(key, 'char') and key.char:
                return key.char.lower()
            if hasattr(key, 'name'):
                return key.name
        except Exception:
            pass
        return ""

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @Slot(str)
    def _set_preview_keyboard(self, combo: str) -> None:
        """Updates preview with keyboard combo (called on Qt main thread)."""
        if combo:
            self.recorded_string = f"keyboard:{combo}"
            self.preview_label.setText(self.recorded_string)

    def _set_preview(self, action: str) -> None:
        """Sets preview directly (for mouse quick-buttons)."""
        self.recorded_string = action
        self.preview_label.setText(action)

    def _apply_scroll_binding(self) -> None:
        """Builds and previews the scroll notch action string."""
        direction = self.scroll_dir.currentText()
        notches = self.scroll_notches.value()
        mode_id = self._scroll_mode_group.checkedId()
        mode = "continuous" if mode_id == 1 else "oneshot"
        delay = self.scroll_delay.value()
        action = f"mouse:{direction}:{mode}:{notches}:{delay:.2f}"
        self._set_preview(action)

    def _clear(self) -> None:
        """Clears the current recorded string."""
        self.recorded_string = ""
        self._held_keys.clear()
        self.preview_label.setText("Press a key combination…")

    def _save_standard(self) -> None:
        """Emits the recorded mapping for the standard (base layer) slot."""
        if self.recorded_string:
            self.input_recorded.emit("standard", self.recorded_string)
        self.accept()

    def _save_shift(self) -> None:
        """Emits the recorded mapping for the active shift layer slot."""
        if self.recorded_string:
            self.input_recorded.emit("shift", self.recorded_string)
        self.accept()

    # ------------------------------------------------------------------
    # Qt event overrides
    # ------------------------------------------------------------------
    def closeEvent(self, event) -> None:
        """Guarantees pynput listeners are stopped on any close path."""
        self.stop_pynput_listeners()
        super().closeEvent(event)

    def reject(self) -> None:
        self.stop_pynput_listeners()
        super().reject()
