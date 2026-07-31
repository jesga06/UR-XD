"""
Unit and Integration Tests for Phase 7: Logging System Overhaul & Flavor Quote Engine.
"""

import os
import sys
import tempfile
import logging
import unittest

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src")))
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from logger_setup import (
    setup_logger, setup_telemetry_logger, filter_sanitized_logs,
    sanitize_log_file, SUCCESS_LEVEL_NUM, QUOTE_LEVEL_NUM
)
from gui_v2.services.quote_engine import QuoteEngine


class TestPhase7LoggingQuoteEngine(unittest.TestCase):

    def test_custom_logging_levels_and_methods(self):
        logger = logging.getLogger("test_logger_levels")
        self.assertTrue(hasattr(logger, "success"))
        self.assertTrue(hasattr(logger, "quote"))
        self.assertEqual(logging.getLevelName(SUCCESS_LEVEL_NUM), "SUCCESS")
        self.assertEqual(logging.getLevelName(QUOTE_LEVEL_NUM), "QUOTE")

    def test_log_sanitation_filter(self):
        raw_log = (
            "2026-07-31 04:00:00 [INFO] [main] Connected to controller.\n"
            "2026-07-31 04:00:01 [QUOTE] [main] [BOOT] \"Feature creep is ambition...\" - dev\n"
            "2026-07-31 04:00:02 [SUCCESS] [main] Profile loaded successfully.\n"
            "2026-07-31 04:00:03 [WARN] [main] HID report descriptor malformed.\n"
        )
        sanitized = filter_sanitized_logs(raw_log)
        self.assertNotIn("[QUOTE]", sanitized)
        self.assertIn("[INFO]", sanitized)
        self.assertIn("[SUCCESS]", sanitized)
        self.assertIn("[WARN]", sanitized)

    def test_quote_engine_service(self):
        qe = QuoteEngine()
        quotes = qe._load_quotes()
        self.assertGreater(len(quotes), 0)

        quote = qe.get_random_quote(formatted=True)
        self.assertIsInstance(quote, str)
        self.assertGreater(len(quote), 0)

        event_quote = qe.trigger_event_quote("connect")
        self.assertIsInstance(event_quote, str)

    def test_package_report_sanitation(self):
        from diagnostics.package_report import package_issue_report
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_zip = os.path.join(tmp_dir, "test_report.zip")
            success = package_issue_report(output_zip=test_zip)
            self.assertTrue(success)
            self.assertTrue(os.path.exists(test_zip))


if __name__ == "__main__":
    unittest.main()
