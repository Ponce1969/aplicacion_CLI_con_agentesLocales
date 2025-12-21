"""Cliente para RAG remoto vía Gateway Interno."""

from typing import Any

import httpx

from config import RAG_API_KEY, RAG_BASE_URL, RAG_TIMEOUT
from core.exceptions import (
    RAGConnectionError,
    RAGException,
    RAGPartialResponse,
    RAGSessionNotFound,
    map_http_status_to_exception,
)


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
    ) -> str:
        """
        Consulta al endpoint /api/internal/llm-gateway.

        Args:
            question: Pregunta del usuario
            mode: 'auto', 'rag', o 'kimi'
            session_id: ID de sesión (0 para nueva sesión temporal)

        Returns:
            Respuesta del servidor

        Raises:
            RAGUnavailable: Proveedor IA no disponible (503)
            RAGTimeout: Timeout externo (504)
            RAGUpstreamError: Error upstream (502)
            RAGRateLimited: Rate limit alcanzado (429)
            RAGBlocked: Guardian bloqueó la consulta (403)
            RAGAuthError: Autenticación inválida (401)
            RAGInvalidRequest: Request inválido (400/422)
            RAGSessionNotFound: Sesión no encontrada (422)
            RAGNotFound: Endpoint no existe (404)
            RAGInternalError: Error interno API (500)
            RAGConnectionError: Error de red/conexión
            RAGPartialResponse: Respuesta parcial (206)
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

            # Éxito (200)
            if response.status_code == 200:
                data = response.json()
                answer = data.get("answer")

                # Detectar respuestas placeholder (cache corrupto)
                # Comportamiento actual: devolvía None
                # Nuevo: lanza RAGPartialResponse para que orchestrator decida
                if isinstance(answer, str):
                    if "Voy a buscar información actualizada sobre esto" in answer:
                        raise RAGPartialResponse(
                            "RAG devolvió respuesta placeholder (cache corrupto)",
                            response=answer
                        )
                    return answer

                # answer no es string válido
                raise RAGPartialResponse("Respuesta sin contenido válido", response=None)

            # Caso especial: Error 500 con "Sesión no encontrada"
            # Comportamiento actual: retry automático con session_id=0
            # Nuevo: lanza RAGSessionNotFound para que orchestrator decida el retry
            if (
                response.status_code == 500
                and "Sesión" in response.text
                and "no encontrada" in response.text
                and session_id != 0
            ):
                raise RAGSessionNotFound(
                    "Sesión no encontrada en el servidor",
                    session_id=session_id
                )

            # Mapeo HTTP → Excepciones de dominio
            # Esto reemplaza el print + return None
            try:
                response_json = response.json()
            except Exception:
                response_json = None

            raise map_http_status_to_exception(
                response.status_code,
                response.text,
                response_json
            )

        except (RAGPartialResponse, RAGSessionNotFound):
            # Re-lanzar excepciones de dominio sin modificar
            raise

        except RAGException:
            # Re-lanzar TODAS las excepciones de dominio sin modificar
            raise

        except httpx.TimeoutException as e:
            # Timeout de red (no HTTP)
            raise RAGConnectionError(f"Timeout de conexión: {e}") from e

        except httpx.ConnectError as e:
            # API no alcanzable
            raise RAGConnectionError(f"No se pudo conectar a la API: {e}") from e

        except httpx.HTTPStatusError as e:
            # Error HTTP no manejado arriba
            raise RAGConnectionError(f"Error HTTP: {e}") from e

        except Exception as e:
            # Cualquier otro error de red/httpx
            raise RAGConnectionError(f"Error de conexión inesperado: {e}") from e

    def query_gemini_rag(self, question: str) -> str:
        """Consulta forzando modo RAG (Gemini + PDFs).

        Raises:
            Ver excepciones en query()
        """
        return self.query(question, mode="rag")

    def query_kimi(self, question: str) -> str:
        """Consulta forzando modo Kimi (Chat general).

        Raises:
            Ver excepciones en query()
        """
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

