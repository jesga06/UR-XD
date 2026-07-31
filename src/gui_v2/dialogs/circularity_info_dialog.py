"""
Circularity Calibration Info Dialog for PySide6 UI (gui_v2).

Provides detailed explanation of stick circularity algorithms, polar sweep calibration,
radial normalization vs. Cartesian bounding, and Bezier response curve fitting.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
)
from PySide6.QtCore import Qt
from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6


class CircularityInfoDialog(QDialog):
    """
    Technical Info Modal detailing stick circularity math and rotational sweep calibration.
    """

    def __init__(self, theme_manager: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_manager
        self.setWindowTitle("Stick Circularity & Calibration Guide")
        self.resize(640, 520)
        self.setMinimumSize(520, 400)
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.title_lbl = QLabel("Stick Circularity & Polar Sweep Calibration", self)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet("font-size: 17px; font-weight: bold;")
        layout.addWidget(self.title_lbl)

        self.txt_content = QTextEdit(self)
        self.txt_content.setReadOnly(True)
        self.txt_content.setPlainText(self._get_info_text())
        layout.addWidget(self.txt_content)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.close_btn = QPushButton("Close", self)
        self.close_btn.setFixedWidth(120)
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        layout.addLayout(btn_layout)

    def apply_theme(self):
        """Applies dynamic theme styling using ThemeManager tokens."""
        if not self.theme_mgr:
            return

        bg_col = self.theme_mgr.get_color("background")
        acc1_col = self.theme_mgr.get_color("accent_1")

        bg_str = color_to_hex6(bg_col)
        acc1_hex = color_to_hex6(acc1_col)
        acc1_hover = color_to_rgba_str(acc1_col, 0.3)
        acc1_btn_bg = color_to_rgba_str(acc1_col, 0.15)
        border_str = color_to_rgba_str(acc1_col, 0.4)

        dialog_qss = f"""
        QDialog {{
            background-color: {bg_str};
            color: #FFFFFF;
        }}
        QLabel {{
            color: #FFFFFF;
        }}
        QTextEdit {{
            background-color: {color_to_rgba_str(bg_col, 0.9)};
            color: #EEEEEE;
            border: 1px solid {border_str};
            border-radius: 4px;
            font-family: Consolas, monospace, sans-serif;
            font-size: 12px;
            line-height: 1.4;
        }}
        QPushButton {{
            background-color: {acc1_btn_bg};
            border: 1px solid {border_str};
            border-radius: 4px;
            color: #FFFFFF;
            padding: 6px 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {acc1_hover};
            border-color: {acc1_hex};
        }}
        """
        self.setStyleSheet(dialog_qss)

    def _get_info_text(self) -> str:
        return (
            "=== STICK CIRCULARITY & POLAR SWEEP CALIBRATION ===\n\n"
            "1. WHAT IS STICK CIRCULARITY CORRECTION?\n"
            "Physical gamepad analog sticks often have non-circular outer boundaries (squarish or irregular shapes).\n"
            "This can cause diagonal inputs to exceed expected max radial limits (up to 141% input magnitude),\n"
            "leading to unnatural character movement or camera acceleration in games.\n\n"
            "2. HOW THE POLAR ROTATIONAL SWEEP WORKS:\n"
            "* Rest Measurement: Captures the resting center offset (X, Y) of the analog stick when untouched.\n"
            "* 360° Rotational Sweep: As you rotate the stick slowly around the outer edge, the engine captures\n"
            "  the maximum outer radius reached across 360 discrete angular sectors.\n"
            "* Radial Normalization: Maps irregular physical boundaries into a clean, true 1.0 unit circle.\n\n"
            "3. MODES AVAILABLE:\n"
            "* Disabled: Raw Cartesian inputs passed through directly.\n"
            "* Circular: Standard radial scaling to a perfect circular outer boundary (1.0 max radius).\n"
            "* Square: Restricts outer boundary to a sharp square boundary for games expecting square inputs.\n"
            "* Custom Polar Map: Uses your unique 360° sweep data for precise per-angle radial compensation.\n\n"
            "4. TIPS FOR BEST RESULTS:\n"
            "* Leave the stick untouched during the REST phase.\n"
            "* Perform 2-3 full 360-degree rotations steadily along the physical rim during the SWEEP phase."
        )
