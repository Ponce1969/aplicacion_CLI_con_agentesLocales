"""Lightweight metrics collector for tool execution."""

import time
from collections import defaultdict
from typing import Any


class MetricsCollector:
    """In-memory metrics with counters and timing histograms."""

    def __init__(self) -> None:
        self._counters: dict[str, int] = defaultdict(int)
        self._timings: dict[str, list[float]] = defaultdict(list)

    def increment(self, key: str, value: int = 1) -> None:
        self._counters[key] += value

    def record_time(self, key: str, duration: float) -> None:
        self._timings[key].append(duration)

    def timing(self, key: str) -> "_TimingContext":
        """Context manager to record duration of a block."""
        return _TimingContext(self, key)

    def summary(self) -> dict[str, Any]:
        return {
            "counters": dict(self._counters),
            "avg_timings": {
                k: round(sum(v) / len(v), 4) for k, v in self._timings.items() if v
            },
        }

    def reset(self) -> None:
        self._counters.clear()
        self._timings.clear()


class _TimingContext:
    def __init__(self, collector: MetricsCollector, key: str) -> None:
        self._collector = collector
        self._key = key
        self._start = 0.0

    def __enter__(self) -> "_TimingContext":
        self._start = time.perf_counter()
        return self

    def __exit__(self, *args: object) -> None:
        duration = time.perf_counter() - self._start
        self._collector.record_time(self._key, duration)
