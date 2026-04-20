"""Tests for GenerateAndFixTool pipeline."""

from unittest.mock import MagicMock, patch

from adapters.opencode.generate_and_fix import GenerateAndFixTool
from application.services.pipeline_service import PipelineService


class TestGenerateAndFixTool:
    @patch("adapters.opencode.generate_and_fix.Orchestrator")
    def test_returns_structured_result(self, mock_orch_cls: MagicMock) -> None:
        mock_orch = MagicMock()
        mock_orch.run_agent.side_effect = [
            {
                "response": "```python\ndef hello() -> str:\n    return 'hi'\n```",
                "code_blocks": [],
                "intent": "local",
                "confidence": 0.9,
                "needs_validation": True,
                "patterns_detected": [],
            },
            {
                "is_valid": True,
                "feedback": "Código Correcto",
                "suggestions": [],
            },
        ]
        mock_orch_cls.return_value = mock_orch

        with patch(
            "adapters.opencode.generate_and_fix.read_stdin", return_value="Create hello"
        ):
            tool = GenerateAndFixTool(max_iterations=3)
            result = tool.execute()

        assert result.success is True
        assert result.data is not None
        assert result.data["success"] is True
        assert result.data["iterations"] == 1
        assert result.metadata["tool"] == "generate_and_fix"


class TestPipelineService:
    def _make_orchestrator_mock(
        self,
        generate_response: str = "```python\ndef hello() -> str:\n    return 'hi'\n```",
        validate_result: dict | None = None,
    ) -> MagicMock:
        if validate_result is None:
            validate_result = {
                "is_valid": True,
                "feedback": "Correcto",
                "suggestions": [],
            }

        mock_orch = MagicMock()
        mock_orch.run_agent.side_effect = [
            {
                "response": generate_response,
                "code_blocks": [],
                "intent": "local",
                "confidence": 0.9,
                "needs_validation": True,
                "patterns_detected": [],
            },
            validate_result,
        ]
        return mock_orch

    def test_passes_on_first_iteration(self) -> None:
        mock_orch = self._make_orchestrator_mock()
        service = PipelineService(mock_orch)
        result = service.generate_and_fix("Create hello", max_iterations=3)

        assert result["success"] is True
        assert result["iterations"] == 1
        assert result["code"] == "def hello() -> str:\n    return 'hi'"
        assert mock_orch.run_agent.call_count == 2

    def test_retries_on_validation_failure(self) -> None:
        mock_orch = MagicMock()
        call_count = [0]

        def side_effect(task_type: object, input_data: str) -> dict:
            if "generate" in str(task_type).lower():
                return {
                    "response": "```python\ndef hello(): return 'hi'\n```",
                    "code_blocks": [],
                    "intent": "local",
                    "confidence": 0.9,
                    "needs_validation": True,
                    "patterns_detected": [],
                }
            call_count[0] += 1
            if call_count[0] <= 2:
                return {
                    "is_valid": False,
                    "feedback": f"Missing type hints (attempt {call_count[0]})",
                    "suggestions": [],
                }
            return {"is_valid": True, "feedback": "Correcto", "suggestions": []}

        mock_orch.run_agent.side_effect = side_effect

        service = PipelineService(mock_orch)
        result = service.generate_and_fix("Create hello", max_iterations=3)

        assert result["success"] is True
        assert result["iterations"] == 3
        assert len(result["feedback_history"]) == 2

    def test_respects_max_iterations(self) -> None:
        mock_orch = MagicMock()
        mock_orch.run_agent.side_effect = [
            {
                "response": "```python\ndef hello(): return 'hi'\n```",
                "code_blocks": [],
                "intent": "local",
                "confidence": 0.9,
                "needs_validation": True,
                "patterns_detected": [],
            },
            {"is_valid": False, "feedback": "Broken 1", "suggestions": []},
            {
                "response": "```python\ndef hello(): return 'hi'\n```",
                "code_blocks": [],
                "intent": "local",
                "confidence": 0.9,
                "needs_validation": True,
                "patterns_detected": [],
            },
            {"is_valid": False, "feedback": "Still broken", "suggestions": []},
        ]

        service = PipelineService(mock_orch)
        result = service.generate_and_fix("Create hello", max_iterations=2)

        assert result["success"] is False
        assert result["iterations"] == 2
        assert len(result["feedback_history"]) == 2

    def test_accumulates_feedback_in_fix_prompt(self) -> None:
        mock_orch = MagicMock()
        prompts_seen: list[str] = []

        def side_effect(task_type: object, input_data: str) -> dict:
            if "generate" in str(task_type).lower():
                prompts_seen.append(input_data)
                return {
                    "response": "```python\ndef hello(): return 'hi'\n```",
                    "code_blocks": [],
                    "intent": "local",
                    "confidence": 0.9,
                    "needs_validation": True,
                    "patterns_detected": [],
                }
            return {
                "is_valid": False,
                "feedback": f"Feedback #{len(prompts_seen)}",
                "suggestions": [],
            }

        mock_orch.run_agent.side_effect = side_effect

        service = PipelineService(mock_orch)
        service.generate_and_fix("Create hello", max_iterations=3)

        assert len(prompts_seen) == 3
        assert "Feedback #1" in prompts_seen[1]
        assert "Feedback #1" in prompts_seen[2]
        assert "Feedback #2" in prompts_seen[2]
