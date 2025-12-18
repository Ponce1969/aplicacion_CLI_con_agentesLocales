"""Agente Principal - llama3.1:8b para análisis y decisiones."""

from typing import Any

import httpx

from config import BACKEND_PATTERNS, OLLAMA_BASE_URL, OLLAMA_TIMEOUT, PRINCIPAL_MODEL


class PrincipalAgent:
    """Agente principal con llama3.1:8b para razonamiento y análisis."""

    def __init__(self) -> None:
        self.model = PRINCIPAL_MODEL
        self.client = httpx.Client(
            base_url=OLLAMA_BASE_URL, timeout=OLLAMA_TIMEOUT
        )

    def analyze(self, query: str, context: str | None = None) -> dict[str, Any]:
        """
        Analiza la consulta y decide estrategia.

        Args:
            query: Consulta del usuario
            context: Contexto adicional (patrones aprendidos, etc.)

        Returns:
            Dict con análisis y respuesta
        """
        # Detectar patrones de backend
        detected_patterns = self._detect_backend_patterns(query)

        # Construir prompt enriquecido
        prompt = self._build_prompt(query, context, detected_patterns)

        # Generar respuesta
        response = self._generate(prompt)

        return {
            "response": response,
            "patterns_detected": detected_patterns,
            "needs_validation": self._needs_validation(response),
            "confidence": self._estimate_confidence(response),
        }

    def _detect_backend_patterns(self, query: str) -> list[str]:
        """Detecta patrones de backend en la consulta."""
        query_lower = query.lower()
        detected = []

        for pattern_name, keywords in BACKEND_PATTERNS.items():
            if any(keyword.lower() in query_lower for keyword in keywords):
                detected.append(pattern_name)

        return detected

    def _build_prompt(
        self,
        query: str,
        context: str | None,
        patterns: list[str],
    ) -> str:
        """Construye prompt optimizado y conciso."""
        parts = []

        # Solo agregar contexto si es relevante
        if patterns:
            parts.append(f"Backend: {', '.join(patterns[:2])}")

        if context:
            parts.append(f"Ref: {context[:200]}")

        # Instrucciones mínimas
        parts.append(
            "Python 3.12+, type hints, mypy strict.\n"
            f"Q: {query}"
        )

        return "\n".join(parts)

    def _generate(self, prompt: str) -> str:
        """Genera respuesta usando Ollama."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "top_p": 0.9,
                    "num_predict": 512,
                    "num_ctx": 2048,
                },
            }

            response = self.client.post("/api/generate", json=payload)
            response.raise_for_status()

            result = response.json()
            answer = result.get("response", "")
            return str(answer) if answer is not None else ""

        except Exception as e:
            return f"Error generando respuesta: {e}"

    def _needs_validation(self, response: str) -> bool:
        """Determina si la respuesta necesita validación del ejecutor."""
        code_indicators = ["```", "def ", "class ", "import ", "from "]
        return any(indicator in response for indicator in code_indicators)

    def _estimate_confidence(self, response: str) -> float:
        """Estima confianza en la respuesta (0.0 - 1.0)."""
        uncertainty_phrases = [
            "no estoy seguro",
            "podría ser",
            "tal vez",
            "no tengo información",
            "no sé",
        ]

        response_lower = response.lower()
        uncertainty_count = sum(
            1 for phrase in uncertainty_phrases if phrase in response_lower
        )

        if uncertainty_count > 0:
            return max(0.3, 1.0 - (uncertainty_count * 0.2))

        if len(response) < 50:
            return 0.5

        return 0.9

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
