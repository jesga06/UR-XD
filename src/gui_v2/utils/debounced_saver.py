"""
Debounced Config Saver utility module for gui_v2.
Prevents main-thread disk I/O lag and ANR triggers by batching rapid UI setting changes.
"""

from PySide6.QtCore import QObject, QTimer


class DebouncedConfigSaver(QObject):
    """
    Single-shot timer utility that debounces high-frequency UI events (sliders, inputs)
    to batch configuration disk writes and avoid blocking the event loop.
    """
    def __init__(self, save_callback, delay_ms: int = 300, parent=None):
        super().__init__(parent)
        self._save_callback = save_callback
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.setInterval(delay_ms)
        self._timer.timeout.connect(self._do_save)

    def mark_dirty(self):
        """Restarts the single-shot debounce timer."""
        self._timer.start()

    def flush(self):
        """Immediately executes pending save if timer is active."""
        if self._timer.isActive():
            self._timer.stop()
            self._do_save()

    def _do_save(self):
        try:
            self._save_callback()
        except Exception as e:
            print(f"[DebouncedConfigSaver] Error executing save callback: {e}")
