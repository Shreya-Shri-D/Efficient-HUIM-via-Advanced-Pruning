from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from typing import Dict


@dataclass
class RunMetrics:
    runtime_seconds: float
    candidates: int
    visited_transactions: int
    upper_bound_calculations: int
    hui_count: int


class Timer:
    def __enter__(self) -> "Timer":
        self.start = time.perf_counter()
        self.end = None
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.end = time.perf_counter()

    @property
    def elapsed(self) -> float:
        if self.end is None:
            return time.perf_counter() - self.start
        return self.end - self.start


def write_metrics_json(path: str, metrics: RunMetrics) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(asdict(metrics), f, indent=2)
