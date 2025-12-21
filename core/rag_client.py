"""Cliente para RAG remoto vía Gateway Interno."""

from typing import Any

import httpx
from rich.console import Console

from config import RAG_API_KEY, RAG_BASE_URL, RAG_TIMEOUT

console = Console()


class RAGClient:
    """Cliente simplificado para el Gateway LLM."""

    def __init__(self, base_url: str = RAG_BASE_URL, api_key: str = RAG_API_KEY) -> None:
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(
            base_url=self.base_url,
            timeout=RAG_TIMEOUT,
            headers={"X-API-Key": api_key} if api_key else None
        )

    def query(
        self, question: str, mode: str = "auto", session_id: int = 0
    ) -> str | None:
        """
        Consulta al endpoint /api/internal/llm-gateway.

        Args:
            question: Pregunta del usuario
            mode: 'auto', 'rag', o 'kimi'
            session_id: ID de sesión (0 para nueva sesión temporal)

        Returns:
            Respuesta del servidor o None si falla
        """
        try:
            payload = {
                "query": question,
                "mode": mode,
                "session_id": session_id
            }

            response = self.client.post(
                "/api/internal/llm-gateway",
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                # El servidor devuelve: { "answer": "...", "mode_used": "...", ... }
                answer = data.get("answer")

                # Filtrar respuestas placeholder que indican fallo en el servidor
                if isinstance(answer, str):
                    if "Voy a buscar información actualizada sobre esto" in answer:
                        console.print("[yellow]⚠️ RAG devolvió respuesta placeholder (cache corrupto).[/yellow]")
                        return None
                    return answer
                return None

            # Manejo específico para error de sesión no encontrada (500)
            if (
                response.status_code == 500
                and "Sesión" in response.text
                and "no encontrada" in response.text
                and session_id != 0
            ):
                console.print("[yellow]⚠️ Sesión no encontrada, reintentando con nueva sesión...[/yellow]")
                return self.query(question, mode, session_id=0)

            console.print(f"[yellow]⚠️ Error del servidor ({response.status_code}): {response.text}[/yellow]")
            return None

        except Exception as e:
            console.print(f"[red]❌ Error de conexión RAG: {e}[/red]")
            return None

    def query_gemini_rag(self, question: str) -> str | None:
        """Consulta forzando modo RAG (Gemini + PDFs)."""
        return self.query(question, mode="rag")

    def query_kimi(self, question: str) -> str | None:
        """Consulta forzando modo Kimi (Chat general)."""
        return self.query(question, mode="kimi")

    def is_available(self) -> bool:
        """Verifica si el gateway está disponible."""
        try:
            response = self.client.get("/api/internal/llm-gateway/status")
            return response.status_code == 200
        except Exception:
            return False

    def get_status(self) -> dict[str, Any]:
        """Obtiene estadísticas del gateway."""
        try:
            response = self.client.get("/api/internal/llm-gateway/status")
            if response.status_code == 200:
                result = response.json()
                if isinstance(result, dict):
                    return result
            return {"status": "error", "code": response.status_code}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def close(self) -> None:
        """Cierra la conexión."""
        self.client.close()

    def __del__(self) -> None:
        """Limpieza automática."""
        if hasattr(self, "client"):
            self.client.close()

