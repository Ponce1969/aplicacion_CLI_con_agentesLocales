"""Test rápido para verificar que el refactor de rag_client no rompió nada."""

from core.exceptions import (
    RAGConnectionError,
    RAGPartialResponse,
    RAGSessionNotFound,
)
from core.rag_client import RAGClient


def test_basic_instantiation() -> None:
    """Verifica que el cliente se puede instanciar."""
    client = RAGClient()
    assert client is not None
    print("✅ Cliente instanciado correctamente")


def test_is_available() -> None:
    """Verifica que is_available() sigue funcionando."""
    client = RAGClient()
    # No importa si está disponible o no, solo que no lance excepción
    result = client.is_available()
    assert isinstance(result, bool)
    print(f"✅ is_available() funciona: {result}")


def test_get_status() -> None:
    """Verifica que get_status() sigue funcionando."""
    client = RAGClient()
    status = client.get_status()
    assert isinstance(status, dict)
    print(f"✅ get_status() funciona: {status.get('status', 'unknown')}")


def test_exceptions_are_importable() -> None:
    """Verifica que las excepciones se pueden importar."""
    assert RAGConnectionError is not None
    assert RAGPartialResponse is not None
    assert RAGSessionNotFound is not None
    print("✅ Excepciones importadas correctamente")


if __name__ == "__main__":
    print("🧪 Probando refactor de rag_client.py...\n")

    test_basic_instantiation()
    test_is_available()
    test_get_status()
    test_exceptions_are_importable()

    print("\n✅ Todas las pruebas básicas pasaron")
    print("⚠️  Nota: El comportamiento real se probará cuando orchestrator use las excepciones")
