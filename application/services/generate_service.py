"""Generate code service — delegates to orchestrator for single-pass generation."""

from typing import Any

from application.observability.logger import StructuredLogger
from application.observability.metrics import MetricsCollector
from application.task_types import TaskType
from core.orchestrator import Orchestrator


class GenerateService:
    """Generates code or answers technical questions via the principal agent."""

    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator
        self.logger = StructuredLogger("generate")
        self.metrics = MetricsCollector()

    def generate(self, prompt: str) -> dict[str, Any]:
        self.logger.log("generate_start", prompt_length=len(prompt))

        with self.metrics.timing("generate_total"):
            result = self.orchestrator.run_agent(TaskType.GENERATE, prompt)

        self.metrics.increment("generate_calls")
        self.logger.log(
            "generate_complete",
            intent=result.get("intent"),
            confidence=result.get("confidence"),
            code_blocks=len(result.get("code_blocks", [])),
            duration=self.metrics.summary()["avg_timings"].get("generate_total", 0),
        )

        result["metrics"] = self.metrics.summary()
        return result
