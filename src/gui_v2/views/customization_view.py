"""
Customization View Module for PySide6 UI (gui_v2).
Provides live dynamic color token customization, color picker dialogs with alpha channels,
theme import/export JSON functionality, factory defaults reset, and embedded dynamic theme preview.
"""

import sys
import os
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QLineEdit, QColorDialog, QFileDialog, QScrollArea, QMessageBox
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, Slot

# Import ThemeManager and ThemePreviewWidget
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from gui_v2.services.theme_manager import ThemeManager, color_to_hex8, color_to_rgba_str
from gui_v2.widgets.theme_preview_widget import ThemePreviewWidget


class CustomizationView(QWidget):
    """
    Main Customization View tab allowing users to customize accent_1, accent_2, and background colors,
    open alpha-enabled color dialogs, import/export theme JSON files, reset default themes,
    and preview changes live via ThemePreviewWidget.
    """
    def __init__(self, theme_manager: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_manager or ThemeManager.get_instance()
        self.theme_mgr.theme_changed.connect(self.on_theme_changed)

        self.preview_swatches: Dict[str, QFrame] = {}
        self.hex_labels: Dict[str, QLabel] = {}

        self.setup_ui()
        self.refresh_color_display(self.theme_mgr.tokens)

    def setup_ui(self):
        """Constructs the visual layout for the Customization tab."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)

        # Scroll Area container to support small monitors cleanly
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet("background: transparent;")

        scroll_content = QWidget()
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(14)

        # 1. THEME COLOR TOKENS & CONTROLS CARD
        self.controls_card = QFrame()
        self.controls_card.setObjectName("controls_card")
        card_layout = QVBoxLayout(self.controls_card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)

        header_label = QLabel("THEME COLOR TOKENS & CONTROLS")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        card_layout.addWidget(header_label)

        # Token Rows Definition
        token_configs = [
            ("accent_1", "Accent #1 (Input Color):", "(Used for physical input visualizers)"),
            ("accent_2", "Accent #2 (Output Color):", "(Used for virtual output visualizers)"),
            ("background", "Background Color:", "(Used for card bases and window)")
        ]

        for token_key, title, description in token_configs:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)

            title_lbl = QLabel(title)
            title_lbl.setFixedWidth(160)
            title_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #ffffff;")

            pick_btn = QPushButton("🎨 Pick Color")
            pick_btn.setFixedWidth(110)
            pick_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            pick_btn.clicked.connect(lambda _, k=token_key: self.open_color_picker(k))

            preview_lbl = QLabel("Preview:")
            preview_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.7); font-size: 11px;")

            # Color Swatch Box
            swatch_box = QFrame()
            swatch_box.setFixedSize(28, 22)
            swatch_box.setStyleSheet("border: 1px solid #ffffff; border-radius: 4px;")
            self.preview_swatches[token_key] = swatch_box

            # Hex Value Display
            hex_val_lbl = QLabel("#FFFFFFFF")
            hex_val_lbl.setFixedWidth(95)
            hex_val_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            hex_val_lbl.setStyleSheet("""
                background: rgba(0, 0, 0, 0.35);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                padding: 2px 6px;
                font-family: 'Consolas', 'Courier New', monospace;
                font-size: 11px;
                color: #ffffff;
            """)
            self.hex_labels[token_key] = hex_val_lbl

            desc_lbl = QLabel(description)
            desc_lbl.setStyleSheet("color: rgba(255, 255, 255, 0.6); font-size: 11px; font-style: italic;")

            row_layout.addWidget(title_lbl)
            row_layout.addWidget(pick_btn)
            row_layout.addWidget(preview_lbl)
            row_layout.addWidget(swatch_box)
            row_layout.addWidget(hex_val_lbl)
            row_layout.addWidget(desc_lbl)
            row_layout.addStretch()

            card_layout.addLayout(row_layout)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); max-height: 1px;")
        card_layout.addWidget(divider)

        # Actions Row
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(12)

        actions_title = QLabel("Actions:")
        actions_title.setStyleSheet("font-weight: bold; font-size: 12px; color: #ffffff;")
        actions_layout.addWidget(actions_title)

        import_btn = QPushButton("📥 Import Theme JSON")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self.import_theme_dialog)
        actions_layout.addWidget(import_btn)

        export_btn = QPushButton("💾 Export Theme JSON")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self.export_theme_dialog)
        actions_layout.addWidget(export_btn)

        reset_btn = QPushButton("🔄 Reset Default Theme")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self.reset_default_theme)
        actions_layout.addWidget(reset_btn)

        actions_layout.addStretch()
        card_layout.addLayout(actions_layout)

        content_layout.addWidget(self.controls_card)

        # 2. LIVE INTERACTIVE THEME PREVIEW PANEL
        self.preview_panel = ThemePreviewWidget(self.theme_mgr)
        content_layout.addWidget(self.preview_panel)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.update_card_styles()

    @Slot(dict)
    def on_theme_changed(self, tokens: dict):
        """Callback invoked when theme tokens are modified or reset."""
        self.refresh_color_display(tokens)
        self.update_card_styles()

    def refresh_color_display(self, tokens: dict):
        """Updates color swatches and hex labels in control rows."""
        for token_key in ["accent_1", "accent_2", "background"]:
            if token_key in tokens:
                hex_str = tokens[token_key]
                color = self.theme_mgr.get_color(token_key)

                # Update Swatch Box
                swatch = self.preview_swatches.get(token_key)
                if swatch:
                    rgba_str = color_to_rgba_str(color)
                    swatch.setStyleSheet(f"background-color: {rgba_str}; border: 1.5px solid #ffffff; border-radius: 4px;")

                # Update Hex Label
                lbl = self.hex_labels.get(token_key)
                if lbl:
                    lbl.setText(hex_str)

    def update_card_styles(self):
        """Applies dynamic QSS tokens to controls card."""
        bg_color = self.theme_mgr.get_color("background")
        accent_1 = self.theme_mgr.get_color("accent_1")

        bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
        border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)
        accent_1_subtle = color_to_rgba_str(accent_1, alpha_override=0.20)
        accent_1_hex = color_to_hex8(accent_1)

        style = f"""
        QFrame#controls_card {{
            background-color: {bg_glass};
            border: 1.5px solid {border_glass};
            border-radius: 12px;
        }}

        QPushButton {{
            background-color: {accent_1_subtle};
            border: 1px solid {border_glass};
            color: #ffffff;
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: rgba({accent_1.red()}, {accent_1.green()}, {accent_1.blue()}, 0.40);
            border: 1px solid {accent_1_hex};
        }}

        QPushButton:pressed {{
            background-color: rgba({accent_1.red()}, {accent_1.green()}, {accent_1.blue()}, 0.60);
        }}
        """
        self.controls_card.setStyleSheet(style)

    def open_color_picker(self, token_key: str):
        """Launches QColorDialog initialized with ShowAlphaChannel option."""
        current_color = self.theme_mgr.get_color(token_key)
        dialog = QColorDialog(current_color, self)
        dialog.setOption(QColorDialog.ColorDialogOption.ShowAlphaChannel, True)
        dialog.setWindowTitle(f"Select Color for {token_key.replace('_', ' ').title()}")

        if dialog.exec() == QColorDialog.DialogCode.Accepted:
            new_color = dialog.currentColor()
            hex_str = color_to_hex8(new_color)
            self.theme_mgr.set_token(token_key, hex_str)

    def import_theme_dialog(self):
        """Opens QFileDialog to select JSON theme file for import."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Theme JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            success = self.theme_mgr.import_theme(file_path)
            if success:
                QMessageBox.information(self, "Theme Imported", "Theme configuration was successfully applied.")
            else:
                QMessageBox.warning(self, "Import Failed", "Could not import the selected theme file.")

    def export_theme_dialog(self):
        """Opens QFileDialog to save current theme tokens to JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Theme JSON", "custom_theme.json", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            success = self.theme_mgr.export_theme(file_path)
            if success:
                QMessageBox.information(self, "Theme Exported", f"Theme saved to:\n{file_path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Could not export the theme file.")

    def reset_default_theme(self):
        """Restores factory default theme tokens."""
        confirm = QMessageBox.question(
            self, "Reset Theme",
            "Are you sure you want to restore the default theme colors?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.theme_mgr.reset_defaults()
