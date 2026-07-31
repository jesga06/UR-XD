"""
Event-Driven Personality Quote Engine (quote_engine.py)
Manages personality quotes loaded from src/.loading_quotes.json, handles event-driven
quote triggers ('boot', 'connect', 'profile_change'), low-frequency idle rotation,
logging via logger.quote, and log export sanitation.
"""

import os
import json
import random
import logging
from typing import Optional, List, Dict, Any

from PySide6.QtCore import QObject, QTimer, Signal

logger = logging.getLogger("quote_engine")


class QuoteEngine(QObject):
    """
    Event-driven personality quote engine for PySide6 UI.
    Emits quote_updated signal and logs quotes under [QUOTE] severity tag.
    """
    quote_updated = Signal(str)

    def __init__(self, theme_manager=None, parent=None):
        super().__init__(parent)
        self.theme_mgr = theme_manager
        self._quotes: List[Dict[str, str]] = self._load_quotes()
        self._last_quote: str = ""

        # Low-frequency idle timer (7.5 minutes = 450,000 ms)
        self._idle_timer = QTimer(self)
        self._idle_timer.setInterval(450000)
        self._idle_timer.timeout.connect(self._on_idle_timeout)

    def _load_quotes(self) -> List[Dict[str, str]]:
        """
        Loads personality quotes from src/.loading_quotes.json.
        Returns a list of dicts with 'quote' and 'author' keys.
        """
        quotes_path = os.path.abspath(
            os.path.join(os.path.dirname(__file__), "..", "..", ".loading_quotes.json")
        )
        if os.path.exists(quotes_path):
            try:
                with open(quotes_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, dict) and "quotes" in data:
                        raw_list = data["quotes"]
                    elif isinstance(data, list):
                        raw_list = data
                    else:
                        raw_list = []

                    valid = []
                    for item in raw_list:
                        if isinstance(item, dict) and "quote" in item:
                            valid.append({
                                "quote": str(item.get("quote", "")).strip(),
                                "author": str(item.get("author", "unknown")).strip()
                            })
                    if valid:
                        return valid
            except Exception as e:
                logger.warning(f"Failed to load quotes from {quotes_path}: {e}")

        # Fallback default quotes
        return [
            {"quote": "DInput insisted the triggers were digital. My stubbornness disagreed.", "author": "the developer"},
            {"quote": "Human did the reverse engineering. AI did the repetitive engineering.", "author": "chatgpt"},
            {"quote": "One human. One AI. Too much feature creep.", "author": "chatgpt"},
            {"quote": "Works on my controller.", "author": "happy user"}
        ]

    def get_random_quote(self, formatted: bool = True) -> str:
        """
        Returns a randomly chosen quote from the loaded database.
        If formatted is True, returns '"Quote Text"' or '"Quote Text" - Author'.
        """
        if not self._quotes:
            return "UR-XD Input System Active"

        item = random.choice(self._quotes)
        quote_text = item.get("quote", "")
        author = item.get("author", "")

        if not formatted:
            return quote_text

        if author and author.lower() != "unknown":
            formatted_str = f'"{quote_text}" - {author}'
        else:
            formatted_str = f'"{quote_text}"'

        self._last_quote = formatted_str
        return formatted_str

    def trigger_event_quote(self, event_type: str) -> str:
        """
        Fetches, logs, and emits a quote for event ('boot', 'connect', 'profile_change').
        """
        formatted_quote = self.get_random_quote(formatted=True)

        # Log quote under reserved [QUOTE] category
        try:
            if hasattr(logger, "quote"):
                logger.quote(f"[{event_type.upper()}] {formatted_quote}")
            else:
                logger.info(f"[QUOTE] [{event_type.upper()}] {formatted_quote}")
        except Exception:
            pass

        # Emit quote to UI subscribers
        self.quote_updated.emit(formatted_quote)
        return formatted_quote

    def start_idle_timer(self) -> None:
        """Starts the low-frequency idle quote rotation timer."""
        if not self._idle_timer.isActive():
            self._idle_timer.start()

    def stop_idle_timer(self) -> None:
        """Stops the low-frequency idle quote rotation timer."""
        if self._idle_timer.isActive():
            self._idle_timer.stop()

    def _on_idle_timeout(self) -> None:
        """Periodic timeout handler triggered every 7.5 minutes during idle."""
        self.trigger_event_quote("idle_rotation")

    @staticmethod
    def filter_sanitized_logs(raw_log_text: str) -> str:
        """
        Strips all [QUOTE] tagged lines from log text prior to developer packaging.
        """
        if not raw_log_text:
            return ""
        lines = raw_log_text.splitlines()
        sanitized = [line for line in lines if "[QUOTE]" not in line]
        return "\n".join(sanitized)
