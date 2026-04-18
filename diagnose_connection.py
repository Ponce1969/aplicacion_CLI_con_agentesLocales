import json
import os
import time

import httpx
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

API_KEY = os.getenv("RAG_API_KEY", "")
BASE_URL = "https://swagger-rag.loquinto.com"

print("--- Diagnóstico de Conexión RAG/DeepSeek ---")
print(f"URL Base: {BASE_URL}")
print(f"API Key presente: {'Sí' if API_KEY else 'No'}")
if API_KEY:
    print(f"API Key (primeros 5): {API_KEY[:5]}...")

headers = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def test_endpoint(mode: str, query: str) -> None:
    print(f"\nProbando modo: {mode.upper()}")
    print(f"Consulta: {query}")

    payload = {
        "query": query,
        "mode": mode,
        "session_id": int(time.time()),  # ID único para evitar cache
    }

    try:
        start = time.time()
        response = httpx.post(
            f"{BASE_URL}/api/internal/llm-gateway",
            json=payload,
            headers=headers,
            timeout=60.0,
        )
        duration = time.time() - start

        print(f"Status Code: {response.status_code}")
        print(f"Tiempo: {duration:.2f}s")

        if response.status_code == 200:
            data = response.json()
            print("Respuesta Exitosa:")
            print(json.dumps(data, indent=2, ensure_ascii=False))

            answer = data.get("answer", "")
            if answer and answer != "Voy a buscar información actualizada sobre esto.":
                print("✅ Conexión y respuesta válida")
            else:
                print("⚠️ Respuesta sospechosa (posible placeholder o cache vacío)")
        else:
            print("❌ Error en la petición:")
            print(response.text)

    except Exception as e:
        print(f"❌ Excepción: {e}")


# 1. Probar Modo DeepSeek (Chat General, servidor usa mode='kimi' internamente)
test_endpoint("kimi", "¿Cual es la capital de Francia? Responde brevemente.")

# 2. Probar Modo RAG (Búsqueda)
test_endpoint("rag", "Novedades recientes de Python 3.13")
