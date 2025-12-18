"""Agente Ejecutor/Validador - qwen2.5:7b-instruct para validación y ejecución."""

from typing import Any

import httpx

from config import EXECUTOR_MODEL, OLLAMA_BASE_URL, OLLAMA_TIMEOUT


class ExecutorAgent:
    """Agente ejecutor con qwen2.5:7b-instruct para validación y testing."""

    def __init__(self) -> None:
        self.model = EXECUTOR_MODEL
        self.client = httpx.Client(
            base_url=OLLAMA_BASE_URL, timeout=OLLAMA_TIMEOUT
        )

    def validate(self, code: str, context: str = "") -> dict[str, Any]:
        """
        Valida código generado por el agente principal.

        Args:
            code: Código a validar
            context: Contexto adicional

        Returns:
            Dict con resultado de validación
        """
        prompt = self._build_validation_prompt(code, context)
        response = self._generate(prompt)

        return {
            "is_valid": self._check_validity(response),
            "feedback": response,
            "suggestions": self._extract_suggestions(response),
        }

    def _build_validation_prompt(self, code: str, context: str) -> str:
        """Construye prompt optimizado para validación."""
        prompt = f"Valida Python 3.12+, type hints, mypy strict:\n```python\n{code}\n```\n"

        if context:
            prompt += f"Ctx: {context[:100]}\n"

        prompt += "Respuesta: OK o errores."
        return prompt

    def _generate(self, prompt: str) -> str:
        """Genera respuesta usando Ollama."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "num_predict": 1024,
                    "num_ctx": 2048,
                },
            }

            response = self.client.post("/api/generate", json=payload)
            response.raise_for_status()

            result = response.json()
            answer = result.get("response", "")
            return str(answer) if answer is not None else ""

        except Exception as e:
            return f"Error en validación: {e}"

    def _check_validity(self, response: str) -> bool:
        """Verifica si la validación fue positiva."""
        positive_indicators = [
            "correcto",
            "válido",
            "bien",
            "apropiado",
            "cumple",
        ]
        negative_indicators = [
            "error",
            "incorrecto",
            "falta",
            "problema",
            "no cumple",
        ]

        response_lower = response.lower()
        positive_count = sum(
            1 for ind in positive_indicators if ind in response_lower
        )
        negative_count = sum(
            1 for ind in negative_indicators if ind in response_lower
        )

        return positive_count > negative_count

    def _extract_suggestions(self, response: str) -> list[str]:
        """Extrae sugerencias de mejora."""
        suggestions = []
        lines = response.split("\n")

        for line in lines:
            line_lower = line.lower().strip()
            if any(
                keyword in line_lower
                for keyword in ["sugerencia", "mejorar", "considerar", "agregar"]
            ):
                suggestions.append(line.strip())

        return suggestions[:5]

    def is_available(self) -> bool:
        """Verifica si Ollama está disponible."""
        try:
            response = self.client.get("/api/tags")
            return response.status_code == 200
        except Exception:
            return False

    def close(self) -> None:
        """Cierra el cliente."""
        self.client.close()

    def __del__(self) -> None:
        """Limpieza automática."""
        if hasattr(self, "client"):
            self.client.close()
