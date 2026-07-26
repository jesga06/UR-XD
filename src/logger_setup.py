import logging
import sys


def setup_logger(name: str, log_file: str, is_debug: bool, append: bool = False) -> logging.Logger:
    """
    Configures and returns a logging.Logger instance with file handler.
    Also sets the root logger level so all child getLogger() loggers inherit it.
    """
    level = logging.DEBUG if is_debug else logging.INFO

    # Propagate level to root so child loggers (mapper, decoder, etc.) are
    # gated at the same level without needing individual setup calls.
    logging.getLogger().setLevel(level)

    logger = logging.getLogger(name)
    logger.setLevel(level)

    if logger.handlers:
        return logger

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    file_handler = logging.FileHandler(
        log_file, mode='a' if append else 'w', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger


def setup_telemetry_logger(log_file: str = 'wrapper_telemetry.log') -> logging.Logger:
    """
    Returns a dedicated logger for high-frequency decoded-state telemetry.
    Writes to a separate file so it never pollutes the main log.
    """
    tel_logger = logging.getLogger('telemetry')
    if tel_logger.handlers:
        return tel_logger

    tel_logger.setLevel(logging.DEBUG)
    tel_logger.propagate = False  # don't echo into root/main handlers

    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
    fh.setFormatter(formatter)
    tel_logger.addHandler(fh)
    return tel_logger


def setup_gui_loggers(log_file: str, is_debug: bool) -> None:
    """
    Wires all GUI-side module loggers to the same log file as the daemon
    (append mode so both processes share one file).
    Called once at GUI startup after parsing --debug.
    """
    level = logging.DEBUG if is_debug else logging.INFO
    logging.getLogger().setLevel(level)

    gui_modules = [
        'remapping_view', 'key_recorder_dialog', 'mapper',
        'config_manager', 'app_window', 'tray_icon',
        'dashboard_view', 'haptic_engine', 'macro_executor',
    ]

    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    for mod_name in gui_modules:
        mod_logger = logging.getLogger(mod_name)
        if mod_logger.handlers:
            continue
        mod_logger.setLevel(level)
        fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        fh.setFormatter(formatter)
        mod_logger.addHandler(fh)
