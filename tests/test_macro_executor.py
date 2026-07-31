import unittest
from unittest.mock import MagicMock
import time
import os
import json

from src.macro_executor import MacroExecutor


class TestMacroExecutor(unittest.TestCase):
    def setUp(self):
        self.mock_mapper = MagicMock()
        self.executor = MacroExecutor(self.mock_mapper)

    def test_run_dict_macro_with_string_steps(self):
        macro_data = {
            "mode": "one_shot",
            "steps": [
                "keyboard:f+u+c+k",
                "wait:10ms"
            ]
        }
        self.executor.macros = {"test": macro_data}
        self.executor.execute_or_toggle("test")
        
        # Wait for background thread execution
        if self.executor.worker_thread:
            self.executor.worker_thread.join(timeout=1.0)

        self.mock_mapper._press.assert_called_with("keyboard:f+u+c+k")
        self.mock_mapper._release.assert_called_with("keyboard:f+u+c+k")

    def test_run_dict_macro_with_explicit_press_release(self):
        macro_data = {
            "mode": "one_shot",
            "steps": [
                "press:keyboard:a",
                "wait:5ms",
                "release:keyboard:a"
            ]
        }
        self.executor.macros = {"test_explicit": macro_data}
        self.executor.execute_or_toggle("test_explicit")

        if self.executor.worker_thread:
            self.executor.worker_thread.join(timeout=1.0)

        self.mock_mapper._press.assert_called_with("keyboard:a")
        self.mock_mapper._release.assert_called_with("keyboard:a")

    def test_run_dict_steps(self):
        macro_data = {
            "mode": "one_shot",
            "steps": [
                {"action": "press", "key": "keyboard:x"},
                {"action": "wait", "ms": 5},
                {"action": "release", "key": "keyboard:x"}
            ]
        }
        self.executor.macros = {"test_dict_steps": macro_data}
        self.executor.execute_or_toggle("test_dict_steps")

        if self.executor.worker_thread:
            self.executor.worker_thread.join(timeout=1.0)

        self.mock_mapper._press.assert_called_with("keyboard:x")
        self.mock_mapper._release.assert_called_with("keyboard:x")

    def test_legacy_list_macro(self):
        macro_data = [
            "press:a",
            "wait:5ms",
            "release:a"
        ]
        self.executor.macros = {"test_legacy": macro_data}
        self.executor.execute_or_toggle("test_legacy")

        if self.executor.worker_thread:
            self.executor.worker_thread.join(timeout=1.0)

        self.mock_mapper._press.assert_called_with("a")
        self.mock_mapper._release.assert_called_with("a")


if __name__ == "__main__":
    unittest.main()
