"""
Remapping & Shift Layers Master Guide Dialog for PySide6 UI (gui_v2).

Provides comprehensive instructions on mapping syntax, shift layer creation,
hold vs. toggle activation modes, shift block, macro referencing, and interactive key recording.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit
)
from PySide6.QtCore import Qt
from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6


class RemappingGuideDialog(QDialog):
    """
    Master Guide Modal explaining Remapping syntaxes, Shift Layers, Macros, and Button Blocking.
    """

    def __init__(self, theme_manager: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_manager
        self.setWindowTitle("Remapping & Shift Layers Master Guide")
        self.resize(680, 560)
        self.setMinimumSize(560, 450)
        self.setup_ui()
        self.apply_theme()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.title_lbl = QLabel("Remapping & Shift Layers Master Guide", self)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        layout.addWidget(self.title_lbl)

        self.txt_content = QTextEdit(self)
        self.txt_content.setReadOnly(True)
        self.txt_content.setPlainText(self._get_guide_text())
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

    def _get_guide_text(self) -> str:
        return (
            "=== REMAPPING & SHIFT LAYERS MASTER GUIDE ===\n\n"
            "1. KEYBOARD & MOUSE MAPPING:\n"
            "* Plain Keyboard Key: Type the key directly (example: 'h', 'space', 'e', 'f1').\n"
            "* Explicit Keyboard Prefix: Type 'keyboard:key_name' (example: 'keyboard:space', 'keyboard:left_shift').\n"
            "* Mouse Clicks: Type 'mouse:left', 'mouse:right', 'mouse:middle', 'mouse4', or 'mouse5'.\n"
            "* Mouse Scroll: Type 'mouse:scroll_up' or 'mouse:scroll_down'.\n\n"
            "2. MULTIPLE SHIFT LAYERS (SECONDARY REMAPPING PROFILES):\n"
            "* Shift Layers allow your controller buttons to perform a completely different set of actions when a designated activation key is held or toggled.\n"
            "* Adding Layers: Click '+ Add Layer' in the Shift Tab Bar at the top of the Remapping tab to create additional shift layers (e.g. Shift 1, Shift 2).\n"
            "* Trigger Button & Modifier Key: Set a primary activation button (e.g. 'lb') or a 2-button chord (e.g. Trigger 'lb' + Modifier 'rb').\n"
            "* Hold Mode vs Toggle Mode:\n"
            "  - Hold: The Shift Layer is active strictly while holding down the activation button(s).\n"
            "  - Toggle: Pressing the activation button(s) once toggles the Shift Layer ON or OFF permanently until pressed again.\n"
            "* Shift Block (S. Blk): Check 'S. Blk' next to any button to block its native controller signal ONLY while that Shift layer is active.\n\n"
            "3. REFERENCING MACROS BY NAME (macro:MyMacro):\n"
            "* You can map any macro created in the Advanced tab directly to any button in the Remapping tab!\n"
            "* Usage: Enter 'macro:MacroName' or simply 'MacroName' into the button's mapping entry (example: 'macro:FireCombo' or 'FireCombo').\n\n"
            "4. BUTTON BLOCKING (Block vs S. Blk):\n"
            "* Check 'Block' to prevent the controller's original native button press from reaching the game (useful when remapping to keyboard/mouse or macros).\n"
            "* Check 'S. Blk' to block the original native button press only when the selected Shift layer is active.\n\n"
            "5. INTERACTIVE RECORDING ([Rec]):\n"
            "* Click the '[Rec]' button next to any remapping entry to interactively record key combinations or macro steps."
        )
