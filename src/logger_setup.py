import logging
import sys


def setup_logger(name: str, log_file: str, is_debug: bool, append: bool = False) -> logging.Logger:
    """
    Configures and returns a logging.Logger instance with file handler.
    Also adds a root-level handler as a catch-all so every child logger
    (mapper, decoder, etc.) that uses getLogger('name') propagates here.
    """
    level = logging.DEBUG if is_debug else logging.INFO
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Wire root logger so all child loggers that propagate land in this file
    root = logging.getLogger()
    root.setLevel(level)
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', '').endswith(log_file)
               for h in root.handlers):
        root_fh = logging.FileHandler(log_file, mode='w', encoding='utf-8')
        root_fh.setFormatter(formatter)
        root.addHandler(root_fh)

    # Named logger for 'main' (or whatever the caller uses)
    logger = logging.getLogger(name)
    logger.setLevel(level)
    # Named logger can propagate to root — no separate handler needed
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

    # Wire root so every logger in the GUI process lands in the file
    root = logging.getLogger()
    root.setLevel(level)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', '').endswith(log_file)
               for h in root.handlers):
        root_fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        root_fh.setFormatter(formatter)
        root.addHandler(root_fh)
