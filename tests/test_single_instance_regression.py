import sys
import os
import unittest
import socket

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from single_instance import ensure_single_instance, PORT_GUI

class TestSingleInstanceRegression(unittest.TestCase):
    """
    Regression tests verifying that ensure_single_instance prevents duplicate
    processes from binding to the same port on Windows.
    """

    def test_single_instance_binding_and_rejection(self):
        test_port = 48199
        # First binding should succeed
        s1 = ensure_single_instance("TEST_APP_1", test_port)
        self.assertIsNotNone(s1)

        # Second binding attempt should fail and exit with SystemExit(0)
        with self.assertRaises(SystemExit) as cm:
            ensure_single_instance("TEST_APP_2", test_port)
        self.assertEqual(cm.exception.code, 0)

        # Cleanup test socket
        s1.close()

if __name__ == "__main__":
    unittest.main()
