"""Validate code service — delegates to orchestrator for single-pass validation."""

from typing import Any

from application.observability.logger import StructuredLogger
from application.observability.metrics import MetricsCollector
from application.task_types import TaskType
from core.orchestrator import Orchestrator


class ValidateService:
    """Validates code quality via the executor agent."""

    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator
        self.logger = StructuredLogger("validate")
        self.metrics = MetricsCollector()

    def validate(self, code: str) -> dict[str, Any]:
        self.logger.log("validate_start", code_length=len(code))

        with self.metrics.timing("validate_total"):
            result = self.orchestrator.run_agent(TaskType.VALIDATE, code)

        self.metrics.increment("validate_calls")
        self.metrics.increment("valid_code" if result["is_valid"] else "invalid_code")

        self.logger.log(
            "validate_complete",
            is_valid=result["is_valid"],
            suggestions=len(result.get("suggestions", [])),
            duration=self.metrics.summary()["avg_timings"].get("validate_total", 0),
        )

        result["metrics"] = self.metrics.summary()
        return result
