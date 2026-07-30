"""
Customization View Module for PySide6 UI (gui_v2).
Provides live dynamic color token customization, pre-built theme presets dropdown,
theme CRUD management (Save, Rename, Copy, Delete), alpha-capable color pickers,
theme import/export JSON functionality, and embedded dynamic theme preview panel.
"""

import sys
import os
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QLineEdit, QColorDialog, QFileDialog, QScrollArea, QMessageBox,
    QComboBox, QInputDialog
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, Slot

# Import ThemeManager and ThemePreviewWidget
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from gui_v2.services.theme_manager import ThemeManager, color_to_hex8, color_to_rgba_str
from gui_v2.widgets.theme_preview_widget import ThemePreviewWidget


class CustomizationView(QWidget):
    """
    Main Customization View tab allowing users to switch pre-built system themes,
    manage custom themes (Save, Rename, Copy, Delete), pick Accent #1, Accent #2, and Background colors,
    and preview all changes live via ThemePreviewWidget.
    """
    def __init__(self, theme_manager: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_manager or ThemeManager.get_instance()
        self.theme_mgr.theme_changed.connect(self.on_theme_changed)

        self.preview_swatches: Dict[str, QFrame] = {}
        self.hex_labels: Dict[str, QLabel] = {}
        self._block_dropdown_signals: bool = False

        self.setup_ui()
        self.populate_theme_dropdown()
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

        # 1. PRESET THEMES & MANAGEMENT CARD
        self.preset_card = QFrame()
        self.preset_card.setObjectName("preset_card")
        preset_layout = QVBoxLayout(self.preset_card)
        preset_layout.setContentsMargins(16, 14, 16, 14)
        preset_layout.setSpacing(10)

        preset_title = QLabel("THEME PRESETS & MANAGEMENT")
        preset_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        preset_layout.addWidget(preset_title)

        toolbar_layout = QHBoxLayout()
        toolbar_layout.setSpacing(10)

        theme_lbl = QLabel("Active Theme:")
        theme_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #ffffff;")
        toolbar_layout.addWidget(theme_lbl)

        # Theme Dropdown
        self.theme_dropdown = QComboBox()
        self.theme_dropdown.setMinimumWidth(220)
        self.theme_dropdown.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_dropdown.currentTextChanged.connect(self.on_theme_selected)
        toolbar_layout.addWidget(self.theme_dropdown)

        # CRUD Toolbar Buttons
        save_btn = QPushButton("💾 Save Theme")
        save_btn.setToolTip("Save current color tokens as a new custom theme")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_theme_dialog)
        toolbar_layout.addWidget(save_btn)

        rename_btn = QPushButton("✏️ Rename")
        rename_btn.setToolTip("Rename currently selected user theme")
        rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rename_btn.clicked.connect(self.rename_theme_dialog)
        toolbar_layout.addWidget(rename_btn)

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setToolTip("Duplicate currently selected theme")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self.copy_theme_dialog)
        toolbar_layout.addWidget(copy_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setToolTip("Delete currently selected user theme")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self.delete_theme_dialog)
        toolbar_layout.addWidget(delete_btn)

        toolbar_layout.addStretch()
        preset_layout.addLayout(toolbar_layout)

        content_layout.addWidget(self.preset_card)

        # 2. THEME COLOR TOKENS & CONTROLS CARD
        self.controls_card = QFrame()
        self.controls_card.setObjectName("controls_card")
        card_layout = QVBoxLayout(self.controls_card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)

        header_label = QLabel("COLOR TOKENS & ALPHA PICKERS")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        card_layout.addWidget(header_label)

        # Token Rows Definition
        token_configs = [
            ("accent_1", "Accent #1 (Input Color):", "(Used for physical input visualizers)"),
            ("accent_2", "Accent #2 (Output Color):", "(Used for virtual output visualizers)"),
            ("background", "Widget Background:", "(Used for card fill and container bases)"),
            ("window_bg", "Window Background:", "(Used for main window canvas base, pure black by default)")
        ]

        for token_key, title, description in token_configs:
            row_layout = QHBoxLayout()
            row_layout.setSpacing(10)

            title_lbl = QLabel(title)
            title_lbl.setFixedWidth(180)
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

        actions_title = QLabel("File Actions:")
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

        # 3. LIVE INTERACTIVE THEME PREVIEW PANEL
        self.preview_panel = ThemePreviewWidget(self.theme_mgr)
        content_layout.addWidget(self.preview_panel)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.update_card_styles()

    def populate_theme_dropdown(self):
        """Discovers presets and user themes and populates dropdown."""
        self._block_dropdown_signals = True
        self.theme_dropdown.clear()

        available = self.theme_mgr.get_available_themes()

        # Add System Presets
        for name, meta in available.items():
            if meta["is_preset"]:
                self.theme_dropdown.addItem(f"{name} (Preset)", userData=name)

        # Add Separator if user themes exist
        has_user_themes = any(not meta["is_preset"] for meta in available.values())
        if has_user_themes:
            self.theme_dropdown.insertSeparator(self.theme_dropdown.count())
            for name, meta in available.items():
                if not meta["is_preset"]:
                    self.theme_dropdown.addItem(name, userData=name)

        # Match current active theme name
        current_name = self.theme_mgr.active_theme_name
        index = -1
        for i in range(self.theme_dropdown.count()):
            if self.theme_dropdown.itemData(i) == current_name:
                index = i
                break

        if index >= 0:
            self.theme_dropdown.setCurrentIndex(index)

        self._block_dropdown_signals = False

    def on_theme_selected(self, item_text: str):
        """Triggered when user selects a theme from the dropdown."""
        if self._block_dropdown_signals or not item_text:
            return

        current_index = self.theme_dropdown.currentIndex()
        theme_name = self.theme_dropdown.itemData(current_index)
        if theme_name:
            self.theme_mgr.apply_theme_by_name(theme_name)

    @Slot(dict)
    def on_theme_changed(self, tokens: dict):
        """Callback invoked when theme tokens are modified or reset."""
        self.refresh_color_display(tokens)
        self.update_card_styles()
        self.populate_theme_dropdown()

    def refresh_color_display(self, tokens: dict):
        """Updates color swatches and hex labels in control rows."""
        for token_key in ["accent_1", "accent_2", "background", "window_bg"]:
            if token_key in tokens:
                hex_str = tokens[token_key]
                color = self.theme_mgr.get_color(token_key)

                swatch = self.preview_swatches.get(token_key)
                if swatch:
                    rgba_str = color_to_rgba_str(color)
                    swatch.setStyleSheet(f"background-color: {rgba_str}; border: 1.5px solid #ffffff; border-radius: 4px;")

                lbl = self.hex_labels.get(token_key)
                if lbl:
                    lbl.setText(hex_str)

    def update_card_styles(self):
        """Applies dynamic QSS tokens to cards."""
        bg_color = self.theme_mgr.get_color("background")
        accent_1 = self.theme_mgr.get_color("accent_1")

        bg_glass = color_to_rgba_str(bg_color, alpha_override=0.85)
        border_glass = color_to_rgba_str(accent_1, alpha_override=0.35)
        accent_1_subtle = color_to_rgba_str(accent_1, alpha_override=0.20)
        accent_1_hex = color_to_hex8(accent_1)

        style = f"""
        QFrame#controls_card, QFrame#preset_card {{
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
        self.preset_card.setStyleSheet(style)

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

    def save_theme_dialog(self):
        """Prompts user for theme name and saves user custom theme."""
        name, ok = QInputDialog.getText(self, "Save Custom Theme", "Enter a name for this custom theme:")
        if ok and name.strip():
            success = self.theme_mgr.save_user_theme(name.strip())
            if success:
                QMessageBox.information(self, "Theme Saved", f"Custom theme '{name.strip()}' saved successfully.")
            else:
                QMessageBox.warning(self, "Save Failed", "Could not save custom theme.")

    def rename_theme_dialog(self):
        """Prompts user to rename the currently selected custom theme."""
        current_index = self.theme_dropdown.currentIndex()
        current_name = self.theme_dropdown.itemData(current_index)
        available = self.theme_mgr.get_available_themes()

        if not current_name or current_name not in available or available[current_name]["is_preset"]:
            QMessageBox.warning(self, "Protected Theme", "Pre-built system presets cannot be renamed. Please save as a new theme first.")
            return

        new_name, ok = QInputDialog.getText(self, "Rename Theme", f"Enter new name for '{current_name}':", text=current_name)
        if ok and new_name.strip() and new_name.strip() != current_name:
            success = self.theme_mgr.rename_user_theme(current_name, new_name.strip())
            if success:
                QMessageBox.information(self, "Theme Renamed", f"Theme renamed to '{new_name.strip()}'.")
            else:
                QMessageBox.warning(self, "Rename Failed", "Could not rename selected theme.")

    def copy_theme_dialog(self):
        """Prompts user to duplicate the currently selected theme."""
        current_index = self.theme_dropdown.currentIndex()
        current_name = self.theme_dropdown.itemData(current_index) or "Theme"
        default_copy_name = f"{current_name} (Copy)"

        new_name, ok = QInputDialog.getText(self, "Copy Theme", f"Enter name for the duplicate theme:", text=default_copy_name)
        if ok and new_name.strip():
            success = self.theme_mgr.copy_theme(current_name, new_name.strip())
            if success:
                QMessageBox.information(self, "Theme Copied", f"Theme duplicated as '{new_name.strip()}'.")
            else:
                QMessageBox.warning(self, "Copy Failed", "Could not copy selected theme.")

    def delete_theme_dialog(self):
        """Prompts confirmation to delete currently selected custom theme."""
        current_index = self.theme_dropdown.currentIndex()
        current_name = self.theme_dropdown.itemData(current_index)
        available = self.theme_mgr.get_available_themes()

        if not current_name or current_name not in available or available[current_name]["is_preset"]:
            QMessageBox.warning(self, "Protected Theme", "Pre-built system presets cannot be deleted.")
            return

        confirm = QMessageBox.question(
            self, "Delete Theme",
            f"Are you sure you want to permanently delete the custom theme '{current_name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            success = self.theme_mgr.delete_user_theme(current_name)
            if success:
                QMessageBox.information(self, "Theme Deleted", f"Custom theme '{current_name}' deleted.")
            else:
                QMessageBox.warning(self, "Delete Failed", "Could not delete selected theme.")

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
