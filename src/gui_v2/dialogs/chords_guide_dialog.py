"""
Hardware Chords & Macros Studio Master Guide Dialog for PySide6 UI (gui_v2).

Provides interactive, tabbed instructions on hardware input suppression, chord triggers,
delay buffers, synthetic extra button creation (M1, M2, L4, R4), and Macros Studio sequence syntax.
"""

from typing import Optional
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTabWidget, QTextEdit, QWidget
)
from PySide6.QtCore import Qt
from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6


class ChordsGuideDialog(QDialog):
    """
    Master Guide Modal explaining Hardware Chords (Input Suppression) and Macros Studio.
    """

    def __init__(self, theme_manager: Optional[ThemeManager] = None, topic: str = "all", parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_manager
        self.setWindowTitle("Macros & Hardware Chords Master Guide")
        self.resize(680, 580)
        self.setMinimumSize(560, 450)
        self.setup_ui(initial_topic=topic)
        self.apply_theme()

    def setup_ui(self, initial_topic: str = "all"):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Title
        self.title_lbl = QLabel("Macros & Hardware Chords Tutorial", self)
        self.title_lbl.setAlignment(Qt.AlignCenter)
        self.title_lbl.setStyleSheet("font-size: 18px; font-weight: bold; margin-bottom: 4px;")
        layout.addWidget(self.title_lbl)

        # Tab Widget for Topics
        self.tab_widget = QTabWidget(self)

        # 1. Overview Tab
        self.txt_overview = QTextEdit(self)
        self.txt_overview.setReadOnly(True)
        self.txt_overview.setPlainText(self._get_overview_content())
        self.tab_widget.addTab(self.txt_overview, "Overview")

        # 2. Hardware Chords Tab
        self.txt_hw = QTextEdit(self)
        self.txt_hw.setReadOnly(True)
        self.txt_hw.setPlainText(self._get_hw_content())
        self.tab_widget.addTab(self.txt_hw, "Hardware Chords Guide")

        # 3. Macros Tab
        self.txt_macros = QTextEdit(self)
        self.txt_macros.setReadOnly(True)
        self.txt_macros.setPlainText(self._get_macros_content())
        self.tab_widget.addTab(self.txt_macros, "Macros Guide")

        # Select initial tab based on topic
        if initial_topic == "hw":
            self.tab_widget.setCurrentIndex(1)
        elif initial_topic == "std":
            self.tab_widget.setCurrentIndex(2)
        else:
            self.tab_widget.setCurrentIndex(0)

        layout.addWidget(self.tab_widget)

        # Close Button Container
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
        QTabWidget::pane {{
            border: 1px solid {border_str};
            background-color: {color_to_rgba_str(bg_col, 0.8)};
            border-radius: 4px;
        }}
        QTabBar::tab {{
            background: {color_to_rgba_str(bg_col, 0.5)};
            color: #CCCCCC;
            padding: 8px 16px;
            border-top-left-radius: 4px;
            border-top-right-radius: 4px;
            border: 1px solid {border_str};
            border-bottom: none;
            margin-right: 2px;
        }}
        QTabBar::tab:selected {{
            background: {acc1_btn_bg};
            color: #FFFFFF;
            border-color: {acc1_hex};
            font-weight: bold;
        }}
        QTextEdit {{
            background-color: {color_to_rgba_str(bg_col, 0.9)};
            color: #EEEEEE;
            border: none;
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

    def _get_save_warning(self) -> str:
        return (
            "*** IMPORTANT NOTE: After creating or editing Hardware Chords or Macros, click 'Save Settings' for your changes to apply! ***\n"
            "*** CHORD BUTTON DELIMITERS: Buttons in a chord can be separated by commas (,), pluses (+), or spaces. Examples: 'dpad_up, lb', 'dpad_up + lb', 'dpad_up dpad_left dpad_right'. ***\n\n"
        )

    def _get_overview_content(self) -> str:
        return (
            "=== MACROS & HARDWARE CHORDS OVERVIEW ===\n\n"
            + self._get_save_warning() +
            "Both features enhance your controller remapping capabilities:\n\n"
            "1. HARDWARE CHORDS (INPUT SUPPRESSION)\n"
            "* Purpose: Turn physical button combinations (like dpad_up + lb) into a new extra button (like M1), while BLOCKING original buttons from reaching the game.\n"
            "* Example: Back paddles mapped to dpad_up + lb will send M1 cleanly without pressing D-Pad Up or LB in-game.\n"
            "* Requirements: Requires XInput backend mode.\n\n"
            "2. MACROS STUDIO\n"
            "* Purpose: Create named multi-step macro sequences (keyboard keys, mouse clicks, delays) that can be mapped directly to any button in the Remapping tab.\n"
            "* Example: Map 'macro:fire_combo' to the B button to trigger 'H', wait 50ms, and left-click."
        )

    def _get_hw_content(self) -> str:
        return (
            "=== HARDWARE CHORDS (INPUT SUPPRESSION) TUTORIAL ===\n\n"
            + self._get_save_warning() +
            "1. WHAT ARE HARDWARE CHORDS?\n"
            "Hardware Chords combine physical controller buttons into a single virtual extra button (like M1, M2, L4, or R4).\n\n"
            "2. WHAT IS INPUT SUPPRESSION?\n"
            "Normally, pressing a button combination sends ALL of those buttons to your game. "
            "With Hardware Chords, the physical combination gets CONSUMED by UR-XD (blocked from reaching the game). "
            "Instead, the combination becomes a 'virtual' key (like M1 or L4) which you can freely remap to keyboard keys, mouse actions, or macros in the Remapping tab!\n\n"
            "3. RECOMMENDED VS. NOT-RECOMMENDED COMBINATIONS:\n"
            "* What to look for: Pick physical button combinations that are NOT normally pressed together during normal gameplay so you don't accidentally trigger them.\n"
            "* RECOMMENDED:\n"
            "  - 'dpad_up + lb' (rarely held simultaneously)\n"
            "  - 'dpad_up + start' or 'dpad_left + select'\n"
            "  - 'dpad_down + r3' (directional pad + stick click)\n"
            "* NOT RECOMMENDED:\n"
            "  - 'a + b' or 'x + y' (frequently pressed quickly or together in games)\n"
            "  - 'lt + rt' (holding both triggers to aim + shoot is common in FPS games)\n"
            "  - 'l3 + r3' (sprinting while meleeing)\n\n"
            "4. STEP-BY-STEP SETUP GUIDE:\n"
            "* Step 1: Ensure your controller is in XInput mode.\n"
            "* Step 2: Under 'Hardware Chords (Input Suppression)', click '+ Add Hardware Chord'.\n"
            "* Step 3: 'Chord:' - Enter the controller buttons you press together (example: dpad_up, lb or dpad_up dpad_left dpad_right).\n"
            "* Step 4: 'Action:' - Enter the new extra button name you want to trigger (example: M1 or extra_1).\n"
            "* Step 5: 'Delayed:' - (Optional) Enter any button that should wait briefly to ensure both buttons are pressed together out-of-sync (example: dpad_up).\n"
            "* Step 6: 'Mode:' - Select timing delay: 'auto', '0ms', '50ms', or '100ms'.\n"
            "* Step 7: Save your settings to save your config and update the Remapping tab!"
        )

    def _get_macros_content(self) -> str:
        return (
            "=== MACROS STUDIO TUTORIAL ===\n\n"
            + self._get_save_warning() +
            "1. WHAT ARE MACROS?\n"
            "Macros let you trigger automated keyboard keys, mouse clicks, or multi-step action sequences from any controller button.\n\n"
            "2. EXECUTION MODES:\n"
            "* One-shot: Executes sequence once per button press.\n"
            "* Toggle Mode: Press once to start macro execution, press again to cancel immediately.\n"
            "* Hold/Loop Mode: Repeats sequence continuously as long as the mapped trigger button is held down.\n\n"
            "3. STEP-BY-STEP SETUP GUIDE:\n"
            "* Step 1: Under 'Macros Studio', click '+ Add Macro'.\n"
            "* Step 2: 'Name:' - Enter a short, unique name for your macro (example: fire_combo).\n"
            "* Step 3: 'Outputs:' - Enter the keys, clicks, or delays to trigger (example: keyboard:h, wait:50, mouse:left). You can also click '[Rec]' to record steps interactively.\n"
            "* Step 4: Click 'Save Settings' at the bottom of the section to save your macro.\n"
            "* Step 5: Switch to the Remapping tab and assign the macro to any controller button by entering 'macro:fire_combo' or 'fire_combo'!"
        )
