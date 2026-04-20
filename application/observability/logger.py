"""Structured logging for the application layer."""

import json
import logging
import sys
from datetime import UTC, datetime


class StructuredLogger:
    """JSON-structured logger. Writes to stderr to avoid polluting tool stdout."""

    def __init__(self, name: str = "agente") -> None:
        self._logger = logging.getLogger(name)
        if not self._logger.handlers:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(logging.Formatter("%(message)s"))
            self._logger.addHandler(handler)
            self._logger.setLevel(logging.INFO)

    def log(self, event: str, **kwargs: object) -> None:
        payload = {
            "timestamp": datetime.now(UTC).isoformat(),
            "event": event,
            **kwargs,
        }
        self._logger.info(json.dumps(payload, default=str))
