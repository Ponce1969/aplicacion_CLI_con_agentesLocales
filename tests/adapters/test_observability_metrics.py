"""Tests for MetricsCollector."""

import time

from application.observability.metrics import MetricsCollector


class TestMetricsCollector:
    def test_increment_increases_counter(self) -> None:
        m = MetricsCollector()
        m.increment("calls")
        m.increment("calls")
        assert m.summary()["counters"]["calls"] == 2

    def test_increment_with_custom_value(self) -> None:
        m = MetricsCollector()
        m.increment("tokens", 500)
        assert m.summary()["counters"]["tokens"] == 500

    def test_record_time_stores_duration(self) -> None:
        m = MetricsCollector()
        m.record_time("latency", 0.5)
        m.record_time("latency", 1.5)
        assert m.summary()["avg_timings"]["latency"] == 1.0

    def test_timing_context_measures_duration(self) -> None:
        m = MetricsCollector()
        with m.timing("block"):
            time.sleep(0.05)
        timings = m.summary()["avg_timings"]
        assert "block" in timings
        assert timings["block"] >= 0.04

    def test_summary_returns_correct_structure(self) -> None:
        m = MetricsCollector()
        m.increment("a")
        m.record_time("b", 1.0)
        summary = m.summary()

        assert "counters" in summary
        assert "avg_timings" in summary
        assert summary["counters"]["a"] == 1
        assert summary["avg_timings"]["b"] == 1.0

    def test_reset_clears_all_data(self) -> None:
        m = MetricsCollector()
        m.increment("x")
        m.record_time("y", 1.0)
        m.reset()
        summary = m.summary()
        assert summary["counters"] == {}
        assert summary["avg_timings"] == {}

    def test_empty_summary_has_empty_collections(self) -> None:
        m = MetricsCollector()
        summary = m.summary()
        assert summary["counters"] == {}
        assert summary["avg_timings"] == {}
