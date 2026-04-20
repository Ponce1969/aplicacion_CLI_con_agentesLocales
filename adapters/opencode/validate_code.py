"""Tool: Validate code using the executor agent (qwen2.5-coder:7b).

Usage:
    cat file.py | python adapters/opencode/validate_code.py
"""

from typing import Any

from adapters.opencode.base import BaseTool, ToolResult, read_stdin
from application.services.validate_service import ValidateService
from core.orchestrator import Orchestrator


class ValidateCodeTool(BaseTool):
    """Validates code quality via stdin input."""

    def execute(self) -> ToolResult[dict[str, Any]]:
        code = read_stdin()

        orchestrator = Orchestrator()
        service = ValidateService(orchestrator)
        result = service.validate(code)

        return ToolResult(
            success=True,
            data=result,
            metadata={
                "tool": "validate_code",
                "model": "qwen-validator",
                "code_length": len(code),
            },
        )


if __name__ == "__main__":
    ValidateCodeTool().run()
