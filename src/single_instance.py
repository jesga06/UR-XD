"""
Single Instance Process Guard
Prevents duplicate instances of application scripts (main.py, gui.py, calibration.py)
from running concurrently by locking a local socket port.
"""

import socket
import sys

_instance_sockets = {}

PORT_MAIN = 48124
PORT_BACKEND = 48125
PORT_GUI = 48126


def ensure_single_instance(app_name: str, port: int) -> socket.socket:
    """
    Ensures that only one instance of app_name is running simultaneously.
    If another instance is already running on the specified port, sends a RESTORE
    signal to the running instance and exits immediately with status 0.

    Args:
        app_name (str): Human readable name of the application/script.
        port (int): Port number on localhost to bind for locking.

    Returns:
        socket.socket: Bound socket object (must remain open for process lifetime).
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind(('127.0.0.1', port))
        s.listen(1)
        # Keep reference in global dict so garbage collector does not close the socket
        _instance_sockets[app_name] = s
        return s
    except (socket.error, OSError):
        try:
            sender = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sender.settimeout(0.5)
            sender.connect(('127.0.0.1', port))
            sender.sendall(b"RESTORE\n")
            sender.close()
        except Exception:
            pass
        print(f"[{app_name}] Another instance of {app_name} is already running. Sent restore signal and exiting.")
        sys.exit(0)
