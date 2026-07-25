"""
IPC Threads Module for PySide6 GUI.
Provides high-frequency UDP telemetry reading and file polling
without blocking the main GUI thread.
"""

import sys
import os
import json
import time
import socket
from typing import Dict, List, Any

from PySide6.QtCore import QThread, Signal, QCoreApplication

class UDPTelemetryWorker(QThread):
    """
    Worker thread that listens for high-frequency UDP telemetry datagrams
    on port 9999 and emits signals when data is received or becomes stale.
    """
    telemetry_received = Signal(dict)
    telemetry_stale = Signal(bool)

    def __init__(self, port: int = 9999, parent=None):
        super().__init__(parent)
        self.port = port
        self.sock: socket.socket | None = None
        self._is_stale: bool = True

    def run(self) -> None:
        """
        Main execution loop for the UDP listener.
        """
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(0.1)
        
        try:
            self.sock.bind(('0.0.0.0', self.port))
        except Exception as e:
            print(f"[UDPTelemetryWorker] Failed to bind to port {self.port}: {e}")
            return

        last_udp_time = 0.0

        while not self.isInterruptionRequested():
            try:
                data, _ = self.sock.recvfrom(2048)
                current_time = time.time()
                last_udp_time = current_time
                
                if self._is_stale:
                    self._is_stale = False
                    self.telemetry_stale.emit(False)
                    
                try:
                    payload = data.decode('utf-8')
                    state_dict = json.loads(payload)
                    self.telemetry_received.emit(state_dict)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    pass # Ignore malformed packets

            except socket.timeout:
                current_time = time.time()
                if not self._is_stale and (current_time - last_udp_time) > 1.0:
                    self._is_stale = True
                    self.telemetry_stale.emit(True)
            except Exception as e:
                # Catch unexpected errors to prevent thread crash
                print(f"[UDPTelemetryWorker] Unexpected error: {e}")

        # Cleanup
        if self.sock:
            self.sock.close()

    def stop(self) -> None:
        """
        Gracefully stop the worker thread.
        """
        self.requestInterruption()
        self.wait()


class FilePollerWorker(QThread):
    """
    Worker thread that polls status and diagnostic JSON files,
    and tails a log file, emitting signals upon updates.
    """
    status_updated = Signal(dict)
    diagnostics_updated = Signal(dict)
    log_lines_received = Signal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_file = "status.json"
        self.diagnostics_file = "diagnostics.json"
        self.log_file = "wrapper.log"
        
        self._last_status: Dict[str, Any] = {}
        self._log_offset: int = 0

    def run(self) -> None:
        """
        Main execution loop for polling files at different intervals.
        """
        last_status_time = 0.0
        last_diag_time = 0.0
        last_log_time = 0.0

        # Try to initialize log offset to the end of the file
        try:
            if os.path.exists(self.log_file):
                self._log_offset = os.path.getsize(self.log_file)
        except OSError:
            self._log_offset = 0

        while not self.isInterruptionRequested():
            current_time = time.time()

            # Poll Log File (10Hz / 100ms)
            if current_time - last_log_time >= 0.1:
                last_log_time = current_time
                self._poll_log_file()

            # Poll Diagnostics File (2Hz / 500ms)
            if current_time - last_diag_time >= 0.5:
                last_diag_time = current_time
                self._poll_diagnostics()

            # Poll Status File (1Hz / 1000ms)
            if current_time - last_status_time >= 1.0:
                last_status_time = current_time
                self._poll_status()

            time.sleep(0.05)

    def _poll_status(self) -> None:
        """
        Internal method to poll the status JSON file.
        """
        try:
            with open(self.status_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data != self._last_status:
                    self._last_status = data
                    self.status_updated.emit(data)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            pass

    def _poll_diagnostics(self) -> None:
        """
        Internal method to poll the diagnostics JSON file.
        """
        try:
            with open(self.diagnostics_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.diagnostics_updated.emit(data)
        except (FileNotFoundError, json.JSONDecodeError, PermissionError):
            pass

    def _poll_log_file(self) -> None:
        """
        Internal method to tail the wrapper log file.
        """
        try:
            if not os.path.exists(self.log_file):
                return
                
            current_size = os.path.getsize(self.log_file)
            
            # File was rotated or truncated
            if current_size < self._log_offset:
                self._log_offset = 0
                
            if current_size > self._log_offset:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    f.seek(self._log_offset)
                    new_lines = f.readlines()
                    self._log_offset = f.tell()
                    
                    if new_lines:
                        # Clean up newlines if needed, or emit raw
                        self.log_lines_received.emit(new_lines)
        except (FileNotFoundError, PermissionError, OSError):
            pass

    def stop(self) -> None:
        """
        Gracefully stop the worker thread.
        """
        self.requestInterruption()
        self.wait()


if __name__ == '__main__':
    # Self-contained test block
    app = QCoreApplication(sys.argv)
    
    print("Initializing IPC Workers...")
    
    udp_worker = UDPTelemetryWorker()
    file_worker = FilePollerWorker()
    
    def on_telemetry(data: dict):
        print(f"[UDP] Telemetry Received: {list(data.keys())[:5]}...")
        
    def on_stale(stale: bool):
        print(f"[UDP] Telemetry Stale Status: {stale}")
        
    def on_status(data: dict):
        print(f"[FILE] Status Updated: {data}")
        
    def on_diag(data: dict):
        print(f"[FILE] Diagnostics Updated: {data}")
        
    def on_log(lines: list):
        print(f"[FILE] Received {len(lines)} new log lines")

    udp_worker.telemetry_received.connect(on_telemetry)
    udp_worker.telemetry_stale.connect(on_stale)
    
    file_worker.status_updated.connect(on_status)
    file_worker.diagnostics_updated.connect(on_diag)
    file_worker.log_lines_received.connect(on_log)
    
    print("Starting workers...")
    udp_worker.start()
    file_worker.start()
    
    # Run for a few seconds then shut down
    def shutdown():
        print("Shutting down workers...")
        udp_worker.stop()
        file_worker.stop()
        app.quit()
        print("Shutdown complete.")
        
    # Use a QTimer for the shutdown sequence
    from PySide6.QtCore import QTimer
    QTimer.singleShot(5000, shutdown)
    
    print("Running event loop (5 seconds)...")
    sys.exit(app.exec())
