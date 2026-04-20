"""Tool: Generate code using the principal agent (qwen3.5:9b).

Usage:
    echo "Create a FastAPI endpoint" | python adapters/opencode/generate_code.py
"""

from typing import Any

from adapters.opencode.base import BaseTool, ToolResult, read_stdin
from application.services.generate_service import GenerateService
from core.orchestrator import Orchestrator


class GenerateCodeTool(BaseTool):
    """Generates code or answers technical questions via stdin input."""

    def execute(self) -> ToolResult[dict[str, Any]]:
        prompt = read_stdin()

        orchestrator = Orchestrator()
        service = GenerateService(orchestrator)
        result = service.generate(prompt)

        return ToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "generate_code",
                "model": "qwen-orchestrator",
                "prompt": prompt,
            },
        )


if __name__ == "__main__":
    GenerateCodeTool().run()
