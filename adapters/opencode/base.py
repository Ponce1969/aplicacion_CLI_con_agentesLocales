"""Base contract for all OpenCode tools with Pydantic v2 validation."""

from __future__ import annotations

import sys
import traceback
from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


def _setup_stdout_encoding() -> None:
    """Force UTF-8 on stdout to avoid Windows cp1252 encoding errors."""
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")


_setup_stdout_encoding()


class ToolResult(BaseModel, Generic[T]):  # noqa: UP046
    """Standard output contract for all OpenCode tools."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    success: bool = Field(
        ...,
        description="Indicates if the tool executed successfully",
    )
    data: T | None = Field(
        default=None,
        description="Payload returned by the tool (if success=True)",
    )
    error: str | None = Field(
        default=None,
        description="Error message (if success=False)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Execution metadata (model used, iterations, timing, etc)",
    )

    def to_json(self) -> str:
        return self.model_dump_json(indent=2)


class BaseTool(ABC):
    """Base class for all OpenCode tools. Enforces structured execution."""

    def run(self) -> None:
        """Entry point for CLI execution. Handles exceptions and prints JSON."""
        try:
            result = self.execute()
            if not isinstance(result, ToolResult):
                raise TypeError("execute() must return a ToolResult instance")
        except Exception as e:
            result = ToolResult(
                success=False,
                error=str(e),
                metadata={
                    "exception_type": type(e).__name__,
                    "traceback": traceback.format_exc(),
                },
            )

        print(result.to_json(), flush=True)

        if not result.success:
            sys.exit(1)

    @abstractmethod
    def execute(self) -> ToolResult[Any]:
        """Core logic of the tool. Must return a ToolResult."""


def read_stdin() -> str:
    """Read input from stdin. Raises ValueError if empty."""
    data = sys.stdin.read().strip()
    if not data:
        raise ValueError("No input received from stdin")
    return data
