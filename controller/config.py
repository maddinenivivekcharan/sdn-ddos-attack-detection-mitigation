"""Dependency-free, strictly validated lab settings (JSON instead of YAML)."""
import json
import math
from pathlib import Path

DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "config" / "lab_config.json"


def load_config(path=DEFAULT_CONFIG):
    with open(path, encoding="utf-8") as stream:
        config = json.load(stream)
    required = {"poll_seconds", "threshold_pps", "consecutive_samples", "block_seconds",
                "server_ip", "client_ips"}
    if set(config) != required:
        raise ValueError("Configuration must contain exactly: " + ", ".join(sorted(required)))
    for key in ("poll_seconds", "threshold_pps", "consecutive_samples", "block_seconds"):
        value = config[key]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(key + " must be a finite number")
        if value <= 0:
            raise ValueError(key + " must be positive")
    for key in ("consecutive_samples", "block_seconds"):
        if not isinstance(config[key], int):
            raise ValueError(key + " must be an integer")
    if not 1 <= config["poll_seconds"] <= 10:
        raise ValueError("poll_seconds must be between 1 and 10")
    if not 1 <= config["block_seconds"] <= 60:
        raise ValueError("block_seconds must be between 1 and 60")
    if config["server_ip"] != "10.0.0.3" or config["client_ips"] != ["10.0.0.1", "10.0.0.2"]:
        raise ValueError("This isolated topology requires the documented fixed host addresses")
    return config
