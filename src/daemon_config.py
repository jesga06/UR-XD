"""
Daemon Config module alias for backward compatibility (daemon_config.py)
Re-exports ControllerConfig as DaemonConfig from config_manager.
"""

from config_manager import ControllerConfig as DaemonConfig, ControllerConfig

__all__ = ['DaemonConfig', 'ControllerConfig']
