"""Configuración centralizada del proyecto."""

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Modelos locales
PRINCIPAL_MODEL: Final[str] = "llama3.1:8b"
EXECUTOR_MODEL: Final[str] = "qwen2.5:7b-instruct"

# Ollama
OLLAMA_BASE_URL: Final[str] = "http://localhost:11434"
OLLAMA_TIMEOUT: Final[int] = 60

# RAG remoto (Orange Pi 5 Plus con Cloudflare Tunnel)
RAG_BASE_URL: Final[str] = "https://swagger-rag.loquinto.com"
RAG_SWAGGER_URL: Final[str] = "https://swagger-rag.loquinto.com/docs"
RAG_API_KEY: Final[str] = os.getenv("RAG_API_KEY", "")
RAG_TIMEOUT: Final[float] = 60.0
RAG_ENABLED: Final[bool] = True

# Base de datos local
DB_PATH: Final[Path] = Path("agente_knowledge.db")

# Sistema de aprendizaje
LEARNING_THRESHOLD: Final[int] = 3  # Después de 3 usos, se considera patrón
CACHE_SIMILARITY_THRESHOLD: Final[float] = 0.85  # Similitud para cache hit

# Contexto de backend (patrones conocidos)
BACKEND_PATTERNS = {
    "arquitectura_hexagonal": [
        "domain", "application", "infrastructure", "adapters",
        "ports", "use_cases", "entities", "repositories"
    ],
    "fastapi": [
        "FastAPI", "APIRouter", "Depends", "HTTPException",
        "status", "Response", "Request", "BackgroundTasks"
    ],
    "postgresql": [
        "asyncpg", "sqlalchemy", "alembic", "migrations",
        "models", "schemas", "crud"
    ],
    "docker": [
        "Dockerfile", "docker-compose.yml", "volumes",
        "networks", "services", "build", "image"
    ],
    "dependency_injection": [
        "Depends", "get_db", "get_service", "Container",
        "inject", "provider"
    ],
    "typing": [
        "mypy", "ruff", "type hints", "Protocol",
        "TypeVar", "Generic", "Literal"
    ]
}

# Colores para CLI (Rich)
COLORS = {
    "user": "cyan bold",
    "principal": "green",
    "executor": "yellow",
    "rag": "blue",
    "cache": "magenta",
    "code": "white on black",
    "error": "red bold",
    "success": "green bold",
    "info": "blue",
    "warning": "yellow"
}
