import json
import os

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RAG_API_KEY", "")
BASE_URL = "https://swagger-rag.loquinto.com"
HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}


def test_rag_gemini() -> None:
    print("\n--- Probando RAG Gemini (session_id=0) ---")
    payload = {"query": "novedades de python 3.13", "mode": "rag", "session_id": 0}
    print(f"Payload: {json.dumps(payload)}")

    try:
        response = httpx.post(
            f"{BASE_URL}/api/internal/llm-gateway",
            json=payload,
            headers=HEADERS,
            timeout=60.0,
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print("Respuesta:")
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            print(f"Error: {response.text}")

    except Exception as e:
        print(f"Excepción: {e}")


if __name__ == "__main__":
    test_rag_gemini()
