import unittest
import time
from src.haptic_engine import parse_haptic_profile, HapticEngine

class DummyVirtualPad:
    def __init__(self):
        self.last_vibration = (0, 0)
        self.calls = []

    def set_vibration(self, lm, rm):
        self.last_vibration = (lm, rm)
        self.calls.append((lm, rm))

class TestHapticEngine(unittest.TestCase):
    def test_parse_keyword_syntax(self):
        profile = "RM[30% @ 0ms, dur=1500ms], LM[100% @ 1500ms, dur=250ms]"
        events = parse_haptic_profile(profile)
        self.assertEqual(len(events), 2)
        
        self.assertEqual(events[0]['motor'], 'RM')
        self.assertAlmostEqual(events[0]['intensity'], 0.30)
        self.assertAlmostEqual(events[0]['start_s'], 0.0)
        self.assertAlmostEqual(events[0]['duration_s'], 1.5)

        self.assertEqual(events[1]['motor'], 'LM')
        self.assertAlmostEqual(events[1]['intensity'], 1.0)
        self.assertAlmostEqual(events[1]['start_s'], 1.5)
        self.assertAlmostEqual(events[1]['duration_s'], 0.25)

    def test_parse_both_keyword(self):
        profile = "BOTH[50% @ 100ms, dur=200ms]"
        events = parse_haptic_profile(profile)
        self.assertEqual(len(events), 2)
        motors = {e['motor'] for e in events}
        self.assertEqual(motors, {'LM', 'RM'})

    def test_haptic_engine_execution(self):
        pad = DummyVirtualPad()
        engine = HapticEngine(pad)
        
        # Short profile for fast test
        profile = "RM[50% @ 0ms, dur=50ms]"
        played = engine.play_profile(profile)
        self.assertTrue(played)
        self.assertTrue(engine.is_hijacked)
        
        # Wait for thread completion
        time.sleep(0.12)
        self.assertFalse(engine.is_hijacked)
        self.assertEqual(pad.last_vibration, (0, 0))

if __name__ == '__main__':
    unittest.main()
