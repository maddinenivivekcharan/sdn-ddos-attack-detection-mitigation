import unittest
from controller.detection import RateDetector

class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.d = RateDetector(5, 2)

    def test_baseline(self):
        self.assertFalse(self.d.observe("a", 999, 1).suspicious)

    def test_normal(self):
        self.d.observe("a", 0, 0)
        self.assertEqual(self.d.observe("a", 2, 2).pps, 1)

    def test_exact_threshold(self):
        self.d.observe("a", 0, 0)
        self.assertFalse(self.d.observe("a", 10, 2).suspicious)
        self.assertEqual(self.d.streak["a"], 0)

    def test_suspicious(self):
        self.d.observe("a", 0, 0)
        self.assertFalse(self.d.observe("a", 20, 2).suspicious)
        self.assertTrue(self.d.observe("a", 40, 4).suspicious)

    def test_streak_reset(self):
        for count, now in [(0, 0), (20, 2), (20, 4), (40, 6)]:
            result = self.d.observe("a", count, now)
        self.assertFalse(result.suspicious)

    def test_client_isolation(self):
        for count, now in [(0, 0), (20, 2), (40, 4)]:
            self.d.observe("a", count, now)
        self.assertFalse(self.d.observe("b", 0, 4).suspicious)

    def test_counter_reset(self):
        self.d.observe("a", 100, 0)
        self.assertEqual(self.d.observe("a", 0, 2).pps, 0)

    def test_recovery(self):
        self.d.observe("a", 0, 0)
        self.d.reset("a")
        self.assertFalse(self.d.observe("a", 100, 20).suspicious)

    def test_invalid_counter(self):
        for value in [-1, 1.5, True]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.d.observe("a", value, 0)

    def test_invalid_time(self):
        self.d.observe("a", 0, 1)
        for value in [1, 0, float("nan"), float("inf")]:
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.d.observe("a", 1, value)

    def test_invalid_settings(self):
        for threshold, windows in [(0, 2), (float("inf"), 2), (5, 0), (5, 1.5), (True, 2)]:
            with self.subTest(threshold=threshold, windows=windows), self.assertRaises(ValueError):
                RateDetector(threshold, windows)
