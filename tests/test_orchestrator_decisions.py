"""Tests de decisiones para Orchestrator: Validar estrategias de fallback.

Estos tests validan DECISIONES, no implementación:
- ¿Qué fuente se usa?
- ¿Qué camino se toma?
- ¿Qué NO se hace?
"""

from unittest.mock import Mock

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
)
from core.orchestrator import Orchestrator


@pytest.fixture
def orchestrator() -> Orchestrator:
    """Orchestrator para tests."""
    return Orchestrator()


# ============================================================================
# 🟡 Tests de Recuperables: RAGUnavailable
# ============================================================================


def test_rag_unavailable_uses_cache(orchestrator: Orchestrator, mocker: Mock) -> None:
    """Test: RAGUnavailable → Cache → Retorna cached."""
    mocker.patch.object(
        orchestrator.rag, "query_gemini_rag", side_effect=RAGUnavailable("Service unavailable")
    )
    mocker.patch.object(
        orchestrator.storage, "get_cached_response", return_value="cached answer"
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is not None
    assert result[0] == "cached answer"
    assert result[1] == "cache"


def test_rag_unavailable_without_cache_uses_local_llm(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGUnavailable sin cache → LLM local."""
    mocker.patch.object(
        orchestrator.rag, "query_gemini_rag", side_effect=RAGUnavailable("Service unavailable")
    )
    mocker.patch.object(orchestrator.storage, "get_cached_response", return_value=None)
    mocker.patch.object(
        orchestrator.principal, "generate_local_fallback", return_value="local answer"
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is not None
    assert result[0] == "local answer"
    assert result[1] == "principal_fallback"


# ============================================================================
# 🟡 Tests de Recuperables: RAGTimeout
# ============================================================================


def test_rag_timeout_retries_once_and_succeeds(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGTimeout → Retry 1x → Éxito."""
    mock_sleep = mocker.patch("time.sleep")

    # Primera llamada falla, segunda tiene éxito
    mocker.patch.object(
        orchestrator.rag,
        "query_gemini_rag",
        side_effect=[RAGTimeout("Timeout"), "rag answer after retry"],
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is not None
    assert result[0] == "rag answer after retry"
    assert result[1] == "rag_gemini"
    mock_sleep.assert_called_once_with(2)  # Espera 2s antes de retry


def test_rag_timeout_retry_fails_uses_cache(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGTimeout → Retry falla → Cache."""
    mocker.patch("time.sleep")
    mocker.patch.object(
        orchestrator.rag, "query_gemini_rag", side_effect=RAGTimeout("Timeout")
    )
    mocker.patch.object(
        orchestrator.storage, "get_cached_response", return_value="cached answer"
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is not None
    assert result[0] == "cached answer"
    assert result[1] == "cache"


def test_rag_timeout_no_cache_returns_none(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGTimeout → Retry falla → Sin cache → None."""
    mocker.patch("time.sleep")
    mocker.patch.object(
        orchestrator.rag, "query_gemini_rag", side_effect=RAGTimeout("Timeout")
    )
    mocker.patch.object(orchestrator.storage, "get_cached_response", return_value=None)

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is None


# ============================================================================
# 🟡 Tests de Recuperables: RAGRateLimited
# ============================================================================


def test_rag_rate_limited_waits_and_retries(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGRateLimited → Espera retry_after → Retry → Éxito."""
    mock_sleep = mocker.patch("time.sleep")

    # Primera llamada rate limited, segunda tiene éxito
    mocker.patch.object(
        orchestrator.rag,
        "query_gemini_rag",
        side_effect=[RAGRateLimited(retry_after=10), "rag answer after wait"],
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is not None
    assert result[0] == "rag answer after wait"
    assert result[1] == "rag_gemini"
    # Verifica que esperó el tiempo correcto
    assert mock_sleep.call_count >= 1
    assert 10 in [call[0][0] for call in mock_sleep.call_args_list]


def test_rag_rate_limited_exhausts_retries_returns_none(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGRateLimited → 3 retries fallan → None."""
    mocker.patch("time.sleep")
    mocker.patch.object(
        orchestrator.rag, "query_gemini_rag", side_effect=RAGRateLimited("Rate limited")
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is None


# ============================================================================
# 🟢 Tests de Parcial: RAGPartialResponse
# ============================================================================


def test_rag_partial_response_with_content_uses_it(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGPartialResponse con respuesta → Usa esa respuesta."""
    mocker.patch.object(
        orchestrator.rag,
        "query_gemini_rag",
        side_effect=RAGPartialResponse(response="partial answer"),
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is not None
    assert result[0] == "partial answer"
    assert result[1] == "rag_partial"


def test_rag_partial_response_without_content_uses_cache(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGPartialResponse sin respuesta → Cache."""
    mocker.patch.object(
        orchestrator.rag,
        "query_gemini_rag",
        side_effect=RAGPartialResponse(response=None),
    )
    mocker.patch.object(
        orchestrator.storage, "get_cached_response", return_value="cached answer"
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is not None
    assert result[0] == "cached answer"
    assert result[1] == "cache"


# ============================================================================
# 🟢 Tests de Caso Especial: RAGSessionNotFound
# ============================================================================


def test_rag_session_not_found_retries_with_session_0(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGSessionNotFound → Retry con session_id=0 → Éxito."""
    # Primera llamada falla, retry con session_id=0 tiene éxito
    mocker.patch.object(
        orchestrator.rag,
        "query",
        side_effect=[RAGSessionNotFound("Session not found"), "answer with new session"],
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is not None
    assert result[0] == "answer with new session"
    assert result[1] == "rag_gemini"


def test_rag_session_not_found_retry_fails_returns_none(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGSessionNotFound → Retry falla → None."""
    mocker.patch.object(
        orchestrator.rag, "query", side_effect=RAGSessionNotFound("Session not found")
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is None


# ============================================================================
# 🔴 Tests de Definitivos: NO retry, NO fallback
# ============================================================================


def test_rag_blocked_returns_none_no_retry(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGBlocked → None (sin retry, sin fallback)."""
    mocker.patch.object(
        orchestrator.rag,
        "query_gemini_rag",
        side_effect=RAGBlocked(reason="contenido_inapropiado"),
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is None


def test_rag_auth_error_returns_none_no_retry(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGAuthError → None (sin retry, sin fallback)."""
    mocker.patch.object(
        orchestrator.rag, "query_gemini_rag", side_effect=RAGAuthError("Auth error")
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is None


def test_rag_invalid_request_returns_none_no_retry(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGInvalidRequest → None (sin retry, sin fallback)."""
    mocker.patch.object(
        orchestrator.rag, "query_gemini_rag", side_effect=RAGInvalidRequest("Invalid request")
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is None


def test_rag_internal_error_returns_none_no_retry(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGInternalError → None (sin retry, sin fallback)."""
    mocker.patch.object(
        orchestrator.rag, "query_gemini_rag", side_effect=RAGInternalError("Internal error")
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is None


# ============================================================================
# 🔌 Tests de Red: RAGConnectionError
# ============================================================================


def test_rag_connection_error_uses_cache_then_local(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGConnectionError → Cache → LLM local."""
    mocker.patch.object(
        orchestrator.rag, "query_gemini_rag", side_effect=RAGConnectionError("Connection error")
    )
    mocker.patch.object(
        orchestrator.storage, "get_cached_response", return_value="cached answer"
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is not None
    assert result[0] == "cached answer"
    assert result[1] == "cache"


def test_rag_connection_error_no_cache_uses_local_llm(
    orchestrator: Orchestrator, mocker: Mock
) -> None:
    """Test: RAGConnectionError sin cache → LLM local."""
    mocker.patch.object(
        orchestrator.rag, "query_gemini_rag", side_effect=RAGConnectionError("Connection error")
    )
    mocker.patch.object(orchestrator.storage, "get_cached_response", return_value=None)
    mocker.patch.object(
        orchestrator.principal, "generate_local_fallback", return_value="local answer"
    )

    result = orchestrator._try_rag_with_fallback("test query", "rag")

    assert result is not None
    assert result[0] == "local answer"
    assert result[1] == "principal_fallback"
