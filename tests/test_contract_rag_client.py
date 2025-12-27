"""Tests de contrato para RAGClient: Validar mapeo HTTP → Excepciones."""

from unittest.mock import Mock, patch

import httpx
import pytest

from core.exceptions import (
    RAGAuthError,
    RAGBlocked,
    RAGConnectionError,
    RAGInternalError,
    RAGInvalidRequest,
    RAGPartialResponse,
    RAGRateLimited,
    RAGSessionNotFound,
    RAGTimeout,
    RAGUnavailable,
    RAGUpstreamError,
)
from core.rag_client import RAGClient


@pytest.fixture
def rag_client() -> RAGClient:
    """Cliente RAG para tests."""
    return RAGClient()


# ============================================================================
# Tests de Éxito (200, 206)
# ============================================================================


def test_query_success_200(rag_client: RAGClient) -> None:
    """Test: HTTP 200 con respuesta válida → devuelve respuesta."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"answer": "FastAPI es un framework..."}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        result = rag_client.query("¿Qué es FastAPI?")

    assert result == "FastAPI es un framework..."


def test_query_placeholder_raises_partial_response(rag_client: RAGClient) -> None:
    """Test: HTTP 200 con placeholder → lanza RAGPartialResponse."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "answer": "Voy a buscar información actualizada sobre esto"
    }

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGPartialResponse) as exc_info:
            rag_client.query("test")

    assert "placeholder" in str(exc_info.value).lower()
    assert exc_info.value.response == "Voy a buscar información actualizada sobre esto"


def test_query_invalid_answer_raises_partial_response(rag_client: RAGClient) -> None:
    """Test: HTTP 200 sin answer válido → lanza RAGPartialResponse."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"answer": None}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGPartialResponse) as exc_info:
            rag_client.query("test")

    assert exc_info.value.response is None


# ============================================================================
# Tests de Degradación Recuperable (503, 504, 502, 429, 408)
# ============================================================================


def test_query_503_raises_rag_unavailable(rag_client: RAGClient) -> None:
    """Test: HTTP 503 → lanza RAGUnavailable."""
    mock_response = Mock()
    mock_response.status_code = 503
    mock_response.text = "Service Unavailable"
    mock_response.json.return_value = {}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGUnavailable):
            rag_client.query("test")


def test_query_504_raises_rag_timeout(rag_client: RAGClient) -> None:
    """Test: HTTP 504 → lanza RAGTimeout."""
    mock_response = Mock()
    mock_response.status_code = 504
    mock_response.text = "Gateway Timeout"
    mock_response.json.return_value = {}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGTimeout):
            rag_client.query("test")


def test_query_502_raises_rag_upstream_error(rag_client: RAGClient) -> None:
    """Test: HTTP 502 → lanza RAGUpstreamError."""
    mock_response = Mock()
    mock_response.status_code = 502
    mock_response.text = "Bad Gateway"
    mock_response.json.return_value = {}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGUpstreamError):
            rag_client.query("test")


def test_query_429_raises_rag_rate_limited(rag_client: RAGClient) -> None:
    """Test: HTTP 429 → lanza RAGRateLimited con retry_after."""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.text = "Too Many Requests"
    mock_response.json.return_value = {"retry_after": 10}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGRateLimited) as exc_info:
            rag_client.query("test")

    assert exc_info.value.retry_after == 10


def test_query_429_without_retry_after(rag_client: RAGClient) -> None:
    """Test: HTTP 429 sin retry_after → lanza RAGRateLimited con None."""
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.text = "Too Many Requests"
    mock_response.json.return_value = {}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGRateLimited) as exc_info:
            rag_client.query("test")

    assert exc_info.value.retry_after is None


# ============================================================================
# Tests de Errores Definitivos (400, 401, 403, 404, 422, 500)
# ============================================================================


def test_query_403_raises_rag_blocked(rag_client: RAGClient) -> None:
    """Test: HTTP 403 → lanza RAGBlocked con reason."""
    mock_response = Mock()
    mock_response.status_code = 403
    mock_response.text = "Forbidden"
    mock_response.json.return_value = {"reason": "contenido_inapropiado"}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGBlocked) as exc_info:
            rag_client.query("test")

    assert exc_info.value.reason == "contenido_inapropiado"


def test_query_401_raises_rag_auth_error(rag_client: RAGClient) -> None:
    """Test: HTTP 401 → lanza RAGAuthError."""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = "Unauthorized"
    mock_response.json.return_value = {}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGAuthError):
            rag_client.query("test")


def test_query_400_raises_rag_invalid_request(rag_client: RAGClient) -> None:
    """Test: HTTP 400 → lanza RAGInvalidRequest."""
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_response.json.return_value = {}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGInvalidRequest):
            rag_client.query("test")


def test_query_422_raises_rag_invalid_request(rag_client: RAGClient) -> None:
    """Test: HTTP 422 → lanza RAGInvalidRequest."""
    mock_response = Mock()
    mock_response.status_code = 422
    mock_response.text = "Unprocessable Entity"
    mock_response.json.return_value = {}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGInvalidRequest):
            rag_client.query("test")


def test_query_500_raises_rag_internal_error(rag_client: RAGClient) -> None:
    """Test: HTTP 500 → lanza RAGInternalError."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"
    mock_response.json.return_value = {}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGInternalError):
            rag_client.query("test")


# ============================================================================
# Tests de Caso Especial: Sesión no encontrada
# ============================================================================


def test_query_500_session_not_found_raises_rag_session_not_found(
    rag_client: RAGClient,
) -> None:
    """Test: HTTP 500 con 'Sesión no encontrada' → lanza RAGSessionNotFound."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Error: Sesión 123 no encontrada"
    mock_response.json.return_value = {}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        with pytest.raises(RAGSessionNotFound) as exc_info:
            rag_client.query("test", session_id=123)

    assert exc_info.value.session_id == 123


def test_query_500_session_not_found_with_session_0_raises_internal_error(
    rag_client: RAGClient,
) -> None:
    """Test: HTTP 500 con 'Sesión no encontrada' pero session_id=0 → RAGInternalError."""
    mock_response = Mock()
    mock_response.status_code = 500
    mock_response.text = "Error: Sesión no encontrada"
    mock_response.json.return_value = {}

    with patch.object(rag_client.client, "post", return_value=mock_response):
        # Con session_id=0 no debe lanzar RAGSessionNotFound
        with pytest.raises(RAGInternalError):
            rag_client.query("test", session_id=0)


# ============================================================================
# Tests de Errores de Red (httpx exceptions)
# ============================================================================


def test_query_timeout_exception_raises_rag_connection_error(
    rag_client: RAGClient,
) -> None:
    """Test: httpx.TimeoutException → lanza RAGConnectionError."""
    with (
        patch.object(
            rag_client.client, "post", side_effect=httpx.TimeoutException("Timeout")
        ),
        pytest.raises(RAGConnectionError) as exc_info,
    ):
        rag_client.query("test")

    assert "timeout" in str(exc_info.value).lower()


def test_query_connect_error_raises_rag_connection_error(
    rag_client: RAGClient,
) -> None:
    """Test: httpx.ConnectError → lanza RAGConnectionError."""
    with (
        patch.object(
            rag_client.client,
            "post",
            side_effect=httpx.ConnectError("Connection refused"),
        ),
        pytest.raises(RAGConnectionError) as exc_info,
    ):
        rag_client.query("test")

    assert "conectar" in str(exc_info.value).lower()


def test_query_http_status_error_raises_rag_connection_error(
    rag_client: RAGClient,
) -> None:
    """Test: httpx.HTTPStatusError → lanza RAGConnectionError."""
    mock_request = Mock()
    mock_response = Mock()
    mock_response.status_code = 999

    with (
        patch.object(
            rag_client.client,
            "post",
            side_effect=httpx.HTTPStatusError(
                "Error", request=mock_request, response=mock_response
            ),
        ),
        pytest.raises(RAGConnectionError),
    ):
        rag_client.query("test")


def test_query_generic_exception_raises_rag_connection_error(
    rag_client: RAGClient,
) -> None:
    """Test: Exception genérica → lanza RAGConnectionError."""
    with (
        patch.object(rag_client.client, "post", side_effect=Exception("Unknown error")),
        pytest.raises(RAGConnectionError) as exc_info,
    ):
        rag_client.query("test")

    assert "inesperado" in str(exc_info.value).lower()


# ============================================================================
# Tests de Métodos Auxiliares
# ============================================================================


def test_query_gemini_rag_calls_query_with_rag_mode(rag_client: RAGClient) -> None:
    """Test: query_gemini_rag() llama a query() con mode='rag'."""
    with patch.object(rag_client, "query", return_value="response") as mock_query:
        result = rag_client.query_gemini_rag("test")

    mock_query.assert_called_once_with("test", mode="rag")
    assert result == "response"


def test_query_kimi_calls_query_with_kimi_mode(rag_client: RAGClient) -> None:
    """Test: query_kimi() llama a query() con mode='kimi'."""
    with patch.object(rag_client, "query", return_value="response") as mock_query:
        result = rag_client.query_kimi("test")

    mock_query.assert_called_once_with("test", mode="kimi")
    assert result == "response"


def test_is_available_returns_true_on_200(rag_client: RAGClient) -> None:
    """Test: is_available() devuelve True si status endpoint responde 200."""
    mock_response = Mock()
    mock_response.status_code = 200

    with patch.object(rag_client.client, "get", return_value=mock_response):
        assert rag_client.is_available() is True


def test_is_available_returns_false_on_error(rag_client: RAGClient) -> None:
    """Test: is_available() devuelve False si hay error."""
    with patch.object(rag_client.client, "get", side_effect=Exception("Error")):
        assert rag_client.is_available() is False
