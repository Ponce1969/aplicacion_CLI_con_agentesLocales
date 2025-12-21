"""Orquestador principal del sistema de agentes."""

import time
from collections.abc import Callable
from typing import Any

from agents.executor import ExecutorAgent
from agents.principal import PrincipalAgent
from config import RAG_ENABLED
from core.exceptions import (
    RAGAuthError,
    RAGBlocked,
    RAGConnectionError,
    RAGException,
    RAGInternalError,
    RAGInvalidRequest,
    RAGPartialResponse,
    RAGRateLimited,
    RAGSessionNotFound,
    RAGTimeout,
    RAGUnavailable,
)
from core.rag_client import RAGClient
from core.storage import KnowledgeStorage


class Orchestrator:
    """Coordina los agentes y decide estrategia de respuesta."""

    def __init__(self) -> None:
        self.principal = PrincipalAgent()
        self.executor = ExecutorAgent()
        self.rag = RAGClient()
        self.storage = KnowledgeStorage()
        self.history: list[dict[str, str]] = []

    def process(
        self, query: str, status_callback: Callable[[str], None] | None = None
    ) -> dict[str, Any]:
        """
        Procesa una consulta del usuario.

        Args:
            query: Consulta del usuario
            status_callback: Función para actualizar estado en UI
        """
        start_time = time.time()

        if status_callback:
            status_callback("Verificando memoria local...")

        # 1. Verificar cache (solo si no hay historial previo para no romper contexto)
        # Si hay historial, es mejor reprocesar para mantener el hilo.
        cached = None
        if not self.history:
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
        if status_callback:
            status_callback("Analizando consulta (Llama 3.1)...")

        analysis = self.principal.analyze(query, learned_context, self.history)

        # 4. Routing Inteligente (Intent vs Confianza)
        intent = analysis.get("intent", "local")
        response = analysis["response"]
        source = "principal"

        # Determinar si necesitamos RAG
        needs_rag = False
        target_mode = None

        if intent == "rag":
            needs_rag = True
            target_mode = "rag"
        elif intent == "web":
            needs_rag = True
            target_mode = "kimi"
        elif analysis["confidence"] < 0.4:
            needs_rag = True
            target_mode = "auto"

        # Ejecutar RAG si es necesario y está habilitado
        rag_result = None
        if needs_rag and RAG_ENABLED and self.rag.is_available():
            if target_mode == "rag":
                if status_callback:
                    status_callback("Consultando Biblioteca RAG (Gemini)...")

                # Prioridad: RAG -> Kimi (fallback)
                rag_result = self._try_rag_with_fallback(
                    query, "rag", status_callback
                )

            elif target_mode == "kimi":
                if status_callback:
                    status_callback("Buscando en Internet (Kimi)...")

                # Prioridad: Kimi directo
                rag_result = self._try_rag_with_fallback(
                    query, "kimi", status_callback
                )

            else:  # target_mode == "auto" (comportamiento original)
                if status_callback:
                    status_callback("Consultando fuentes externas (Auto)...")

                rag_result = self._try_rag_with_fallback(
                    query, "auto", status_callback
                )

        if rag_result:
            response, source = rag_result
        elif needs_rag:
            # Fallback: RAG falló, no estaba disponible o estaba deshabilitado
            if status_callback:
                status_callback("RAG no disponible/falló. Generando respuesta local de emergencia...")

            response = self.principal.generate_local_fallback(query, learned_context)
            source = "principal_fallback"

        # 5. Validar si contiene código
        validation_result = None
        if analysis["needs_validation"]:
            if status_callback:
                status_callback("Validando código (Qwen 2.5)...")

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

        # 9. Actualizar historial
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": response})
        if len(self.history) > 10:
            self.history = self.history[-10:]

        return {
            "response": response,
            "source": source,
            "patterns": analysis.get("patterns_detected", []),
            "validation": validation_result,
            "execution_time": execution_time,
            "confidence": analysis["confidence"],
        }

    def _try_rag_with_fallback(
        self,
        query: str,
        mode: str,
        status_callback: Callable[[str], None] | None = None,
    ) -> tuple[str, str] | None:
        """Intenta obtener respuesta de RAG con manejo de excepciones.

        Args:
            query: Consulta del usuario
            mode: 'rag', 'kimi', o 'auto'
            status_callback: Función para actualizar estado en UI

        Returns:
            Tupla (respuesta, fuente) o None si falla completamente
        """
        try:
            if mode == "rag":
                # Intentar RAG (Gemini)
                response = self.rag.query_gemini_rag(query)
                return response, "rag_gemini"

            elif mode == "kimi":
                # Intentar Kimi directo
                response = self.rag.query_kimi(query)
                return response, "rag_kimi"

            else:  # mode == "auto"
                # Intentar RAG primero, luego Kimi
                try:
                    response = self.rag.query_gemini_rag(query)
                    return response, "rag_gemini"
                except RAGException:
                    # Si RAG falla, intentar Kimi
                    response = self.rag.query_kimi(query)
                    return response, "rag_kimi"

        except RAGUnavailable:
            # Proveedor IA no disponible (503)
            # Decisión: Cache -> LLM local
            if status_callback:
                status_callback("🔄 Servicio remoto no disponible, usando conocimiento local...")

            cached = self.storage.get_cached_response(query)
            if cached:
                return cached, "cache"

            # Fallback a LLM local
            learned_context = self._get_learned_context(query)
            response = self.principal.generate_local_fallback(query, learned_context)
            return response, "principal_fallback"

        except RAGConnectionError:
            # Error de red/conexión
            # Decisión: Cache -> LLM local (modo offline completo)
            if status_callback:
                status_callback("🔌 Sin conexión a la API, usando modo offline...")

            cached = self.storage.get_cached_response(query)
            if cached:
                return cached, "cache"

            # Fallback a LLM local
            learned_context = self._get_learned_context(query)
            response = self.principal.generate_local_fallback(query, learned_context)
            return response, "principal_fallback"

        except RAGTimeout:
            # Timeout externo (504)
            # Decisión: Retry 1x con 2s -> Cache
            if status_callback:
                status_callback("⏱️ Timeout del servicio remoto, reintentando...")

            time.sleep(2)
            try:
                # Retry una vez
                if mode == "rag":
                    response = self.rag.query_gemini_rag(query)
                    return response, "rag_gemini"
                elif mode == "kimi":
                    response = self.rag.query_kimi(query)
                    return response, "rag_kimi"
                else:  # auto
                    response = self.rag.query_gemini_rag(query)
                    return response, "rag_gemini"
            except RAGException:
                # Retry falló, usar cache
                if status_callback:
                    status_callback("⏱️ Timeout persistente, usando caché...")

                cached = self.storage.get_cached_response(query)
                if cached:
                    return cached, "cache"

                # Sin cache, abort (no usar LLM local para timeouts)
                return None

        except RAGRateLimited as e:
            # Rate limit alcanzado (429)
            # Decisión: Backoff exponencial, retry hasta 3x
            wait_time = e.retry_after or 5

            if status_callback:
                status_callback(f"⏳ Límite de consultas alcanzado. Esperando {wait_time}s...")

            time.sleep(wait_time)

            # Retry con backoff exponencial (máximo 3 intentos)
            for attempt in range(3):
                try:
                    if mode == "rag":
                        response = self.rag.query_gemini_rag(query)
                        return response, "rag_gemini"
                    elif mode == "kimi":
                        response = self.rag.query_kimi(query)
                        return response, "rag_kimi"
                    else:  # auto
                        response = self.rag.query_gemini_rag(query)
                        return response, "rag_gemini"
                except RAGRateLimited:
                    # Todavía rate limited, esperar más
                    wait_time = wait_time * 2  # Backoff exponencial
                    if attempt < 2:  # No esperar después del último intento
                        if status_callback:
                            status_callback(f"⏳ Aún limitado. Esperando {wait_time}s...")
                        time.sleep(wait_time)
                except RAGException:
                    # Otro error, abort
                    break

            # Todos los retries fallaron
            if status_callback:
                status_callback("⏳ Rate limit persistente, abortando...")

            return None

        except RAGPartialResponse as e:
            # Respuesta parcial (206) o placeholder detectado
            # Decisión: Usar la respuesta si existe, sino cache
            if status_callback:
                status_callback("⚠️ Respuesta parcial (sin todas las fuentes)...")

            if e.response:
                # Hay respuesta parcial, usarla
                return e.response, "rag_partial"

            # No hay respuesta, usar cache
            cached = self.storage.get_cached_response(query)
            if cached:
                return cached, "cache"

            # Sin cache, abort
            return None

        except RAGSessionNotFound:
            # Sesión no encontrada (422)
            # Decisión: Retry UNA VEZ con session_id=0
            if status_callback:
                status_callback("⚠️ Sesión inválida, creando nueva sesión...")

            try:
                # Retry con session_id=0 (nueva sesión)
                if mode == "rag":
                    response = self.rag.query(query, mode="rag", session_id=0)
                    return response, "rag_gemini"
                elif mode == "kimi":
                    response = self.rag.query(query, mode="kimi", session_id=0)
                    return response, "rag_kimi"
                else:  # auto
                    response = self.rag.query(query, mode="auto", session_id=0)
                    return response, "rag_gemini"
            except RAGException:
                # Retry falló, abort
                if status_callback:
                    status_callback("❌ No se pudo crear nueva sesión...")
                return None

        except RAGBlocked as e:
            # Guardian bloqueó la consulta (403)
            # Decisión: NO reintentar, abort
            if status_callback:
                status_callback(f"🛡️ Consulta bloqueada por seguridad: {e.reason}")

            # No hay fallback para contenido bloqueado
            return None

        except RAGAuthError:
            # Autenticación inválida (401)
            # Decisión: NO reintentar, abort
            if status_callback:
                status_callback("❌ Error de autenticación. Verifica RAG_API_KEY en .env")

            # No hay fallback para auth
            return None

        except RAGInvalidRequest as e:
            # Request inválido (400/422)
            # Decisión: NO reintentar (es un bug del CLI), abort
            if status_callback:
                status_callback(f"❌ Request inválido: {e.message}")

            # No hay fallback para bugs
            return None

        except RAGInternalError:
            # Error interno de la API (500)
            # Decisión: NO reintentar, abort
            if status_callback:
                status_callback("❌ Error interno del servidor. Reporta este problema.")

            # No hay fallback para bugs del servidor
            return None

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
