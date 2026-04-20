"""Abstract protocols for agent interfaces."""

from typing import Any, Protocol


class PrincipalPort(Protocol):
    """Contract for the principal/reasoning agent."""

    def analyze(
        self,
        query: str,
        context: str | None,
        history: list[dict[str, str]] | None,
    ) -> dict[str, Any]: ...

    def generate_local_fallback(self, query: str, context: str | None) -> str: ...

    def is_available(self) -> bool: ...


class ExecutorPort(Protocol):
    """Contract for the executor/validation agent."""

    def validate(self, code: str, context: str) -> dict[str, Any]: ...

    def is_available(self) -> bool: ...
