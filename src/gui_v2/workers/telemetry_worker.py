"""
Decoupled UDP Telemetry Worker for gui_v2.
Processes 1000Hz backend IPC telemetry datagrams on a background QThread
and provides thread-safe atomic state snapshots and throttled signal updates.
"""

import socket
import json
import time
from typing import Dict, Any

from PySide6.QtCore import QThread, Signal, QMutex


class UDPTelemetryWorker(QThread):
    """
    Worker thread that listens for high-frequency UDP telemetry datagrams
    and provides atomic thread-safe state access while throttling UI signals.
    """
    # Emits snapshot dictionary at display refresh rate or atomic request
    telemetry_updated = Signal(dict)
    telemetry_stale = Signal(bool)

    def __init__(self, port: int = 9999, target_fps: float = 144.0, parent=None):
        super().__init__(parent)
        self.port = port
        self._atomic_state: Dict[str, Any] = {}
        self._lock = QMutex()
        self.frame_interval_ms = int(1000 / target_fps)
        self.sock: socket.socket | None = None
        self._is_stale: bool = True

    def get_latest_snapshot(self) -> dict:
        """Atomic thread-safe retrieval of latest ControllerState."""
        self._lock.lock()
        snapshot = dict(self._atomic_state)
        self._lock.unlock()
        return snapshot

    def run(self) -> None:
        """
        Main execution loop for high-frequency UDP packet ingestion.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(0.01)

        try:
            self.sock.bind(('0.0.0.0', self.port))
        except Exception as e:
            print(f"[UDPTelemetryWorker] Failed to bind to port {self.port}: {e}")
            return

        last_udp_time = 0.0
        last_emit_time = 0.0
        frame_interval_sec = self.frame_interval_ms / 1000.0

        while not self.isInterruptionRequested():
            try:
                data, _ = self.sock.recvfrom(2048)
                current_time = time.perf_counter()
                last_udp_time = current_time

                if self._is_stale:
                    self._is_stale = False
                    self.telemetry_stale.emit(False)

                try:
                    payload = data.decode('utf-8')
                    state_dict = json.loads(payload)

                    # Update atomic state inside mutex lock
                    self._lock.lock()
                    self._atomic_state = state_dict
                    self._lock.unlock()

                    # Throttle signal emissions to target FPS rate
                    if (current_time - last_emit_time) >= frame_interval_sec:
                        snapshot = self.get_latest_snapshot()
                        self.telemetry_updated.emit(snapshot)
                        last_emit_time = current_time

                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass

            except socket.timeout:
                current_time = time.perf_counter()
                if not self._is_stale and (current_time - last_udp_time) > 1.0:
                    self._is_stale = True
                    self.telemetry_stale.emit(True)
            except Exception as e:
                print(f"[UDPTelemetryWorker] Error in packet processing: {e}")

        if self.sock:
            self.sock.close()

    def stop(self) -> None:
        """
        Gracefully stop the worker thread.
        """
        self.requestInterruption()
        self.wait()
