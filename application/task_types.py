"""Task types for the application layer."""

from enum import Enum


class TaskType(Enum):
    """Explicit task types for orchestrator dispatch."""

    GENERATE = "generate"
    VALIDATE = "validate"
    PROCESS = "process"
