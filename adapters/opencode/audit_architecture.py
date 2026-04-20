"""Tool: Analyze architecture of a codebase or file.

Usage:
    cat src/core/orchestrator.py | python adapters/opencode/audit_architecture.py
"""

from typing import Any

from adapters.opencode.base import BaseTool, ToolResult, read_stdin
from application.task_types import TaskType
from core.orchestrator import Orchestrator


class AuditArchitectureTool(BaseTool):
    """Analyzes code for architecture patterns, SOLID compliance, and design quality."""

    def execute(self) -> ToolResult[dict[str, Any]]:
        code = read_stdin()

        prompt = (
            "Analyze the following code for:\n"
            "1. Architecture pattern (hexagonal, layered, MVC, etc.)\n"
            "2. SOLID principles compliance\n"
            "3. Separation of concerns\n"
            "4. Testability\n"
            "5. Python 3.12+ modern syntax usage\n\n"
            f"Code:\n```python\n{code}\n```\n\n"
            "Return a structured analysis with specific findings and recommendations."
        )

        orchestrator = Orchestrator()
        analysis = orchestrator.run_agent(TaskType.GENERATE, prompt)

        return ToolResult(
            success=True,
            data={
                "analysis": analysis["response"],
                "confidence": analysis["confidence"],
            },
            metadata={
                "tool": "audit_architecture",
                "model": "qwen-orchestrator",
                "source_length": len(code),
            },
        )


if __name__ == "__main__":
    AuditArchitectureTool().run()
