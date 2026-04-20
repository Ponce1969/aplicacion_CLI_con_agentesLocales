"""Tests for StructuredLogger."""

import io
import json
import logging

from application.observability.logger import StructuredLogger


class TestStructuredLogger:
    def test_log_produces_valid_json_on_stderr(self) -> None:
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = StructuredLogger("test_log_json")
        logger._logger.handlers = []
        logger._logger.addHandler(handler)
        logger._logger.setLevel(logging.INFO)

        logger.log("test_event", key="value", count=42)

        output = stream.getvalue().strip()
        parsed = json.loads(output)

        assert parsed["event"] == "test_event"
        assert parsed["key"] == "value"
        assert parsed["count"] == 42
        assert "timestamp" in parsed

    def test_log_includes_timestamp(self) -> None:
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = StructuredLogger("test_timestamp")
        logger._logger.handlers = []
        logger._logger.addHandler(handler)
        logger._logger.setLevel(logging.INFO)

        logger.log("time_check")

        output = stream.getvalue().strip()
        parsed = json.loads(output)

        assert "timestamp" in parsed
        assert "T" in parsed["timestamp"]

    def test_log_handles_no_extra_kwargs(self) -> None:
        stream = io.StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(logging.Formatter("%(message)s"))

        logger = StructuredLogger("test_no_kwargs")
        logger._logger.handlers = []
        logger._logger.addHandler(handler)
        logger._logger.setLevel(logging.INFO)

        logger.log("minimal_event")

        output = stream.getvalue().strip()
        parsed = json.loads(output)

        assert parsed["event"] == "minimal_event"
        assert "timestamp" in parsed
