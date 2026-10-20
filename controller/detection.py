"""Counter deltas identify a rate anomaly, never prove an attack."""
from dataclasses import dataclass
import math


@dataclass(frozen=True)
class Observation:
    pps: float
    suspicious: bool
    reason: str


class RateDetector:
    def __init__(self, threshold_pps: float, consecutive_samples: int):
        if isinstance(threshold_pps, bool) or not isinstance(threshold_pps, (int, float)) or not math.isfinite(threshold_pps) or threshold_pps <= 0:
            raise ValueError("threshold_pps must be positive and finite")
        if isinstance(consecutive_samples, bool) or not isinstance(consecutive_samples, int) or consecutive_samples < 1:
            raise ValueError("consecutive_samples must be a positive integer")
        self.threshold = threshold_pps
        self.required = consecutive_samples
        self.previous = {}
        self.streak = {}

    def reset(self, key):
        self.previous.pop(key, None)
        self.streak.pop(key, None)

    def observe(self, key, count: int, now: float) -> Observation:
        if isinstance(count, bool) or not isinstance(count, int) or count < 0:
            raise ValueError("packet counter must be a nonnegative integer")
        if not isinstance(now, (int, float)) or not math.isfinite(now):
            raise ValueError("time must be finite")
        previous = self.previous.get(key)
        if previous is not None and now <= previous[1]:
            raise ValueError("sample time must increase")
        self.previous[key] = (count, now)
        if previous is None or count < previous[0]:
            self.streak[key] = 0
            return Observation(0, False, "baseline established or counter reset")
        rate = (count - previous[0]) / (now - previous[1])
        self.streak[key] = self.streak.get(key, 0) + 1 if rate > self.threshold else 0
        suspicious = self.streak[key] >= self.required
        return Observation(rate, suspicious,
                           f"rate {rate:.2f} pps; threshold > {self.threshold}; "
                           f"consecutive elevated samples {self.streak[key]}/{self.required}; "
                           "rate anomaly alone does not prove DDoS")
