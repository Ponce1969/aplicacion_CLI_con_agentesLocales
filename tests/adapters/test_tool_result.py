"""Tests for ToolResult Pydantic contract."""

import json

import pytest
from pydantic import ValidationError

from adapters.opencode.base import ToolResult


class TestToolResultContract:
    def test_success_result(self) -> None:
        result: ToolResult[dict[str, object]] = ToolResult(
            success=True,
            data={"response": "hello", "code_blocks": []},
            metadata={"model": "test"},
        )
        assert result.success is True
        assert result.data == {"response": "hello", "code_blocks": []}
        assert result.error is None
        assert result.metadata == {"model": "test"}

    def test_error_result(self) -> None:
        result: ToolResult[None] = ToolResult(success=False, error="Connection failed")
        assert result.success is False
        assert result.error == "Connection failed"
        assert result.data is None
        assert result.metadata == {}

    def test_to_json_produces_valid_json(self) -> None:
        result: ToolResult[dict[str, int]] = ToolResult(success=True, data={"x": 1})
        output = result.to_json()
        parsed = json.loads(output)
        assert parsed["success"] is True
        assert parsed["data"] == {"x": 1}

    def test_rejects_extra_fields(self) -> None:
        with pytest.raises(ValidationError):
            ToolResult(success=True, unknown_field="bad")  # type: ignore[call-arg]

    def test_strips_whitespace_from_strings(self) -> None:
        result: ToolResult[None] = ToolResult(success=False, error="  error  ")
        assert result.error == "error"

    def test_default_metadata_is_empty_dict(self) -> None:
        result: ToolResult[None] = ToolResult(success=True)
        assert result.metadata == {}

    def test_generic_data_preserves_type(self) -> None:
        result: ToolResult[dict[str, int]] = ToolResult(
            success=True,
            data={"count": 42},
        )
        assert result.data is not None
        assert result.data["count"] == 42
