"""Tool: Generator-Validator pipeline with controlled retry loop.

Usage:
    echo "Create a hexagonal service" | python adapters/opencode/generate_and_fix.py [max_iterations]
"""

import sys
from typing import Any

from adapters.opencode.base import BaseTool, ToolResult, read_stdin
from application.services.pipeline_service import PipelineService
from core.orchestrator import Orchestrator


class GenerateAndFixTool(BaseTool):
    """
    Pipeline: generate code → validate → fix → validate → ... (max N iterations)

    Models:
      - Generator: qwen-orchestrator (qwen3.5:9b)
      - Validator: qwen-validator (qwen2.5-coder:7b)
    """

    def __init__(self, max_iterations: int = 3) -> None:
        self.max_iterations = max_iterations

    def execute(self) -> ToolResult[dict[str, Any]]:
        prompt = read_stdin()

        orchestrator = Orchestrator()
        service = PipelineService(orchestrator)
        result = service.generate_and_fix(
            prompt=prompt,
            max_iterations=self.max_iterations,
        )

        return ToolResult(
            success=result["success"],
            data=result,
            metadata={
                "tool": "generate_and_fix",
                "generator_model": "qwen-orchestrator",
                "validator_model": "qwen-validator",
                "max_iterations": self.max_iterations,
                "prompt": prompt,
            },
        )


def main() -> None:
    max_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 3
    GenerateAndFixTool(max_iterations).run()


if __name__ == "__main__":
    main()
