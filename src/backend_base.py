"""
Base Input Backend Interface (backend_base.py)
Defines the standard abstraction for all input backends (DInput, XInput, etc.)
so the rest of the pipeline can operate on normalized ControllerState.
"""
from enum import Enum, auto
from typing import Callable, Optional
from decoder import ControllerState


class ConnectionState(Enum):
    """
    Explicit 6-state controller connection state machine.
    """
    DISCONNECTED = auto()
    WAITING = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    DISCONNECTING = auto()
    INIT_FAILED = auto()


class BaseInputBackend:
    """
    Abstract interface for acquiring physical controller state and capabilities.
    """
    def __init__(self):
        self.callback: Optional[Callable[[ControllerState], None]] = None
        self._state: ConnectionState = ConnectionState.DISCONNECTED

    @property
    def state(self) -> ConnectionState:
        """Return current connection state."""
        return self._state

    def set_state(self, state: ConnectionState) -> None:
        """Update connection state."""
        self._state = state

    def set_callback(self, callback: Callable[[ControllerState], None]):
        """
        Set the callback function to receive normalized ControllerState updates.
        """
        self.callback = callback
    
    def initialize(self) -> bool:
        """
        Initialize the backend and scan for devices. Returns True if a device is ready.
        """
        raise NotImplementedError
        
    def shutdown(self):
        """
        Release resources and disconnect.
        """
        raise NotImplementedError
        
    def poll(self):
        """
        Synchronous or asynchronous polling loop. Depending on the backend, 
        this might block in a thread or be called periodically.
        """
        raise NotImplementedError
        
    def get_capabilities(self) -> dict:
        """
        Return flags indicating supported features (e.g., {'vibration': True, 'analog_triggers': True})
        """
        raise NotImplementedError
        
    def set_vibration(self, left_motor: float, right_motor: float):
        """
        Set rumble intensities (0.0 to 1.0).
        """
        raise NotImplementedError
        
    def get_connection_state(self) -> bool:
        """
        Check if the device is currently connected and active.
        """
        return self._state == ConnectionState.CONNECTED

