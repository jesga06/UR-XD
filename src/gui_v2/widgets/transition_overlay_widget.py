"""
Transition Overlay Widget (transition_overlay_widget.py)
Provides a smooth cross-fade transition overlay (250ms fade-in, 900ms hold, 250ms fade-out)
rendering a vector loading spinner, status badge, and contextual loading quote.
Integrated with QuoteEngine for event-driven personality quotes and ThemeManager.
"""

import os
import json
import random
from typing import Optional, List, Dict, Any

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGraphicsOpacityEffect, QFrame
from PySide6.QtGui import QPainter, QColor, QPen, QFont
from PySide6.QtCore import Qt, QTimer, Property, Signal, Slot, QPropertyAnimation, QEasingCurve, QRectF

from gui_v2.services.theme_manager import ThemeManager, color_to_rgba_str, color_to_hex6
from gui_v2.services.quote_engine import QuoteEngine


class SpinnerWidget(QWidget):
    """
    Vector loading spinner with smooth rotation animation.
    """
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFixedSize(54, 54)
        self._angle: float = 0.0
        self._color: QColor = QColor("#00f0ff")

        self._timer = QTimer(self)
        self._timer.setInterval(16)  # ~60 FPS
        self._timer.timeout.connect(self._rotate)

    def set_color(self, color: QColor) -> None:
        self._color = color
        self.update()

    def start(self) -> None:
        if not self._timer.isActive():
            self._timer.start()

    def stop(self) -> None:
        self._timer.stop()

    def _rotate(self) -> None:
        self._angle = (self._angle + 6.0) % 360.0
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        rect = QRectF(6, 6, 42, 42)
        # Background track
        pen_bg = QPen(QColor(self._color.red(), self._color.green(), self._color.blue(), 40), 4)
        painter.setPen(pen_bg)
        painter.drawEllipse(rect)

        # Active spinning arc
        pen_arc = QPen(self._color, 4)
        pen_arc.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_arc)
        start_angle = int(-self._angle * 16)
        span_angle = int(100 * 16)  # 100 degrees arc
        painter.drawArc(rect, start_angle, span_angle)
        painter.end()


class TransitionOverlayWidget(QWidget):
    """
    Color-interpolated canvas opacity cross-fade transition overlay widget.
    Fades in over 250ms, holds for 900ms, and fades out over 250ms.
    """
    transition_finished = Signal()

    def __init__(self, parent: Optional[QWidget] = None, quote_engine: Optional[QuoteEngine] = None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        if isinstance(parent, QuoteEngine):
            quote_engine = parent
            parent = None

        self.quote_engine = quote_engine or QuoteEngine(parent=self)
        self.quote_engine.quote_updated.connect(self._on_quote_updated)

        self.opacity_effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(0.0)

        self.anim = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.anim.setEasingCurve(QEasingCurve.Type.InOutCubic)

        self._hold_timer = QTimer(self)
        self._hold_timer.setSingleShot(True)
        self._hold_timer.timeout.connect(self._start_fade_out)

        self.setup_ui()
        self._setup_theme_sync()
        self.hide()

    def setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        self.card = QFrame(self)
        self.card.setObjectName("overlay_card")
        card_layout = QVBoxLayout(self.card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setContentsMargins(32, 28, 32, 28)
        card_layout.setSpacing(16)

        self.spinner = SpinnerWidget()
        card_layout.addWidget(self.spinner, alignment=Qt.AlignmentFlag.AlignCenter)

        self.badge = QLabel("CONNECTING")
        self.badge.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.badge.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        card_layout.addWidget(self.badge, alignment=Qt.AlignmentFlag.AlignCenter)

        self.quote_label = QLabel("Initializing controller connection...")
        self.quote_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.quote_label.setWordWrap(True)
        self.quote_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Normal))
        card_layout.addWidget(self.quote_label, alignment=Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(self.card, alignment=Qt.AlignmentFlag.AlignCenter)

    def _setup_theme_sync(self) -> None:
        try:
            tm = ThemeManager.get_instance()
            tm.theme_changed.connect(self.on_theme_changed)
            self.on_theme_changed(tm.tokens)
        except Exception:
            pass

    @Slot(str)
    def _on_quote_updated(self, quote_text: str) -> None:
        self.quote_label.setText(quote_text)

    @Slot(dict)
    def on_theme_changed(self, tokens: dict) -> None:
        try:
            tm = ThemeManager.get_instance()
            bg_color = tm.get_color("background")
            accent_1 = tm.get_color("accent_1")
            accent_2 = tm.get_color("accent_2")

            bg_glass = color_to_rgba_str(bg_color, alpha_override=0.92)
            border_glass = color_to_rgba_str(accent_1, alpha_override=0.4)

            self.setStyleSheet(f"background-color: {color_to_rgba_str(bg_color, alpha_override=0.75)};")
            self.card.setStyleSheet(f"""
                QFrame#overlay_card {{
                    background-color: {bg_glass};
                    border: 2px solid {border_glass};
                    border-radius: 16px;
                }}
            """)
            self.badge.setStyleSheet(f"""
                background-color: {color_to_rgba_str(accent_1, alpha_override=0.2)};
                color: {color_to_hex6(accent_1)};
                border: 1px solid {color_to_rgba_str(accent_1, alpha_override=0.5)};
                border-radius: 6px;
                padding: 4px 14px;
            """)
            self.quote_label.setStyleSheet(f"color: {color_to_hex6(accent_2)};")
            self.spinner.set_color(accent_1)
        except RuntimeError:
            pass

    def trigger_transition(self, status_text: str = "CONNECTING", custom_quote: Optional[str] = None, event_type: str = "connect") -> None:
        """
        Triggers full cross-fade animation sequence: 250ms fade-in, 900ms hold, 250ms fade-out.
        """
        self.badge.setText(status_text)
        if custom_quote:
            self.quote_label.setText(custom_quote)
        else:
            self.quote_engine.trigger_event_quote(event_type)

        self.spinner.start()
        self.show()
        self.raise_()

        # Fade in 250ms
        self.anim.stop()
        self.anim.setDuration(250)
        self.anim.setStartValue(self.opacity_effect.opacity())
        self.anim.setEndValue(1.0)
        
        try:
            self.anim.finished.disconnect(self._on_fade_in_finished)
        except Exception:
            pass
        try:
            self.anim.finished.disconnect(self._on_fade_out_finished)
        except Exception:
            pass

        self.anim.finished.connect(self._on_fade_in_finished)
        self.anim.start()

    def _on_fade_in_finished(self) -> None:
        # Hold 900ms
        self._hold_timer.start(900)

    def _start_fade_out(self) -> None:
        self.anim.stop()
        self.anim.setDuration(250)
        self.anim.setStartValue(1.0)
        self.anim.setEndValue(0.0)

        try:
            self.anim.finished.disconnect(self._on_fade_in_finished)
        except Exception:
            pass
        try:
            self.anim.finished.disconnect(self._on_fade_out_finished)
        except Exception:
            pass

        self.anim.finished.connect(self._on_fade_out_finished)
        self.anim.start()

    def _on_fade_out_finished(self) -> None:
        self.spinner.stop()
        self.hide()
        self.transition_finished.emit()
