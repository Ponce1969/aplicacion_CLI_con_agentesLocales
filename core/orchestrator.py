"""Orquestador principal del sistema de agentes."""

import time
from typing import Any

from agents.executor import ExecutorAgent
from agents.principal import PrincipalAgent
from config import RAG_ENABLED
from core.rag_client import RAGClient
from core.storage import KnowledgeStorage


class Orchestrator:
    """Coordina los agentes y decide estrategia de respuesta."""

    def __init__(self) -> None:
        self.principal = PrincipalAgent()
        self.executor = ExecutorAgent()
        self.rag = RAGClient()
        self.storage = KnowledgeStorage()

    def process(self, query: str) -> dict[str, Any]:
        """
        Procesa una consulta del usuario.

        Args:
            query: Consulta del usuario

        Returns:
            Dict con respuesta y metadata
        """
        start_time = time.time()

        # 1. Verificar cache
        cached = self.storage.get_cached_response(query)
        if cached:
            return {
                "response": cached,
                "source": "cache",
                "execution_time": time.time() - start_time,
            }

        # 2. Buscar patrones aprendidos
        learned_context = self._get_learned_context(query)

        # 3. Agente principal analiza
        analysis = self.principal.analyze(query, learned_context)

        # 4. Decidir si necesita RAG (solo si está habilitado)
        response = analysis["response"]
        needs_rag = analysis["confidence"] < 0.6 and RAG_ENABLED

        source = "principal"
        if needs_rag and self.rag.is_available():
            rag_result = self._try_rag_sources(query)
            if rag_result:
                response, source = rag_result

        # 5. Validar si contiene código
        validation_result = None
        if analysis["needs_validation"]:
            validation_result = self.executor.validate(
                response, context=query
            )

        # 6. Guardar interacción
        execution_time = time.time() - start_time
        self.storage.save_interaction(
            user_query=query,
            agent_response=response,
            agent_used=source,
            pattern_detected=",".join(analysis.get("patterns_detected", [])),
            rag_used=needs_rag,
            execution_time=execution_time,
            success=True,
        )

        # 7. Aprender patrones si es backend
        if analysis.get("patterns_detected"):
            self._learn_patterns(query, response, analysis["patterns_detected"])

        # 8. Cachear respuesta
        self.storage.cache_response(query, response)

        return {
            "response": response,
            "source": source,
            "patterns": analysis.get("patterns_detected", []),
            "validation": validation_result,
            "execution_time": execution_time,
            "confidence": analysis["confidence"],
        }

    def _try_rag_sources(self, query: str) -> tuple[str, str] | None:
        """Intenta obtener respuesta de fuentes RAG en orden."""
        # 1. Intentar Gemini RAG
        rag_response = self.rag.query_gemini_rag(query)
        if rag_response:
            return rag_response, "rag_gemini"

        # 2. Intentar Kimi-k2
        kimi_response = self.rag.query_kimi(query)
        if kimi_response:
            return kimi_response, "rag_kimi"

        return None

    def _get_learned_context(self, query: str) -> str | None:
        """Obtiene contexto de patrones aprendidos."""
        patterns = self.storage.get_frequent_patterns()

        if not patterns:
            return None

        # Buscar patrones relevantes
        query_lower = query.lower()
        relevant = [
            p for p in patterns
            if any(
                keyword in query_lower
                for keyword in p["key"].split("_")
            )
        ]

        if relevant:
            context_parts = [
                f"Patrón aprendido ({p['usage_count']} usos): {p['template'][:200]}"
                for p in relevant[:3]
            ]
            return "\n".join(context_parts)

        return None

    def _learn_patterns(
        self, query: str, response: str, patterns: list[str]
    ) -> None:
        """Aprende patrones de backend repetitivos."""
        for pattern in patterns:
            pattern_key = f"{pattern}_{hash(query) % 10000}"
            self.storage.learn_pattern(
                pattern_type=pattern,
                pattern_key=pattern_key,
                pattern_template=response[:500],
            )

    def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas del sistema."""
        storage_stats = self.storage.get_stats()
        rag_status = self.rag.get_status()

        return {
            "storage": storage_stats,
            "rag": rag_status,
            "agents": {
                "principal": self.principal.is_available(),
                "executor": self.executor.is_available(),
            },
        }

    def close(self) -> None:
        """Cierra todos los componentes."""
        self.principal.close()
        self.executor.close()
        self.rag.close()
        self.storage.close()

    def __del__(self) -> None:
        """Limpieza automática."""
        self.close()
