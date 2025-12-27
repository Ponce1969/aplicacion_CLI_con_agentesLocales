"""Agente Principal - llama3.1:8b para análisis y decisiones."""

from typing import Any

import httpx

from config import (
    BACKEND_PATTERNS,
    KNOWLEDGE_BASE_SUMMARY,
    OLLAMA_BASE_URL,
    OLLAMA_TIMEOUT,
    PRINCIPAL_MODEL,
)


class PrincipalAgent:
    """Agente principal con llama3.1:8b para razonamiento y análisis."""

    def __init__(self) -> None:
        self.model = PRINCIPAL_MODEL
        self.client = httpx.Client(base_url=OLLAMA_BASE_URL, timeout=OLLAMA_TIMEOUT)
        self.last_eval_count = 0  # 🧬 MANIFOLD: Tokens reales de Ollama

    def analyze(
        self,
        query: str,
        context: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> dict[str, Any]:
        """
        Analiza la consulta y decide estrategia.

        Args:
            query: Consulta del usuario
            context: Contexto adicional (patrones aprendidos, etc.)
            history: Historial de la conversación
        """
        # Detectar patrones de backend
        detected_patterns = self._detect_backend_patterns(query)

        # Construir prompt enriquecido
        prompt = self._build_prompt(query, context, detected_patterns, history)

        # Generar respuesta
        response = self._generate(prompt)

        # Detectar intención explícita
        intent = "local"
        if "[[RAG]]" in response:
            intent = "rag"
            response = response.replace("[[RAG]]", "").strip()
        elif "[[WEB]]" in response:
            intent = "web"
            response = response.replace("[[WEB]]", "").strip()

        # Fallback: Detectar intenciones verbales si fallaron los tags
        if intent == "local":
            lower_resp = response.lower()
            if "necesito consultar la biblioteca" in lower_resp:
                intent = "rag"
            elif "buscaré información" in lower_resp or "buscar rumores" in lower_resp:
                intent = "web"

        return {
            "response": response,
            "patterns_detected": detected_patterns,
            "needs_validation": self._needs_validation(response),
            "confidence": self._estimate_confidence(response),
            "intent": intent,
            "eval_count": self.last_eval_count,  # 🧬 MANIFOLD: Token count real
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
        history: list[dict[str, str]] | None = None,
    ) -> str:
        """Construye prompt optimizado y conciso."""
        parts = []

        # 1. Rol y Estándares
        parts.append(
            "Eres un Asistente Senior de Desarrollo de Software (Llama 3.1). "
            "Especializado en: Python 3.12+, FastAPI, Arquitectura de Software, DevOps, Cloud (AWS/Azure/GCP). "
            "Estándares: Type Hints estrictos, Clean Code, Arquitectura Hexagonal."
        )

        # 2. Contexto de Biblioteca (RAG)
        parts.append(
            f"\nBIBLIOTECA DISPONIBLE (RAG):{KNOWLEDGE_BASE_SUMMARY}\n"
            "NOTA: Tienes acceso a estos libros mediante la herramienta [[RAG]]. "
            "AUNQUE SEPAS LA RESPUESTA, si el tema está cubierto por estos libros (FastAPI, PyQt6, Buenas Prácticas), "
            "PREFIERE SIEMPRE usar [[RAG]] para responder con autoridad y citas."
        )

        # 3. Contexto Técnico Detectado
        if patterns:
            parts.append(f"\nContexto Técnico Detectado: {', '.join(patterns)}")

        # 4. Contexto Aprendido (Memoria)
        if context:
            parts.append(f"\nMemoria Previa:\n{context[:300]}")

        # 5. Historial de Conversación
        if history:
            parts.append("\nHistorial de Conversación:")
            for msg in history:
                role = "User" if msg["role"] == "user" else "Assistant"
                parts.append(f"{role}: {msg['content']}")

        # 6. Instrucción Final
        parts.append(
            "\nREGLAS CRÍTICAS DE ROUTING:"
            "\n- NO respondas con texto si necesitas buscar. Usa SOLO las etiquetas."
            "\n- Noticias, clima, precios, 'novedades recientes' -> [[WEB]]"
            "\n- Libros técnicos, documentación específica, 'FastAPI', 'PyQt6' -> [[RAG]]"
            "\n- Arquitectura de software, infraestructura, AWS, DevOps, diseño de sistemas -> [[RAG]]"
            "\n- Lógica pura, Python básico, corrección de código -> Responde tú mismo."
            "\n\nEjemplos:"
            "\nQ: Novedades Python 3.14? -> [[WEB]]"
            "\nQ: Cómo usar Depends en FastAPI? -> [[RAG]]"
            "\nQ: Define arquitectura AWS con ECS Fargate? -> [[RAG]]"
            "\nQ: Ordena esta lista. -> [Tu respuesta]"
            f"\n\nQ: {query}"
        )

        return "\n".join(parts)

    def generate_local_fallback(self, query: str, context: str | None = None) -> str:
        """Genera una respuesta local cuando fallan las herramientas externas."""
        parts = []
        parts.append(
            "Eres un Asistente Senior de Python (Llama 3.1). "
            "Las herramientas externas (RAG/Web) han fallado o no están disponibles. "
            "Debes responder a la consulta del usuario utilizando SOLO tu conocimiento interno. "
            "NO uses etiquetas como [[RAG]] o [[WEB]]. "
            "Sé honesto si no conoces la respuesta, pero intenta ayudar con lo que sepas."
        )

        if context:
            parts.append(f"\nContexto previo:\n{context[:300]}")

        parts.append(f"\nQ: {query}")

        prompt = "\n".join(parts)
        return self._generate(prompt)

    def _generate(self, prompt: str) -> str:
        """Genera respuesta usando Ollama."""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,  # Más determinista para decisiones
                    "top_p": 0.9,
                    "num_predict": 1024,
                    "num_ctx": 4096,
                },
            }

            response = self.client.post("/api/generate", json=payload)
            response.raise_for_status()

            result = response.json()
            answer = result.get("response", "")

            # 🧬 MANIFOLD: Guardar eval_count para metabolismo preciso
            self.last_eval_count = result.get("eval_count", 0)

            return str(answer).strip() if answer is not None else ""

        except Exception as e:
            return f"Error generando respuesta: {e}"

    def _needs_validation(self, response: str) -> bool:
        """Determina si la respuesta necesita validación del ejecutor."""
        code_indicators = ["```", "def ", "class ", "import ", "from "]
        return any(indicator in response for indicator in code_indicators)

    def _estimate_confidence(self, response: str) -> float:
        """Estima confianza en la respuesta (0.0 - 1.0)."""
        # Si el modelo decidió usar herramientas externas, la confianza en su decisión es alta (para activar el flujo)
        # pero la confianza en el 'contenido local' es nula.
        if "[[RAG]]" in response or "[[WEB]]" in response:
            return 0.0  # Fuerza el uso de herramientas externas

        uncertainty_phrases = [
            "no estoy seguro",
            "podría ser",
            "tal vez",
            "no tengo información",
            "no sé",
            "no tengo información sobre",
            "mi última actualización",
            "no disponibilidad pública",
            "recomendaría consultar",
            "necesito consultar",
            "necesito buscar",
            "buscaré información",
            "fuentes actualizadas",
            "consultar documentación",
            "no puedo proporcionar",
            "no tengo acceso",
            "información no disponible",
        ]

        response_lower = response.lower()
        uncertainty_count = sum(
            1 for phrase in uncertainty_phrases if phrase in response_lower
        )

        if uncertainty_count > 0:
            # Baja confianza drásticamente si hay incertidumbre
            return max(0.1, 0.8 - (uncertainty_count * 0.3))

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
