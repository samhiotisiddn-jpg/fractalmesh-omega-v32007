from __future__ import annotations

import math


class AnomalyDetector:
    def __init__(self) -> None:
        self._series: dict[str, list[float]] = {}

    def record(self, value: float, series: str) -> None:
        self._series.setdefault(series, []).append(value)

    def get_stats(self, series: str) -> dict[str, float | int]:
        values = self._series.get(series, [])
        if not values:
            return {"mean": 0.0, "std": 0.0, "count": 0}
        mean = sum(values) / len(values)
        variance = sum((value - mean) ** 2 for value in values) / len(values)
        return {"mean": mean, "std": math.sqrt(variance), "count": len(values)}

    def is_anomalous(self, value: float, series: str, z_threshold: float = 3.0) -> bool:
        stats = self.get_stats(series)
        if int(stats["count"]) < 2 or float(stats["std"]) == 0.0:
            return False
        z_score = abs((value - float(stats["mean"])) / float(stats["std"]))
        return z_score >= z_threshold
