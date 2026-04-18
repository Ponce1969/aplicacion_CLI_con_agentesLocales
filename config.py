"""Configuración centralizada del proyecto."""

import os
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

# Cargar variables de entorno desde .env
load_dotenv()

# Modelos locales
PRINCIPAL_MODEL: Final[str] = "qwen-orchestrator"  # Modelfile: modelfiles/Modelfile.orchestrator
EXECUTOR_MODEL: Final[str] = "qwen-validator"  # Modelfile: modelfiles/Modelfile.validator

# Ollama
OLLAMA_BASE_URL: Final[str] = "http://localhost:11434"
OLLAMA_TIMEOUT: Final[int] = 120

# RAG remoto (Orange Pi 5 Plus con Cloudflare Tunnel)
RAG_BASE_URL: Final[str] = "https://swagger-rag.loquinto.com"
RAG_SWAGGER_URL: Final[str] = "https://swagger-rag.loquinto.com/docs"
RAG_API_KEY: Final[str] = os.getenv("RAG_API_KEY", "")
RAG_TIMEOUT: Final[float] = 60.0
RAG_ENABLED: Final[bool] = True

# Base de datos local
DB_PATH: Final[Path] = Path("agente_knowledge.db")

# Sistema de aprendizaje
LEARNING_THRESHOLD: Final[int] = 2  # Después de 2 usos, se considera patrón
CACHE_SIMILARITY_THRESHOLD: Final[float] = 0.85  # Similitud para cache hit

# Contexto de backend (patrones conocidos)
BACKEND_PATTERNS = {
    "arquitectura_hexagonal": [
        "domain",
        "application",
        "infrastructure",
        "adapters",
        "ports",
        "use_cases",
        "entities",
        "repositories",
    ],
    "fastapi": [
        "FastAPI",
        "APIRouter",
        "Depends",
        "HTTPException",
        "status",
        "Response",
        "Request",
        "BackgroundTasks",
    ],
    "postgresql": [
        "asyncpg",
        "sqlalchemy",
        "alembic",
        "migrations",
        "models",
        "schemas",
        "crud",
    ],
    "docker": [
        "Dockerfile",
        "docker-compose",
        "docker compose",
        "containerization",
        "docker volume",
        "docker network",
        "docker service",
        "docker build",
        "docker image",
    ],  # Patrones más específicos para evitar falsos positivos
    "dependency_injection": [
        "Depends",
        "get_db",
        "get_service",
        "Container",
        "inject",
        "provider",
    ],
    "typing": [
        "mypy",
        "ruff",
        "type hints",
        "Protocol",
        "TypeVar",
        "Generic",
        "Literal",
    ],
}

# Base de conocimiento indexada (RAG)
# Formato optimizado para el prompt del sistema: ID: Título (Keywords)
KNOWLEDGE_BASE_SUMMARY: Final[str] = """
- ID 30: FastAPI Modern Python Web Dev (backend, api, python web)
- ID 31: El Programador Pragmático (methodology, career, coding philosophy)
- ID 32: Effective Python (best practices, python tips, brett slatkin)
- ID 34: High Performance Python (optimization, performance, profiling)
- ID 35: Architecture Patterns with Python (ddd, architecture, hexagonal)
- ID 36: Patrones de Diseño (design patterns, gof, software design)
- ID 37: Clean Architecture (architecture, solid, robert martin)
- ID 38: Marco de Decisión (decision making, framework)
- ID 39: Fluent Python (advanced python, internals, data structures)
- ID 40: Designing Data-Intensive Applications (data, distributed systems, kleppmann)
"""

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
    "warning": "yellow",
}
