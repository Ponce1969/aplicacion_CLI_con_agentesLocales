"""Excepciones de dominio para el sistema de agentes.

Este módulo define el vocabulario de errores del sistema, siguiendo el contrato
API ↔ CLI documentado en docs/api-cli-contract.md.

Principio:
- La API describe el problema (lanza/devuelve estas excepciones vía HTTP)
- El CLI decide la acción (captura y maneja según estrategia)
"""

from typing import Any


class RAGException(Exception):  # noqa: N818
    """Excepción base para todos los errores relacionados con RAG.

    Nunca se lanza directamente, solo se usa para captura genérica.
    """

    def __init__(self, message: str, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


# ============================================================================
# 🟡 ERRORES RECUPERABLES (Retry/Fallback posible)
# ============================================================================


class RAGUnavailable(RAGException):
    """Proveedor de IA no disponible temporalmente (HTTP 503).

    Causa típica:
    - Gemini/Kimi/Brave están caídos
    - Circuit breaker abierto en la API
    - Mantenimiento programado

    Estrategia CLI:
    - Retry 1x con 2s de espera
    - Fallback a cache
    - Fallback a LLM local

    UX: "🔄 Servicio de conocimiento remoto no disponible. Usando conocimiento local."
    """

    pass


class RAGTimeout(RAGException):
    """Timeout al consultar proveedor externo (HTTP 504).

    Causa típica:
    - Gemini/Kimi tardaron más de lo esperado
    - Red lenta
    - Proveedor sobrecargado

    Estrategia CLI:
    - Retry 1x con 2s de espera
    - Fallback a cache
    - NO usar LLM local (puede ser temporal)

    UX: "⏱️ El servicio remoto tardó demasiado. Usando respuesta en caché."
    """

    pass


class RAGUpstreamError(RAGException):
    """Error en infraestructura upstream (HTTP 502).

    Causa típica:
    - Cloudflare Tunnel caído
    - Proxy/Gateway con problemas
    - Orange Pi sin conectividad

    Estrategia CLI:
    - Retry 2x con backoff (1s, 2s)
    - Si falla, abort (no cache, puede ser corrupto)

    UX: "🔌 Error de conexión con el servidor. Reintentando..."
    """

    pass


class RAGRateLimited(RAGException):
    """Rate limit alcanzado (HTTP 429).

    Causa típica:
    - Demasiadas consultas en poco tiempo
    - Límite de API de Gemini/Kimi

    Estrategia CLI:
    - Retry 3x con backoff exponencial (5s, 10s, 20s)
    - Respetar header Retry-After si existe
    - Si falla, abort

    UX: "⏳ Límite de consultas alcanzado. Reintentando en {seconds}s..."

    Attributes:
        retry_after: Segundos a esperar antes de reintentar (del header Retry-After)
    """

    def __init__(
        self, message: str = "Rate limit alcanzado", retry_after: int | None = None
    ) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class RAGRequestTimeout(RAGException):
    """Timeout del request HTTP (HTTP 408).

    Causa típica:
    - Request tardó más que el timeout configurado
    - Red muy lenta

    Estrategia CLI:
    - Retry 1x inmediato
    - Si falla, abort

    UX: "⏱️ La consulta tardó demasiado. Reintentando..."
    """

    pass


# ============================================================================
# 🔴 ERRORES DEFINITIVOS (NO retry, abort)
# ============================================================================


class RAGBlocked(RAGException):
    """Consulta bloqueada por Guardian (HTTP 403).

    Causa típica:
    - Contenido inapropiado detectado
    - Violación de políticas de uso
    - Intento de jailbreak

    Estrategia CLI:
    - NO reintentar (es definitivo)
    - Mostrar razón al usuario
    - Abort

    UX: "🛡️ La consulta fue bloqueada por el sistema de seguridad: {reason}"

    Attributes:
        reason: Razón del bloqueo (ej: "contenido_inapropiado")
    """

    def __init__(
        self, message: str = "Consulta bloqueada", reason: str = "unknown"
    ) -> None:
        super().__init__(message)
        self.reason = reason


class RAGAuthError(RAGException):
    """Error de autenticación (HTTP 401).

    Causa típica:
    - RAG_API_KEY inválida o expirada
    - Token no proporcionado
    - Credenciales incorrectas

    Estrategia CLI:
    - NO reintentar
    - Avisar al usuario que revise .env
    - Abort

    UX: "❌ Autenticación inválida. Verifica RAG_API_KEY en .env"
    """

    pass


class RAGInvalidRequest(RAGException):
    """Request malformado o inválido (HTTP 400/422).

    Causa típica:
    - JSON inválido
    - Parámetros faltantes
    - Tipos incorrectos
    - Sesión inválida (caso especial, ver RAGSessionNotFound)

    Estrategia CLI:
    - NO reintentar (es un bug del CLI)
    - Log detallado para debugging
    - Abort

    UX: "❌ Request inválido: {details}"
    """

    pass


class RAGSessionNotFound(RAGInvalidRequest):
    """Sesión no encontrada o expiró (HTTP 422 específico).

    Causa típica:
    - session_id no existe en la API
    - Sesión expiró
    - Base de datos de sesiones reiniciada

    Estrategia CLI:
    - Retry UNA VEZ con session_id=0 (nueva sesión)
    - Si falla de nuevo, abort

    UX: "⚠️ Sesión inválida. Creando nueva sesión..."

    Attributes:
        session_id: ID de la sesión que no se encontró
    """

    def __init__(
        self, message: str = "Sesión no encontrada", session_id: int | None = None
    ) -> None:
        super().__init__(message)
        self.session_id = session_id


class RAGNotFound(RAGException):
    """Endpoint no existe (HTTP 404).

    Causa típica:
    - Bug en el CLI (URL incorrecta)
    - Versión de API incompatible

    Estrategia CLI:
    - NO reintentar (es un bug)
    - Log para debugging
    - Abort

    UX: "❌ Endpoint no encontrado (bug del CLI)"
    """

    pass


class RAGInternalError(RAGException):
    """Error interno de la API (HTTP 500).

    Causa típica:
    - Bug en el código de la API
    - Base de datos caída
    - Excepción no capturada

    Estrategia CLI:
    - NO reintentar (no es recuperable por el CLI)
    - Sugerir reportar el problema
    - Abort

    UX: "❌ Error interno del servidor. Por favor reporta este problema."
    """

    pass


# ============================================================================
# 🔌 ERRORES DE RED (no HTTP, sino de conexión)
# ============================================================================


class RAGConnectionError(RAGException):
    """Error de conexión de red (no HTTP).

    Causa típica:
    - API no alcanzable (sin internet, DNS, firewall)
    - Timeout de conexión (httpx.TimeoutException)
    - SSL/TLS error

    Estrategia CLI:
    - Retry 1x con 2s de espera
    - Fallback a cache
    - Fallback a LLM local
    - Modo offline completo

    UX: "🔌 Sin conexión a la API. Usando modo offline."
    """

    pass


# ============================================================================
# 🟢 RESPUESTAS PARCIALES (no son errores, pero necesitan manejo especial)
# ============================================================================


class RAGPartialResponse(RAGException):
    """Respuesta parcial o degradada (HTTP 206).

    Causa típica:
    - RAG sin fuentes disponibles
    - Cache corrupto pero usable
    - Respuesta generada sin contexto completo

    Estrategia CLI:
    - Usar la respuesta
    - Mostrar warning al usuario
    - NO es un error, es degradación aceptable

    UX: "⚠️ Respuesta generada sin acceso a todas las fuentes."

    Attributes:
        response: La respuesta parcial (para no perderla)
    """

    def __init__(
        self, message: str = "Respuesta parcial", response: str | None = None
    ) -> None:
        super().__init__(message)
        self.response = response


# ============================================================================
# HELPERS (para facilitar el mapeo HTTP → Excepción)
# ============================================================================


def map_http_status_to_exception(
    status_code: int,
    response_text: str = "",
    response_json: dict[str, Any] | None = None,
) -> RAGException:
    """Mapea un código HTTP a la excepción de dominio correspondiente.

    Args:
        status_code: Código HTTP de la respuesta
        response_text: Texto de la respuesta (para mensajes de error)
        response_json: JSON de la respuesta (para extraer detalles)

    Returns:
        Instancia de la excepción apropiada

    Example:
        >>> exc = map_http_status_to_exception(503, "Service Unavailable")
        >>> isinstance(exc, RAGUnavailable)
        True
    """
    response_json = response_json or {}

    # 🟡 Recuperables
    if status_code == 503:
        return RAGUnavailable("Proveedor de IA no disponible")

    if status_code == 504:
        return RAGTimeout("Timeout al consultar proveedor externo")

    if status_code == 502:
        return RAGUpstreamError("Error en infraestructura upstream")

    if status_code == 429:
        retry_after = response_json.get("retry_after")
        return RAGRateLimited(retry_after=retry_after)

    if status_code == 408:
        return RAGRequestTimeout("Timeout del request HTTP")

    # 🔴 Definitivos
    if status_code == 403:
        reason = response_json.get("reason", "unknown")
        return RAGBlocked(reason=reason)

    if status_code == 401:
        return RAGAuthError("Error de autenticación")

    if status_code == 404:
        return RAGNotFound("Endpoint no existe")

    if status_code == 422:
        # Caso especial: sesión no encontrada
        error_type = response_json.get("error", "")
        if "session" in error_type.lower() or "sesión" in response_text.lower():
            session_id = response_json.get("session_id")
            return RAGSessionNotFound(session_id=session_id)
        return RAGInvalidRequest(f"Request inválido: {response_text}")

    if status_code == 400:
        return RAGInvalidRequest(f"Request malformado: {response_text}")

    if status_code == 500:
        return RAGInternalError("Error interno de la API")

    # 🟢 Parcial
    if status_code == 206:
        response_content = response_json.get("answer")
        return RAGPartialResponse(response=response_content)

    # Default: error genérico
    return RAGException(f"HTTP {status_code}: {response_text}")
