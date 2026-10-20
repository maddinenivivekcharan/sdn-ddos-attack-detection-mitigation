import json
import tempfile
from pathlib import Path
import unittest
from controller.config import load_config

class ConfigTests(unittest.TestCase):
    def invalid(self, key, value):
        config = load_config()
        config[key] = value
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "config.json"
            path.write_text(json.dumps(config), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)

    def test_defaults(self):
        self.assertEqual(load_config()["threshold_pps"], 5)

    def test_nonpositive(self):
        for key in ["poll_seconds", "threshold_pps", "consecutive_samples", "block_seconds"]:
            with self.subTest(key=key):
                self.invalid(key, 0)

    def test_types(self):
        for value in [True, "5", None, float("nan"), float("inf")]:
            with self.subTest(value=value):
                self.invalid("threshold_pps", value)

    def test_integers(self):
        self.invalid("consecutive_samples", 1.5)
        self.invalid("block_seconds", 2.5)

    def test_bounds(self):
        self.invalid("block_seconds", 61)
        self.invalid("poll_seconds", 11)

    def test_scope(self):
        self.invalid("server_ip", "192.0.2.1")
        self.invalid("client_ips", ["192.0.2.2"])

    def test_unknown(self):
        self.invalid("unexpected", 1)

    def test_missing(self):
        with self.assertRaises(FileNotFoundError):
            load_config("does-not-exist.json")

    def test_malformed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.json"
            path.write_text("{", encoding="utf-8")
            with self.assertRaises(json.JSONDecodeError):
                load_config(path)
