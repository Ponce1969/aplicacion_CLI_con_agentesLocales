import json
import os
from typing import Any

import httpx
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RAG_API_KEY", "")
BASE_URL = "https://swagger-rag.loquinto.com"
HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_payload(name: str, payload: dict[str, Any]) -> None:
    print(f"\n--- Probando {name} ---")
    print(f"Payload: {json.dumps(payload)}")
    try:
        response = httpx.post(
            f"{BASE_URL}/api/internal/llm-gateway",
            json=payload,
            headers=HEADERS,
            timeout=30.0
        )
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

# Prueba 1: Sin session_id
test_payload("Sin session_id", {
    "query": "Hola Kimi",
    "mode": "kimi"
})

# Prueba 2: session_id = None
test_payload("session_id = None", {
    "query": "Hola Kimi",
    "mode": "kimi",
    "session_id": None
})

# Prueba 3: session_id = 0
test_payload("session_id = 0", {
    "query": "Hola Kimi",
    "mode": "kimi",
    "session_id": 0
})
