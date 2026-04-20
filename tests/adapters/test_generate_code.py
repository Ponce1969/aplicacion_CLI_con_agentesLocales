"""Tests for GenerateCodeTool adapter."""

from unittest.mock import MagicMock, patch

from adapters.opencode.generate_code import GenerateCodeTool


class TestGenerateCodeTool:
    @patch("adapters.opencode.generate_code.Orchestrator")
    def test_returns_structured_result(self, mock_orch_cls: MagicMock) -> None:
        mock_orch = MagicMock()
        mock_orch.run_agent.return_value = {
            "response": "Here is the code:\n```python\ndef hello() -> str:\n    return 'hi'\n```",
            "code_blocks": [
                {"language": "python", "code": "def hello() -> str:\n    return 'hi'"}
            ],
            "intent": "local",
            "confidence": 0.9,
            "needs_validation": True,
            "patterns_detected": [],
        }
        mock_orch_cls.return_value = mock_orch

        with patch(
            "adapters.opencode.generate_code.read_stdin",
            return_value="Create hello function",
        ):
            tool = GenerateCodeTool()
            result = tool.execute()

        assert result.success is True
        assert result.data is not None
        assert result.data["intent"] == "local"
        assert len(result.data["code_blocks"]) == 1
        assert result.metadata["tool"] == "generate_code"
        assert result.metadata["model"] == "qwen-orchestrator"

    @patch("adapters.opencode.generate_code.Orchestrator")
    def test_delegates_to_orchestrator(self, mock_orch_cls: MagicMock) -> None:
        mock_orch = MagicMock()
        mock_orch.run_agent.return_value = {
            "response": "test",
            "code_blocks": [],
            "intent": "local",
            "confidence": 0.9,
            "needs_validation": False,
            "patterns_detected": [],
        }
        mock_orch_cls.return_value = mock_orch

        with patch(
            "adapters.opencode.generate_code.read_stdin", return_value="test prompt"
        ):
            tool = GenerateCodeTool()
            tool.execute()

        mock_orch.run_agent.assert_called_once()
