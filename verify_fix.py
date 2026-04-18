from dotenv import load_dotenv

from core.rag_client import RAGClient

# Cargar variables
load_dotenv()


def verify_fixes() -> None:
    print("--- Verificando correcciones en RAGClient ---")
    client = RAGClient()

    # 1. Prueba de reintento de sesión (Simulamos fallo de sesión enviando ID inválido si pudiéramos controlar el ID,
    # pero el método query permite pasar session_id)
    print("\n1. Prueba de recuperación de Sesión (session_id=999999)")
    # Esto debería fallar primero con 500, y luego reintentar con 0 y tener éxito
    response = client.query("Hola DeepSeek", mode="kimi", session_id=999999)
    if response:
        print(f"✅ Recuperación exitosa. Respuesta: {response[:50]}...")
    else:
        print("❌ Falló la recuperación.")

    # 2. Prueba de filtrado de Placeholder (RAG)
    print("\n2. Prueba de filtrado de Placeholder (RAG)")
    # Usamos la query que sabemos que devuelve el placeholder
    response_rag = client.query_gemini_rag("novedades de python 3.13")

    if response_rag is None:
        print("✅ Placeholder filtrado correctamente (retornó None).")
    elif "Voy a buscar información" in response_rag:
        print("❌ Falló el filtrado: Se devolvió el placeholder.")
    else:
        print(f"✅ Se obtuvo una respuesta real: {response_rag[:50]}...")


if __name__ == "__main__":
    verify_fixes()
