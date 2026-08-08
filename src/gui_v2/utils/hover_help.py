"""
Hover Help & Markdown Help Viewers for PySide6 UI (gui_v2).
Provides styled hover tooltips and a dedicated markdown help modal window.
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QTextBrowser, QPushButton, QLabel, QWidget
from PySide6.QtCore import Qt


class MarkdownHelpDialog(QDialog):
    """
    Modal window for displaying rich Markdown documentation guides.
    """
    def __init__(self, title: str, markdown_text: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.resize(600, 500)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header Title
        lbl_title = QLabel(title, self)
        lbl_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ffffff;")
        layout.addWidget(lbl_title)

        # Markdown Text Browser
        self.browser = QTextBrowser(self)
        self.browser.setMarkdown(markdown_text)
        self.browser.setStyleSheet("""
            QTextBrowser {
                background-color: rgba(20, 15, 30, 0.9);
                border: 1px solid rgba(168, 85, 247, 0.35);
                border-radius: 8px;
                color: #e0e0e0;
                padding: 12px;
                font-size: 13px;
            }
        """)
        layout.addWidget(self.browser)

        # Bottom Close Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_close = QPushButton("Close", self)
        btn_close.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_close.setStyleSheet("""
            QPushButton {
                background-color: rgba(168, 85, 247, 0.2);
                border: 1px solid rgba(168, 85, 247, 0.5);
                border-radius: 6px;
                color: #ffffff;
                padding: 6px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(168, 85, 247, 0.4);
            }
        """)
        btn_close.clicked.connect(self.accept)
        btn_layout.addWidget(btn_close)
        layout.addLayout(btn_layout)


def attach_tooltip(widget: QWidget, description: str, title: str = "") -> None:
    """
    Attaches a formatted rich-text tooltip to a PySide6 control widget.
    """
    if not widget:
        return

    header_html = f"<b>{title}</b><br/>" if title else ""
    tooltip_html = f"""
    <div style="background-color: #0c0914; color: #ffffff; border: 1px solid #a855f7; padding: 6px; border-radius: 4px;">
        {header_html}
        <span style="color: #cccccc; font-size: 11px;">{description}</span>
    </div>
    """
    widget.setToolTip(tooltip_html)
