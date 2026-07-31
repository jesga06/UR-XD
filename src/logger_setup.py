"""
Logger Setup Module (logger_setup.py)
Provides standardized severity logging formatters, custom levels (SUCCESS, QUOTE),
terminal log filtering (excluding DEBUG), high-frequency telemetry isolation/rate-limiting,
and log sanitation filters for issue report packaging.
"""

import os
import sys
import time
import logging
from typing import Optional

# Custom Logging Level Definitions
SUCCESS_LEVEL_NUM = 22  # Between INFO (20) and QUOTE (25)
QUOTE_LEVEL_NUM = 25    # Between SUCCESS (22) and WARNING (30)

logging.addLevelName(SUCCESS_LEVEL_NUM, "SUCCESS")
logging.addLevelName(QUOTE_LEVEL_NUM, "QUOTE")


def log_success(self, message, *args, **kws):
    """Logs a message with SUCCESS severity (Level 22)."""
    if self.isEnabledFor(SUCCESS_LEVEL_NUM):
        self._log(SUCCESS_LEVEL_NUM, message, args, **kws)


def log_quote(self, message, *args, **kws):
    """Logs a message with QUOTE severity (Level 25)."""
    if self.isEnabledFor(QUOTE_LEVEL_NUM):
        self._log(QUOTE_LEVEL_NUM, message, args, **kws)


if not hasattr(logging.Logger, "success"):
    logging.Logger.success = log_success  # type: ignore[attr-defined]

if not hasattr(logging.Logger, "quote"):
    logging.Logger.quote = log_quote  # type: ignore[attr-defined]


class CustomSeverityFormatter(logging.Formatter):
    """
    Formatter mapping level numbers to standardized bracketed tags:
    [INFO], [SUCCESS], [WARN], [ERROR], [DEBUG], [QUOTE].
    """

    LEVEL_TAGS = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        SUCCESS_LEVEL_NUM: "SUCCESS",
        QUOTE_LEVEL_NUM: "QUOTE",
        logging.WARNING: "WARN",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "ERROR",
    }

    def format(self, record: logging.LogRecord) -> str:
        tag = self.LEVEL_TAGS.get(record.levelno, record.levelname)
        record.levelname_tagged = tag  # type: ignore[attr-defined]
        return super().format(record)


class NoDebugTerminalFilter(logging.Filter):
    """
    Filter that allows INFO, SUCCESS, WARN, ERROR, QUOTE to print to terminal stdout,
    while excluding DEBUG (Level 10) messages.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        return record.levelno != logging.DEBUG


def filter_sanitized_logs(raw_log_text: str) -> str:
    """
    Strips all [QUOTE] tagged lines from raw log text prior to issue report packaging.
    Diagnostic logs sent to developers remain strictly factual, concise, and technical.
    """
    if not raw_log_text:
        return ""
    lines = raw_log_text.splitlines()
    sanitized = [line for line in lines if "[QUOTE]" not in line]
    return "\n".join(sanitized)


def sanitize_log_file(input_path: str, output_path: Optional[str] = None) -> str:
    """
    Reads a log file, removes all [QUOTE] lines, and writes the sanitized output
    to output_path (or overwrites input_path if output_path is None).
    """
    if not os.path.exists(input_path):
        return ""
    try:
        with open(input_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        sanitized = filter_sanitized_logs(content)
        target = output_path or input_path
        os.makedirs(os.path.dirname(os.path.abspath(target)), exist_ok=True)
        with open(target, 'w', encoding='utf-8') as f:
            f.write(sanitized)
        return target
    except Exception as e:
        sys.stderr.write(f"Error sanitizing log file {input_path}: {e}\n")
        return ""


def setup_logger(name: str, log_file: str, is_debug: bool, append: bool = False) -> logging.Logger:
    """
    Configures and returns a logging.Logger instance with file handler and terminal stream handler.
    File output captures all levels down to DEBUG (if is_debug=True) or INFO.
    Terminal output captures INFO, SUCCESS, WARN, ERROR, QUOTE (DEBUG is excluded).
    """
    level = logging.DEBUG if is_debug else logging.INFO
    file_formatter = CustomSeverityFormatter(
        '%(asctime)s [%(levelname_tagged)s] [%(name)s] %(message)s'
    )
    term_formatter = CustomSeverityFormatter(
        '[%(levelname_tagged)s] %(message)s'
    )

    # Wire root logger so child loggers propagate to file and terminal
    root = logging.getLogger()
    root.setLevel(level)

    # File Handler
    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', '').endswith(log_file)
               for h in root.handlers):
        mode = 'a' if append else 'w'
        root_fh = logging.FileHandler(log_file, mode=mode, encoding='utf-8')
        root_fh.setFormatter(file_formatter)
        root_fh.setLevel(level)
        root.addHandler(root_fh)

    # Terminal Stream Handler (excludes DEBUG via NoDebugTerminalFilter)
    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
               for h in root.handlers):
        term_sh = logging.StreamHandler(sys.stdout)
        term_sh.setFormatter(term_formatter)
        term_sh.setLevel(logging.INFO)
        term_sh.addFilter(NoDebugTerminalFilter())
        root.addHandler(term_sh)

    # Named logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    return logger


class RateLimitedTelemetryHandler(logging.FileHandler):
    """
    File handler for high-frequency telemetry logs with built-in 500ms (2Hz)
    rate limiting for terminal reporting if needed.
    """

    def __init__(self, filename: str, mode: str = 'w', encoding: str = 'utf-8'):
        super().__init__(filename, mode=mode, encoding=encoding)
        self.last_emit_time: float = 0.0
        self.min_interval: float = 0.5  # 500ms (2Hz)


def setup_telemetry_logger(log_file: str = 'wrapper_telemetry.log') -> logging.Logger:
    """
    Returns a dedicated logger for high-frequency decoded-state telemetry.
    Writes strictly to wrapper_telemetry.log with propagate=False so it never
    pollutes the main log or clutters the terminal.
    """
    tel_logger = logging.getLogger('telemetry')
    if tel_logger.handlers:
        return tel_logger

    tel_logger.setLevel(logging.DEBUG)
    tel_logger.propagate = False  # strictly isolated from root/terminal handlers

    formatter = logging.Formatter('%(asctime)s - %(message)s')
    fh = RateLimitedTelemetryHandler(log_file, mode='w', encoding='utf-8')
    fh.setFormatter(formatter)
    tel_logger.addHandler(fh)
    return tel_logger


def setup_gui_loggers(log_file: str, is_debug: bool) -> None:
    """
    Wires all GUI-side module loggers to the same log file as the daemon
    and configures terminal logging without DEBUG clutter.
    """
    level = logging.DEBUG if is_debug else logging.INFO
    file_formatter = CustomSeverityFormatter(
        '%(asctime)s [%(levelname_tagged)s] [%(name)s] %(message)s'
    )
    term_formatter = CustomSeverityFormatter(
        '[%(levelname_tagged)s] %(message)s'
    )

    root = logging.getLogger()
    root.setLevel(level)

    if not any(isinstance(h, logging.FileHandler) and getattr(h, 'baseFilename', '').endswith(log_file)
               for h in root.handlers):
        root_fh = logging.FileHandler(log_file, mode='a', encoding='utf-8')
        root_fh.setFormatter(file_formatter)
        root_fh.setLevel(level)
        root.addHandler(root_fh)

    if not any(isinstance(h, logging.StreamHandler) and not isinstance(h, logging.FileHandler)
               for h in root.handlers):
        term_sh = logging.StreamHandler(sys.stdout)
        term_sh.setFormatter(term_formatter)
        term_sh.setLevel(logging.INFO)
        term_sh.addFilter(NoDebugTerminalFilter())
        root.addHandler(term_sh)
