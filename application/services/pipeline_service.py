"""Generator-Validator pipeline service with accumulated feedback loop."""

from typing import Any

from application.observability.logger import StructuredLogger
from application.observability.metrics import MetricsCollector
from application.task_types import TaskType
from core.orchestrator import Orchestrator


class PipelineService:
    """
    Pipeline: generate code → validate → fix → validate → ... (max N iterations)

    All orchestration goes through the single Orchestrator.run_agent() entry point.
    No duplication of agent calls.
    """

    def __init__(self, orchestrator: Orchestrator) -> None:
        self.orchestrator = orchestrator
        self.logger = StructuredLogger("pipeline")
        self.metrics = MetricsCollector()

    def generate_and_fix(
        self,
        prompt: str,
        max_iterations: int = 3,
    ) -> dict[str, Any]:
        self.logger.log(
            "pipeline_start",
            prompt_length=len(prompt),
            max_iterations=max_iterations,
        )

        with self.metrics.timing("pipeline_total"):
            feedback_history: list[str] = []
            current_code = ""
            last_response = ""

            for iteration in range(1, max_iterations + 1):
                with self.metrics.timing("iteration"):
                    if iteration == 1:
                        gen_result = self.orchestrator.run_agent(
                            TaskType.GENERATE, prompt
                        )
                    else:
                        fix_prompt = self._build_fix_prompt(
                            original_prompt=prompt,
                            current_code=current_code,
                            feedback_history=feedback_history,
                        )
                        gen_result = self.orchestrator.run_agent(
                            TaskType.GENERATE, fix_prompt
                        )

                    current_code = self._extract_main_code(gen_result["response"])
                    last_response = gen_result["response"]

                    with self.metrics.timing("validation"):
                        val_result = self.orchestrator.run_agent(
                            TaskType.VALIDATE, current_code
                        )

                self.metrics.increment("iterations_total")

                if val_result["is_valid"]:
                    duration = self.metrics.summary()["avg_timings"].get(
                        "pipeline_total", 0
                    )
                    self.logger.log(
                        "pipeline_success",
                        iterations=iteration,
                        duration=duration,
                    )
                    return {
                        "success": True,
                        "response": last_response,
                        "code": current_code,
                        "iterations": iteration,
                        "feedback_history": feedback_history,
                        "validation": val_result,
                        "metrics": self.metrics.summary(),
                    }

                feedback_history.append(val_result["feedback"])
                self.logger.log(
                    "validation_failed",
                    iteration=iteration,
                    feedback_preview=val_result["feedback"][:100],
                )

        duration = self.metrics.summary()["avg_timings"].get("pipeline_total", 0)
        self.logger.log(
            "pipeline_exhausted",
            iterations=max_iterations,
            duration=duration,
        )

        return {
            "success": False,
            "response": last_response,
            "code": current_code,
            "iterations": max_iterations,
            "feedback_history": feedback_history,
            "validation": val_result,
            "metrics": self.metrics.summary(),
        }

    @staticmethod
    def _extract_main_code(text: str) -> str:
        parts = text.split("```")
        for i in range(1, len(parts), 2):
            lines = parts[i].split("\n", 1)
            code = lines[1] if len(lines) > 1 else ""
            if code.strip():
                return code.strip()
        return text

    @staticmethod
    def _build_fix_prompt(
        original_prompt: str,
        current_code: str,
        feedback_history: list[str],
    ) -> str:
        joined_feedback = "\n---\n".join(
            f"Feedback #{i + 1}:\n{fb}" for i, fb in enumerate(feedback_history)
        )
        return (
            f"Original request: {original_prompt}\n\n"
            f"Your previous code:\n```python\n{current_code}\n```\n\n"
            f"ALL CODE REVIEW FEEDBACK (address EVERY point):\n{joined_feedback}\n\n"
            f"Return ONLY the corrected code in a single code block."
        )
