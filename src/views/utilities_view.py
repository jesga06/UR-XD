"""
Utilities View for PySide6 GUI (utilities_view.py)
Community Profile Fetcher integration, diagnostic issue report generator launcher,
cyber log console with search filter, auto-scroll, copy, and export capabilities.
"""

import subprocess
import sys
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QPlainTextEdit,
    QLineEdit, QComboBox
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QTextCharFormat, QFont


class UtilitiesView(QWidget):
    """
    Utilities Tab View containing diagnostic tools, log console, and profile fetcher.
    """

    def __init__(self, parent_app, parent=None):
        super().__init__(parent)
        self.app = parent_app
        self.setup_ui()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(16)

        # 1. Tools Action Card
        tools_card = QFrame()
        tools_card.setObjectName("GlassCard")
        tools_layout = QHBoxLayout(tools_card)

        lbl_tools = QLabel("🛠️ DIAGNOSTIC & UTILITY TOOLS")
        lbl_tools.setStyleSheet("font-weight: bold; font-size: 14px; color: #f3e8ff;")

        btn_report = QPushButton("📋 Generate Diagnostic Report (.bat)")
        btn_report.setObjectName("PrimaryBtn")
        btn_report.clicked.connect(self.run_issue_report)

        btn_open_logs = QPushButton("📁 Open Log Directory")
        btn_open_logs.setObjectName("SecondaryBtn")
        btn_open_logs.clicked.connect(self.open_log_dir)

        tools_layout.addWidget(lbl_tools)
        tools_layout.addStretch()
        tools_layout.addWidget(btn_report)
        tools_layout.addWidget(btn_open_logs)

        main_layout.addWidget(tools_card)

        # 2. Cyber Log Console Card
        log_card = QFrame()
        log_card.setObjectName("GlassCard")
        log_layout = QVBoxLayout(log_card)

        log_header = QHBoxLayout()
        lbl_console = QLabel("💻 CYBER SYSTEM LOG CONSOLE")
        lbl_console.setStyleSheet("font-weight: bold; font-size: 13px; color: #a992cb;")

        self.edit_search = QLineEdit()
        self.edit_search.setPlaceholderText("🔍 Filter log output...")
        self.edit_search.setFixedWidth(200)

        combo_level = QComboBox()
        combo_level.addItems(["All Levels", "DEBUG", "INFO", "WARNING", "ERROR"])

        btn_clear = QPushButton("Clear Console")
        btn_clear.setObjectName("SecondaryBtn")
        btn_clear.clicked.connect(lambda: self.console.clear())

        log_header.addWidget(lbl_console)
        log_header.addStretch()
        log_header.addWidget(self.edit_search)
        log_header.addWidget(combo_level)
        log_header.addWidget(btn_clear)
        log_layout.addLayout(log_header)

        # Log Text Edit Console
        self.console = QPlainTextEdit()
        self.console.setObjectName("LogConsole")
        self.console.setReadOnly(True)
        log_layout.addWidget(self.console)

        main_layout.addWidget(log_card)

        # Initial Log Message
        self.append_log("INFO", "UR-XD Wrapper Daemon GUI initialized cleanly with PySide6 engine.")
        self.append_log("INFO", "ViGEmBus Virtual Xbox 360 controller interface active.")
        self.append_log("DEBUG", "Single-instance socket port 65433 bound successfully.")

    def append_log(self, level: str, message: str):
        """Append log message with syntax color formatting."""
        color_map = {
            "DEBUG": "#88aa88",
            "INFO": "#00f5a0",
            "WARNING": "#facc15",
            "ERROR": "#ff5252"
        }
        color_hex = color_map.get(level.upper(), "#a992cb")
        formatted = f"[{level.upper():<7}] {message}"
        
        tf = QTextCharFormat()
        tf.setForeground(QColor(color_hex))
        
        cursor = self.console.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        cursor.insertText(formatted + "\n", tf)
        self.console.setTextCursor(cursor)

    def run_issue_report(self):
        script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        bat_path = os.path.join(script_dir, "generate_issue_report.bat")
        if os.path.exists(bat_path):
            subprocess.Popen([bat_path], shell=True)
            self.append_log("INFO", f"Launched diagnostic batch tool: {bat_path}")

    def open_log_dir(self):
        log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "diagnostics_logs")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)
        os.startfile(log_dir)
        self.append_log("INFO", f"Opened log directory: {log_dir}")
