"""
Shift Layer Home Button Hold Warning Dialog for PySide6 UI (gui_v2).

Displays a non-blocking warning modal advising users against using the Home/Guide button
as a Shift Layer trigger in 'hold' mode due to controller power-off behaviors and OS shortcuts.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt
from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6


class HomeWarningDialog(QDialog):
    """
    Warning Modal shown when the Home/Guide button is configured as a Shift Trigger in Hold mode.
    """

    def __init__(self, theme_manager: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_manager
        self.setWindowTitle("Recommended Setting Notice")
        self.setFixedSize(480, 240)
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        self.title_lbl = QLabel("⚠️ Shift Key Recommendation Notice", self)
        self.title_lbl.setStyleSheet("font-size: 15px; font-weight: bold; color: #FFAA00;")
        layout.addWidget(self.title_lbl)

        msg_text = (
            "Holding the Home/Guide button for several seconds may force turn off "
            "your controller or trigger OS shortcuts (e.g., Xbox Game Bar / Steam Overlay).\n\n"
            "It is strongly recommended to set the Shift Mode to 'toggle' instead of 'hold' "
            "when using the Home button as your Shift Key."
        )
        self.msg_lbl = QLabel(msg_text, self)
        self.msg_lbl.setWordWrap(True)
        self.msg_lbl.setStyleSheet("font-size: 12px; line-height: 1.4;")
        layout.addWidget(self.msg_lbl)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.ok_btn = QPushButton("Understand & Continue", self)
        self.ok_btn.setFixedWidth(160)
        self.ok_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.ok_btn)

        layout.addLayout(btn_layout)

    def apply_theme(self):
        """Applies dynamic theme styling using ThemeManager tokens."""
        if not self.theme_mgr:
            return

        bg_col = self.theme_mgr.get_color("background")
        acc2_col = self.theme_mgr.get_color("accent_2")

        bg_str = color_to_hex6(bg_col)
        acc2_hex = color_to_hex6(acc2_col)
        acc2_hover = color_to_rgba_str(acc2_col, 0.3)
        acc2_btn_bg = color_to_rgba_str(acc2_col, 0.15)
        border_str = color_to_rgba_str(acc2_col, 0.4)

        dialog_qss = f"""
        QDialog {{
            background-color: {bg_str};
            color: #FFFFFF;
        }}
        QLabel {{
            color: #EEEEEE;
        }}
        QPushButton {{
            background-color: {acc2_btn_bg};
            border: 1px solid {border_str};
            border-radius: 4px;
            color: #FFFFFF;
            padding: 6px 14px;
            font-weight: bold;
        }}
        QPushButton:hover {{
            background-color: {acc2_hover};
            border-color: {acc2_hex};
        }}
        """
        self.setStyleSheet(dialog_qss)
