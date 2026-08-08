"""
Customization View Module for PySide6 UI (gui_v2).
Provides live dynamic base color pickers (Window Background, Accent #1, Accent #2, Text),
theme behavior source toggles (Button Color, Widget Background, Outline Color),
brightness adjustment sliders (-80% to +80%), pre-built theme presets dropdown,
theme CRUD management (Save, Rename, Copy, Delete), theme import/export JSON functionality,
and embedded dynamic theme preview panel.
"""

import sys
import os
from typing import Optional, Dict

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton,
    QColorDialog, QFileDialog, QScrollArea, QMessageBox,
    QComboBox, QSlider, QGroupBox
)
from PySide6.QtGui import QColor, QFont
from PySide6.QtCore import Qt, Slot

# Import ThemeManager and ThemePreviewWidget
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from gui_v2.services.theme_manager import ThemeManager, color_to_hex8, color_to_hex6, color_to_rgba_str
from gui_v2.widgets.theme_preview_widget import ThemePreviewWidget


class CustomizationView(QWidget):
    """
    Main Customization View tab providing exposed base color pickers, behavior source toggles,
    brightness sliders, preset theme switching, custom theme CRUD management, and live preview.
    """
    def __init__(self, theme_manager: Optional[ThemeManager] = None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_manager or ThemeManager.get_instance()
        self.theme_mgr.staging_changed.connect(self.on_theme_changed)
        self.theme_mgr.theme_changed.connect(self.on_theme_changed)

        self.preview_swatches: Dict[str, QFrame] = {}
        self.hex_labels: Dict[str, QLabel] = {}
        self._block_signals: bool = False

        self.setup_ui()
        self.populate_theme_dropdown()
        self.refresh_ui_from_theme(self.theme_mgr.tokens)

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

        # Row 1: Active Theme Selection & Sandbox Actions
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(10)

        theme_lbl = QLabel("Active Theme:")
        theme_lbl.setStyleSheet("font-weight: bold; font-size: 12px; color: #ffffff;")
        row1_layout.addWidget(theme_lbl)

        # Theme Dropdown
        self.theme_dropdown = QComboBox()
        self.theme_dropdown.setMinimumWidth(200)
        self.theme_dropdown.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_dropdown.currentTextChanged.connect(self.on_theme_selected)
        row1_layout.addWidget(self.theme_dropdown)

        save_btn = QPushButton("💾 Save Theme")
        save_btn.setToolTip("Save current draft colors, toggles, and sliders as a custom theme")
        save_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        save_btn.clicked.connect(self.save_theme_dialog)
        row1_layout.addWidget(save_btn)

        apply_app_btn = QPushButton("⚡ Apply App-Wide")
        apply_app_btn.setToolTip("Apply current draft colors across all application tabs without creating a new file")
        apply_app_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        apply_app_btn.clicked.connect(self.apply_app_wide)
        row1_layout.addWidget(apply_app_btn)

        discard_btn = QPushButton("↩ Discard Edits")
        discard_btn.setToolTip("Revert draft edits back to active saved theme")
        discard_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        discard_btn.clicked.connect(self.discard_edits)
        row1_layout.addWidget(discard_btn)

        row1_layout.addStretch()
        preset_layout.addLayout(row1_layout)

        # Row 2: Theme Management & File Actions
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(10)

        rename_btn = QPushButton("✏️ Rename")
        rename_btn.setToolTip("Rename currently selected user theme")
        rename_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rename_btn.clicked.connect(self.rename_theme_dialog)
        row2_layout.addWidget(rename_btn)

        copy_btn = QPushButton("📋 Copy")
        copy_btn.setToolTip("Duplicate currently selected theme")
        copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        copy_btn.clicked.connect(self.copy_theme_dialog)
        row2_layout.addWidget(copy_btn)

        delete_btn = QPushButton("🗑️ Delete")
        delete_btn.setToolTip("Delete currently selected user theme")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.clicked.connect(self.delete_theme_dialog)
        row2_layout.addWidget(delete_btn)

        # Divider element
        row2_divider = QFrame()
        row2_divider.setFrameShape(QFrame.Shape.VLine)
        row2_divider.setStyleSheet("background-color: rgba(255, 255, 255, 0.2); max-width: 1px;")
        row2_layout.addWidget(row2_divider)

        import_btn = QPushButton("📥 Import Theme")
        import_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        import_btn.clicked.connect(self.import_theme_dialog)
        row2_layout.addWidget(import_btn)

        export_btn = QPushButton("💾 Export Theme")
        export_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        export_btn.clicked.connect(self.export_theme_dialog)
        row2_layout.addWidget(export_btn)

        invert_btn = QPushButton("🔀 Invert Accents")
        invert_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        invert_btn.clicked.connect(self.invert_accents)
        row2_layout.addWidget(invert_btn)

        reset_btn = QPushButton("🔄 Reset Defaults")
        reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        reset_btn.clicked.connect(self.reset_default_theme)
        row2_layout.addWidget(reset_btn)

        row2_layout.addStretch()
        preset_layout.addLayout(row2_layout)
        content_layout.addWidget(self.preset_card)

        # 2. EXPOSED BASE COLOR PICKERS CARD
        self.controls_card = QFrame()
        self.controls_card.setObjectName("controls_card")
        card_layout = QVBoxLayout(self.controls_card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(12)

        header_label = QLabel("EXPOSED BASE COLORS (ALPHA PICKERS)")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        card_layout.addWidget(header_label)

        # Token Rows Definition for 4 Base Colors
        base_color_configs = [
            ("window_bg", "Window Background:", "(Base frame and application window background)"),
            ("accent_1", "Accent #1 (Input):", "(Primary color used by hardware input visualizers)"),
            ("accent_2", "Accent #2 (Output):", "(Secondary color used by virtual output visualizers)"),
            ("text", "Text Color:", "(Global text color for labels, titles, and fields)")
        ]

        for token_key, title, description in base_color_configs:
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

        content_layout.addWidget(self.controls_card)

        # 3. SOURCE SELECTORS & BRIGHTNESS SLIDERS CARD
        self.behavior_card = QFrame()
        self.behavior_card.setObjectName("behavior_card")
        behavior_layout = QVBoxLayout(self.behavior_card)
        behavior_layout.setContentsMargins(16, 14, 16, 14)
        behavior_layout.setSpacing(14)

        behavior_title = QLabel("THEME BEHAVIOR TOGGLES & BRIGHTNESS SLIDERS")
        behavior_title.setStyleSheet("font-weight: bold; font-size: 14px; color: #ffffff;")
        behavior_layout.addWidget(behavior_title)

        # Source Selection Row
        sources_layout = QHBoxLayout()
        sources_layout.setSpacing(16)

        # Button Color Source
        btn_src_box = QVBoxLayout()
        btn_src_lbl = QLabel("Button Color Source:")
        btn_src_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        self.btn_src_combo = QComboBox()
        self.btn_src_combo.addItem("Window Background", "window_bg")
        self.btn_src_combo.addItem("Accent #1", "accent_1")
        self.btn_src_combo.addItem("Accent #2", "accent_2")
        self.btn_src_combo.currentIndexChanged.connect(self.on_sources_changed)
        btn_src_box.addWidget(btn_src_lbl)
        btn_src_box.addWidget(self.btn_src_combo)
        sources_layout.addLayout(btn_src_box)

        # Widget Background Source
        wbg_src_box = QVBoxLayout()
        wbg_src_lbl = QLabel("Widget Background Source:")
        wbg_src_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        self.wbg_src_combo = QComboBox()
        self.wbg_src_combo.addItem("Window Background", "window_bg")
        self.wbg_src_combo.addItem("Accent #1", "accent_1")
        self.wbg_src_combo.addItem("Accent #2", "accent_2")
        self.wbg_src_combo.currentIndexChanged.connect(self.on_sources_changed)
        wbg_src_box.addWidget(wbg_src_lbl)
        wbg_src_box.addWidget(self.wbg_src_combo)
        sources_layout.addLayout(wbg_src_box)

        # Outline Color Source
        out_src_box = QVBoxLayout()
        out_src_lbl = QLabel("Outline Color Source:")
        out_src_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        self.out_src_combo = QComboBox()
        self.out_src_combo.addItem("Window Background", "window_bg")
        self.out_src_combo.addItem("Accent #1", "accent_1")
        self.out_src_combo.addItem("Accent #2", "accent_2")
        self.out_src_combo.currentIndexChanged.connect(self.on_sources_changed)
        out_src_box.addWidget(out_src_lbl)
        out_src_box.addWidget(self.out_src_combo)
        sources_layout.addLayout(out_src_box)

        # Graph Axes Source
        ga_src_box = QVBoxLayout()
        ga_src_lbl = QLabel("Graph Axes Source:")
        ga_src_lbl.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        self.ga_src_combo = QComboBox()
        self.ga_src_combo.addItem("Window Background", "window_bg")
        self.ga_src_combo.addItem("Accent #1", "accent_1")
        self.ga_src_combo.addItem("Accent #2", "accent_2")
        self.ga_src_combo.currentIndexChanged.connect(self.on_sources_changed)
        ga_src_box.addWidget(ga_src_lbl)
        ga_src_box.addWidget(self.ga_src_combo)
        sources_layout.addLayout(ga_src_box)

        sources_layout.addStretch()
        behavior_layout.addLayout(sources_layout)

        # Divider
        divider1 = QFrame()
        divider1.setFrameShape(QFrame.Shape.HLine)
        divider1.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); max-height: 1px;")
        behavior_layout.addWidget(divider1)

        # Sliders Section
        sliders_layout = QVBoxLayout()
        sliders_layout.setSpacing(10)

        # Widget Brightness Slider
        w_slider_row = QHBoxLayout()
        w_slider_title = QLabel("Widget Brightness:")
        w_slider_title.setFixedWidth(160)
        w_slider_title.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        self.widget_brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.widget_brightness_slider.setRange(0, 20)
        self.widget_brightness_slider.setValue(0)
        self.widget_brightness_slider.valueChanged.connect(self.on_widget_brightness_changed)
        self.widget_brightness_label = QLabel("0%")
        self.widget_brightness_label.setFixedWidth(50)
        self.widget_brightness_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")

        w_slider_row.addWidget(w_slider_title)
        w_slider_row.addWidget(self.widget_brightness_slider)
        w_slider_row.addWidget(self.widget_brightness_label)
        sliders_layout.addLayout(w_slider_row)

        # Graph Brightness Slider
        g_slider_row = QHBoxLayout()
        g_slider_title = QLabel("Graph Brightness:")
        g_slider_title.setFixedWidth(160)
        g_slider_title.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        self.graph_brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.graph_brightness_slider.setRange(0, 20)
        self.graph_brightness_slider.setValue(0)
        self.graph_brightness_slider.valueChanged.connect(self.on_graph_brightness_changed)
        self.graph_brightness_label = QLabel("0%")
        self.graph_brightness_label.setFixedWidth(50)
        self.graph_brightness_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")

        g_slider_row.addWidget(g_slider_title)
        g_slider_row.addWidget(self.graph_brightness_slider)
        g_slider_row.addWidget(self.graph_brightness_label)
        sliders_layout.addLayout(g_slider_row)

        # Graph Axes Brightness Slider (0% to 100%)
        ga_slider_row = QHBoxLayout()
        ga_slider_title = QLabel("Graph Axes Brightness:")
        ga_slider_title.setFixedWidth(160)
        ga_slider_title.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")
        self.graph_axis_brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.graph_axis_brightness_slider.setRange(0, 100)
        self.graph_axis_brightness_slider.setValue(50)
        self.graph_axis_brightness_slider.valueChanged.connect(self.on_graph_axis_brightness_changed)
        self.graph_axis_brightness_label = QLabel("50%")
        self.graph_axis_brightness_label.setFixedWidth(50)
        self.graph_axis_brightness_label.setStyleSheet("font-weight: bold; font-size: 11px; color: #ffffff;")

        ga_slider_row.addWidget(ga_slider_title)
        ga_slider_row.addWidget(self.graph_axis_brightness_slider)
        ga_slider_row.addWidget(self.graph_axis_brightness_label)
        sliders_layout.addLayout(ga_slider_row)

        behavior_layout.addLayout(sliders_layout)

        # Divider
        divider2 = QFrame()
        divider2.setFrameShape(QFrame.Shape.HLine)
        divider2.setStyleSheet("background-color: rgba(255, 255, 255, 0.15); max-height: 1px;")
        behavior_layout.addWidget(divider2)

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
        behavior_layout.addLayout(actions_layout)

        content_layout.addWidget(self.behavior_card)

        # 4. LIVE INTERACTIVE THEME PREVIEW PANEL
        self.preview_panel = ThemePreviewWidget(self.theme_mgr)
        content_layout.addWidget(self.preview_panel)

        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        self.update_card_styles()

    def populate_theme_dropdown(self):
        """Discovers presets and user themes and populates dropdown."""
        self._block_signals = True
        self.theme_dropdown.blockSignals(True)
        self.theme_dropdown.clear()

        # Always add Custom Theme* at index 0
        self.theme_dropdown.addItem("Custom Theme*", userData="Custom Theme")
        self.theme_dropdown.insertSeparator(1)

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

        # Match current active theme name using findData
        current_name = self.theme_mgr.active_theme_name
        idx = self.theme_dropdown.findData(current_name)
        if idx >= 0:
            self.theme_dropdown.setCurrentIndex(idx)
        else:
            self.theme_dropdown.setCurrentIndex(0)

        self.theme_dropdown.blockSignals(False)
        self._block_signals = False

    def _mark_custom_theme_active(self):
        """Sets active dropdown selection to Custom Theme* when staging tokens are edited."""
        if not self._block_signals:
            self.theme_dropdown.blockSignals(True)
            self.theme_dropdown.setCurrentIndex(0)
            self.theme_dropdown.blockSignals(False)

    def on_theme_selected(self, item_text: str):
        """Triggered when user selects a theme from the dropdown."""
        if self._block_signals or not item_text:
            return

        current_index = self.theme_dropdown.currentIndex()
        theme_name = self.theme_dropdown.itemData(current_index)
        if theme_name and theme_name != "Custom Theme":
            self.theme_mgr.apply_theme_by_name(theme_name)

    @Slot(dict)
    def on_theme_changed(self, tokens: dict):
        """Callback invoked when staging tokens, sources, or brightness are modified."""
        self.refresh_ui_from_theme(tokens)
        self.update_card_styles()

    def refresh_ui_from_theme(self, tokens: dict):
        """Updates color swatches, hex labels, source combos, and brightness sliders."""
        self._block_signals = True

        # Base Colors Display
        for token_key in ["window_bg", "accent_1", "accent_2", "text"]:
            hex_str = self.theme_mgr.base_colors.get(token_key, tokens.get(token_key, "#FFFFFFFF"))
            color = self.theme_mgr.get_color(token_key)

            swatch = self.preview_swatches.get(token_key)
            if swatch:
                rgba_str = color_to_rgba_str(color)
                swatch.setStyleSheet(f"background-color: {rgba_str}; border: 1.5px solid #ffffff; border-radius: 4px;")

            lbl = self.hex_labels.get(token_key)
            if lbl:
                lbl.setText(hex_str)

        # Source Combos
        btn_src = self.theme_mgr.sources.get("button_color_source", "accent_1")
        wbg_src = self.theme_mgr.sources.get("widget_bg_source", "window_bg")
        out_src = self.theme_mgr.sources.get("outline_source", "accent_1")
        ga_src = self.theme_mgr.sources.get("graph_axis_source", "accent_1")

        self.btn_src_combo.blockSignals(True)
        btn_idx = self.btn_src_combo.findData(btn_src)
        if btn_idx >= 0:
            self.btn_src_combo.setCurrentIndex(btn_idx)
        self.btn_src_combo.blockSignals(False)

        self.wbg_src_combo.blockSignals(True)
        wbg_idx = self.wbg_src_combo.findData(wbg_src)
        if wbg_idx >= 0:
            self.wbg_src_combo.setCurrentIndex(wbg_idx)
        self.wbg_src_combo.blockSignals(False)

        self.out_src_combo.blockSignals(True)
        out_idx = self.out_src_combo.findData(out_src)
        if out_idx >= 0:
            self.out_src_combo.setCurrentIndex(out_idx)
        self.out_src_combo.blockSignals(False)

        self.ga_src_combo.blockSignals(True)
        ga_idx = self.ga_src_combo.findData(ga_src)
        if ga_idx >= 0:
            self.ga_src_combo.setCurrentIndex(ga_idx)
        self.ga_src_combo.blockSignals(False)

        # Brightness Sliders
        w_val = self.theme_mgr.brightness.get("widget_brightness", 0)
        g_val = self.theme_mgr.brightness.get("graph_brightness", 0)
        ga_val = self.theme_mgr.brightness.get("graph_axis_brightness", 50)

        self.widget_brightness_slider.blockSignals(True)
        self.widget_brightness_slider.setValue(w_val)
        self.widget_brightness_slider.blockSignals(False)
        self.widget_brightness_label.setText(f"{w_val}%")

        self.graph_brightness_slider.blockSignals(True)
        self.graph_brightness_slider.setValue(g_val)
        self.graph_brightness_slider.blockSignals(False)
        self.graph_brightness_label.setText(f"{g_val}%")

        self.graph_axis_brightness_slider.blockSignals(True)
        self.graph_axis_brightness_slider.setValue(ga_val)
        self.graph_axis_brightness_slider.blockSignals(False)
        self.graph_axis_brightness_label.setText(f"{ga_val}%")

        self._block_signals = False

    def on_sources_changed(self):
        """Triggered when any behavior source selector combo box changes."""
        if self._block_signals:
            return

        btn_val = self.btn_src_combo.currentData()
        wbg_val = self.wbg_src_combo.currentData()
        out_val = self.out_src_combo.currentData()
        ga_val = self.ga_src_combo.currentData()

        if btn_val:
            self.theme_mgr.set_source("button_color_source", btn_val)
        if wbg_val:
            self.theme_mgr.set_source("widget_bg_source", wbg_val)
        if out_val:
            self.theme_mgr.set_source("outline_source", out_val)
        if ga_val:
            self.theme_mgr.set_source("graph_axis_source", ga_val)

        self._mark_custom_theme_active()

    def on_widget_brightness_changed(self, value: int):
        """Triggered when widget brightness slider moves."""
        self.widget_brightness_label.setText(f"{value}%")
        if not self._block_signals:
            self.theme_mgr.set_brightness("widget_brightness", value)
            self._mark_custom_theme_active()

    def on_graph_brightness_changed(self, value: int):
        """Triggered when graph brightness slider moves."""
        self.graph_brightness_label.setText(f"{value}%")
        if not self._block_signals:
            self.theme_mgr.set_brightness("graph_brightness", value)
            self._mark_custom_theme_active()

    def on_graph_axis_brightness_changed(self, value: int):
        """Triggered when graph axes brightness slider moves (0% to 100%)."""
        self.graph_axis_brightness_label.setText(f"{value}%")
        if not self._block_signals:
            self.theme_mgr.set_brightness("graph_axis_brightness", value)
            self._mark_custom_theme_active()

    def update_card_styles(self):
        """Applies dynamic QSS tokens to cards."""
        window_bg = self.theme_mgr.get_color("window_bg")
        widget_bg = self.theme_mgr.get_color("widget_bg")
        outline = self.theme_mgr.get_color("outline")
        btn_bg = self.theme_mgr.get_color("button_bg")

        bg_glass = color_to_rgba_str(widget_bg, alpha_override=0.85)
        border_glass = color_to_rgba_str(outline, alpha_override=0.35)
        btn_bg_str = color_to_rgba_str(btn_bg, alpha_override=0.80)

        style = f"""
        QFrame#controls_card, QFrame#preset_card, QFrame#behavior_card {{
            background-color: {bg_glass};
            border: 1.5px solid {border_glass};
            border-radius: 12px;
        }}

        QPushButton {{
            background-color: {btn_bg_str};
            border: 1px solid {border_glass};
            color: #ffffff;
            border-radius: 6px;
            padding: 6px 12px;
            font-weight: bold;
        }}

        QPushButton:hover {{
            background-color: {color_to_rgba_str(btn_bg, alpha_override=0.95)};
            border: 1px solid #ffffff;
        }}

        QPushButton:pressed {{
            background-color: {color_to_rgba_str(btn_bg, alpha_override=0.60)};
        }}
        """
        if self.controls_card.styleSheet() != style:
            self.controls_card.setStyleSheet(style)
            self.preset_card.setStyleSheet(style)
            self.behavior_card.setStyleSheet(style)

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
            self._mark_custom_theme_active()

    def apply_app_wide(self):
        """Applies current draft colors across all application tabs."""
        self.theme_mgr.commit_staging_theme()
        QMessageBox.information(self, "Theme Applied", "Draft theme colors applied across all application tabs.")

    def discard_edits(self):
        """Reverts draft edits back to active saved theme."""
        self.theme_mgr.discard_staging_theme()
        self.populate_theme_dropdown()

    def _prompt_for_new_theme_name(self, default_text: str = "") -> Optional[str]:
        """
        Prompts user for a new custom theme name.
        Enforces collision checks:
        - Blocks overwriting pre-built system presets with a warning modal.
        - Asks confirmation modal before overwriting an existing user custom theme.
        """
        from PySide6.QtWidgets import QInputDialog

        current_prompt = default_text
        while True:
            name, ok = QInputDialog.getText(
                self, "Save Custom Theme", "Enter a name for this custom theme:", text=current_prompt
            )
            if not ok or not name.strip():
                return None

            clean_name = name.strip()
            exists, is_preset, path = self.theme_mgr.theme_exists(clean_name)

            if exists:
                if is_preset:
                    QMessageBox.warning(
                        self, "Preset Protection",
                        f"A pre-built system preset named '{clean_name}' already exists and cannot be overwritten.\n"
                        "Please choose a different custom theme name."
                    )
                    current_prompt = clean_name
                    continue
                else:
                    confirm = QMessageBox.question(
                        self, "Overwrite Custom Theme",
                        f"A custom theme named '{clean_name}' already exists.\nDo you want to overwrite it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                        QMessageBox.StandardButton.No
                    )
                    if confirm == QMessageBox.StandardButton.Yes:
                        return clean_name
                    else:
                        current_prompt = clean_name
                        continue
            else:
                return clean_name

    def save_theme_dialog(self):
        """Saves current draft theme with preset protection and overwrite choice modals."""
        current_index = self.theme_dropdown.currentIndex()
        current_name = self.theme_dropdown.itemData(current_index)
        available = self.theme_mgr.get_available_themes()

        if not current_name or current_name == "Custom Theme" or current_name not in available or available[current_name]["is_preset"]:
            target_name = self._prompt_for_new_theme_name()
            if target_name:
                if self.theme_mgr.save_user_theme(target_name):
                    self.populate_theme_dropdown()
                    QMessageBox.information(self, "Theme Saved", f"Custom theme '{target_name}' saved and applied app-wide.")
                else:
                    QMessageBox.warning(self, "Save Failed", "Could not save custom theme.")
        else:
            msg = QMessageBox(self)
            msg.setWindowTitle("Save Custom Theme")
            msg.setText(f"You are saving changes while custom theme '{current_name}' is selected.")
            msg.setInformativeText("Would you like to overwrite the current custom theme or save as a new theme?")
            btn_overwrite = msg.addButton(f"Overwrite '{current_name}'", QMessageBox.ButtonRole.AcceptRole)
            btn_save_new = msg.addButton("Save as New Theme...", QMessageBox.ButtonRole.ActionRole)
            btn_cancel = msg.addButton(QMessageBox.StandardButton.Cancel)

            msg.exec()
            clicked = msg.clickedButton()

            if clicked == btn_overwrite:
                if self.theme_mgr.save_user_theme(current_name):
                    self.populate_theme_dropdown()
                    QMessageBox.information(self, "Theme Overwritten", f"Theme '{current_name}' updated and applied app-wide.")
                else:
                    QMessageBox.warning(self, "Save Failed", "Could not update custom theme.")
            elif clicked == btn_save_new:
                target_name = self._prompt_for_new_theme_name(default_text=f"{current_name} (Copy)")
                if target_name:
                    if self.theme_mgr.save_user_theme(target_name):
                        self.populate_theme_dropdown()
                        QMessageBox.information(self, "Theme Saved", f"Custom theme '{target_name}' saved and applied app-wide.")
                    else:
                        QMessageBox.warning(self, "Save Failed", "Could not save custom theme.")

    def rename_theme_dialog(self):
        """Prompts user to rename the currently selected custom theme."""
        current_index = self.theme_dropdown.currentIndex()
        current_name = self.theme_dropdown.itemData(current_index)
        available = self.theme_mgr.get_available_themes()

        if not current_name or current_name == "Custom Theme" or current_name not in available or available[current_name]["is_preset"]:
            QMessageBox.warning(self, "Protected Theme", "Pre-built system presets cannot be renamed. Please save as a new theme first.")
            return

        target_name = self._prompt_for_new_theme_name(default_text=current_name)
        if target_name and target_name != current_name:
            success = self.theme_mgr.rename_user_theme(current_name, target_name)
            if success:
                self.populate_theme_dropdown()
                QMessageBox.information(self, "Theme Renamed", f"Theme renamed to '{target_name}'.")
            else:
                QMessageBox.warning(self, "Rename Failed", "Could not rename selected theme.")

    def copy_theme_dialog(self):
        """Prompts user to duplicate the currently selected theme."""
        current_index = self.theme_dropdown.currentIndex()
        current_name = self.theme_dropdown.itemData(current_index) or "Theme"
        default_copy_name = f"{current_name} (Copy)"

        target_name = self._prompt_for_new_theme_name(default_text=default_copy_name)
        if target_name:
            success = self.theme_mgr.copy_theme(current_name, target_name)
            if success:
                self.populate_theme_dropdown()
                QMessageBox.information(self, "Theme Copied", f"Theme duplicated as '{target_name}'.")
            else:
                QMessageBox.warning(self, "Copy Failed", "Could not copy selected theme.")

    def delete_theme_dialog(self):
        """Prompts confirmation to delete currently selected custom theme."""
        current_index = self.theme_dropdown.currentIndex()
        current_name = self.theme_dropdown.itemData(current_index)
        available = self.theme_mgr.get_available_themes()

        if not current_name or current_name == "Custom Theme" or current_name not in available or available[current_name]["is_preset"]:
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
                self.populate_theme_dropdown()
                QMessageBox.information(self, "Theme Deleted", f"Custom theme '{current_name}' deleted.")
            else:
                QMessageBox.warning(self, "Delete Failed", "Could not delete selected theme.")

    def import_theme_dialog(self):
        """Opens QFileDialog to select JSON theme file for import."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Import Theme JSON", "", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            success = self.theme_mgr.import_theme_json(file_path)
            if success:
                self.populate_theme_dropdown()
                QMessageBox.information(self, "Theme Imported", "Theme configuration was successfully applied.")
            else:
                QMessageBox.warning(self, "Import Failed", "Could not import the selected theme file.")

    def export_theme_dialog(self):
        """Opens QFileDialog to save current theme tokens, sources, and sliders to JSON file."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Theme JSON", "custom_theme.json", "JSON Files (*.json);;All Files (*)"
        )
        if file_path:
            success = self.theme_mgr.export_theme_json(file_path)
            if success:
                QMessageBox.information(self, "Theme Exported", f"Theme saved to:\n{file_path}")
            else:
                QMessageBox.warning(self, "Export Failed", "Could not export the theme file.")

    def invert_accents(self):
        """Swaps Accent #1 and Accent #2 base colors and recalculates theme."""
        acc1 = self.theme_mgr.get_color("accent_1")
        acc2 = self.theme_mgr.get_color("accent_2")
        acc1_hex = color_to_hex8(acc1)
        acc2_hex = color_to_hex8(acc2)
        
        self.theme_mgr.set_token("accent_1", acc2_hex)
        self.theme_mgr.set_token("accent_2", acc1_hex)
        self.sync_controls_from_theme_mgr()
        self._mark_custom_theme_active()

    def reset_default_theme(self):
        """Restores factory default theme configuration."""
        confirm = QMessageBox.question(
            self, "Reset Theme",
            "Are you sure you want to restore the default theme colors and behavior settings?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.theme_mgr.reset_defaults()
            self.populate_theme_dropdown()
