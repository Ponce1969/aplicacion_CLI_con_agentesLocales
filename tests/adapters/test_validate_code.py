"""Tests for ValidateCodeTool adapter."""

from unittest.mock import MagicMock, patch

from adapters.opencode.validate_code import ValidateCodeTool


class TestValidateCodeTool:
    @patch("adapters.opencode.validate_code.Orchestrator")
    def test_returns_structured_result(self, mock_orch_cls: MagicMock) -> None:
        mock_orch = MagicMock()
        mock_orch.run_agent.return_value = {
            "is_valid": True,
            "feedback": "Código Correcto",
            "suggestions": [],
        }
        mock_orch_cls.return_value = mock_orch

        code = "def hello() -> str:\n    return 'hi'"
        with patch("adapters.opencode.validate_code.read_stdin", return_value=code):
            tool = ValidateCodeTool()
            result = tool.execute()

        assert result.success is True
        assert result.data is not None
        assert result.data["is_valid"] is True
        assert result.metadata["tool"] == "validate_code"
        assert result.metadata["model"] == "qwen-validator"
        assert result.metadata["code_length"] == len(code)
