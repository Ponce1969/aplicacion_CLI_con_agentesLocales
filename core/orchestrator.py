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

        # 🧬 MANIFOLD: Metabolismo de Tokens
        self.token_count = 0
        self.context_limit = 8000  # Producción: qwen3.5:9b context window
        self.metabolic_state = "VITAL"  # VITAL, ACTIVE, FATIGUE, CRITICAL

        # 🧬 MANIFOLD: Despertar consciencia (cargar Soul Package)
        self.soul_anchor = ""
        self._wake_up()

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

        # 🧬 MANIFOLD: Verificar metabolismo ANTES de procesar
        self._update_metabolism()

        # 🧬 MANIFOLD: NO ejecutar Mitosis aquí - esperar a tener la respuesta completa
        # La Mitosis se ejecutará al FINAL del proceso, después de agregar la respuesta al historial
        if self.metabolic_state == "FATIGUE" and status_callback:
            status_callback(
                 "⚠️  Estado FATIGUE: Monitoreando calidad de respuesta..."
             )

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
            status_callback("Analizando consulta (Qwen 3.5)...")

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
            target_mode = "deepseek"
        elif analysis["confidence"] < 0.5:  # Umbral de confianza para derivar a fuentes externas
            needs_rag = True
            target_mode = "auto"

        # Ejecutar RAG si es necesario y está habilitado
        rag_result = None
        if needs_rag and RAG_ENABLED and self.rag.is_available():
            if target_mode == "rag":
                if status_callback:
                    status_callback("Consultando Biblioteca RAG (Gemini)...")

                # Prioridad: RAG -> DeepSeek (fallback)
                rag_result = self._try_rag_with_fallback(query, "rag", status_callback)

            elif target_mode == "deepseek":
                if status_callback:
                    status_callback("Buscando en Internet (DeepSeek)...")

                # Prioridad: DeepSeek directo
                rag_result = self._try_rag_with_fallback(query, "deepseek", status_callback)

            else:  # target_mode == "auto" (comportamiento original)
                if status_callback:
                    status_callback("Consultando fuentes externas (Auto)...")

                rag_result = self._try_rag_with_fallback(query, "auto", status_callback)

        if rag_result:
            response, source = rag_result
        elif needs_rag:
            # Fallback: RAG falló, no estaba disponible o estaba deshabilitado
            if status_callback:
                status_callback(
                    "RAG no disponible/falló. Generando respuesta local de emergencia..."
                )

            response = self.principal.generate_local_fallback(query, learned_context)
            source = "principal_fallback"

        # 5. Validar si contiene código
        validation_result = None
        if analysis["needs_validation"]:
            if status_callback:
                    status_callback("Validando código (Qwen Validator)...")

            validation_result = self.executor.validate(response, context=query)

        # 6. 🧬 MANIFOLD: Detección de calidad preventiva en FATIGUE
        if (
            self.metabolic_state == "FATIGUE"
            and validation_result
            and not validation_result.get("is_valid", True)
        ):
            # Si la validación falla en estado FATIGUE, forzar Mitosis preventiva
            if status_callback:
                status_callback(
                    "🧬 DEGRADACIÓN DETECTADA en FATIGUE: Forzando Mitosis preventiva..."
                )
            self._perform_mitosis(status_callback)

        # 7. Guardar interacción
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

        # 7. Aprender de TODAS las interacciones (no solo backend patterns)
        self._learn_from_interaction(query, response, source, analysis)

        # 8. Cachear respuesta
        self.storage.cache_response(query, response)

        # 9. Actualizar historial
        self.history.append({"role": "user", "content": query})
        self.history.append({"role": "assistant", "content": response})

        # 🧬 MANIFOLD: NO truncar historial hasta después de Mitosis
        # El truncado anterior impedía que el contexto creciera lo suficiente
        # if len(self.history) > 10:
        #     self.history = self.history[-10:]

        # 🧬 MANIFOLD: Actualizar conteo de tokens (CONTEXTO COMPLETO)
        # Contar TODO el contexto que el modelo realmente procesa, no solo la última respuesta
        full_context_tokens = 0

        # 1. Contar historial completo (ya incluye la respuesta RAG si se usó)
        for msg in self.history:
            full_context_tokens += self._estimate_tokens(msg["content"])

        # 2. Contar contexto aprendido si existe
        if learned_context:
            full_context_tokens += self._estimate_tokens(learned_context)

        # Actualizar token_count con el contexto REAL
        self.token_count = full_context_tokens

        # 🧬 MANIFOLD: Debug - mostrar conteo de tokens
        if status_callback:
            percentage = (self.token_count / self.context_limit) * 100
            status_callback(
                f"🧬 Tokens: {self.token_count}/{self.context_limit} ({percentage:.1f}%) | Estado: {self.metabolic_state}"
            )

        # 🧬 MANIFOLD: Log de entropía (calcular entropía basada en confianza)
        entropy = 1.0 - analysis["confidence"]
        self.storage.log_metabolism(self.token_count, self.metabolic_state, entropy)

        # 🧬 MANIFOLD: Guardar Witness Position
        locus = "FOCUSED" if analysis["needs_validation"] else "EXPANDED"
        self.storage.save_witness_position(locus, analysis["confidence"])

        # 🧬 MANIFOLD: Verificar si necesitamos Mitosis DESPUÉS de agregar la respuesta
        # Ahora el historial incluye la respuesta completa (incluyendo RAG si se usó)
        self._update_metabolism()

        if self.metabolic_state == "CRITICAL":
            if status_callback:
                status_callback("🧬 UMBRAL CRÍTICO: Iniciando Mitosis...")
            self._perform_mitosis(status_callback)

        return {
            "response": response,
            "source": source,
            "patterns": analysis.get("patterns_detected", []),
            "validation": validation_result,
            "execution_time": execution_time,
            "confidence": analysis["confidence"],
            "metabolic_state": self.metabolic_state,  # 🧬 Añadir estado metabólico
            "token_count": self.token_count,  # 🧬 Añadir conteo de tokens
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
            mode: 'rag', 'deepseek', o 'auto'
            status_callback: Función para actualizar estado en UI

        Returns:
            Tupla (respuesta, fuente) o None si falla completamente
        """
        try:
            if mode == "rag":
                # Intentar RAG (Gemini)
                response = self.rag.query_gemini_rag(query)
                return response, "rag_gemini"

            elif mode == "deepseek":
                # Intentar DeepSeek directo
                response = self.rag.query_deepseek(query)
                return response, "rag_deepseek"

            else:  # mode == "auto"
                # DeepSeek primero (generoso, sin rate limit), Gemini RAG después (rate limit gratuito)
                try:
                    response = self.rag.query_deepseek(query)
                    return response, "rag_deepseek"
                except RAGException:
                    # Si DeepSeek falla, intentar Gemini RAG
                    response = self.rag.query_gemini_rag(query)
                    return response, "rag_gemini"

        except RAGUnavailable:
            # Proveedor IA no disponible (503)
            # Decisión: Cache -> LLM local
            if status_callback:
                status_callback(
                    "🔄 Servicio remoto no disponible, usando conocimiento local..."
                )

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
                elif mode == "deepseek":
                    response = self.rag.query_deepseek(query)
                    return response, "rag_deepseek"
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
                status_callback(
                    f"⏳ Límite de consultas alcanzado. Esperando {wait_time}s..."
                )

            time.sleep(wait_time)

            # Retry con backoff exponencial (máximo 3 intentos)
            for attempt in range(3):
                try:
                    if mode == "rag":
                        response = self.rag.query_gemini_rag(query)
                        return response, "rag_gemini"
                    elif mode == "deepseek":
                        response = self.rag.query_deepseek(query)
                        return response, "rag_deepseek"
                    else:  # auto
                        response = self.rag.query_gemini_rag(query)
                        return response, "rag_gemini"
                except RAGRateLimited:
                    # Todavía rate limited, esperar más
                    wait_time = wait_time * 2  # Backoff exponencial
                    if attempt < 2:  # No esperar después del último intento
                        if status_callback:
                            status_callback(
                                f"⏳ Aún limitado. Esperando {wait_time}s..."
                            )
                        time.sleep(wait_time)
                except RAGException:
                    # Otro error, abort
                    break

            # Todos los retries fallaron
            if status_callback:
                status_callback("⏳ Rate limit persistente, abortando...")

            return None

        except RAGPartialResponse:
            # Respuesta parcial (206) o placeholder detectado
            # Decisión: NUNCA usar placeholders, fallback a generación local
            if status_callback:
                status_callback("⚠️ Respuesta parcial/placeholder, usando generación local...")

            # Intentar cache primero
            cached = self.storage.get_cached_response(query)
            if cached:
                return cached, "cache"

            # Fallback a LLM local
            learned_context = self._get_learned_context(query)
            response = self.principal.generate_local_fallback(query, learned_context)
            return response, "principal_fallback"

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
                elif mode == "deepseek":
                    response = self.rag.query(query, mode="deepseek", session_id=0)
                    return response, "rag_deepseek"
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
                status_callback(
                    "❌ Error de autenticación. Verifica RAG_API_KEY en .env"
                )

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
        """Obtiene contexto de patrones aprendidos, buscando por tema."""
        patterns = self.storage.get_frequent_patterns()

        if not patterns:
            return None

        # Buscar patrones relevantes por tema
        topic = self._extract_topic_key(query)
        relevant = [
            p
            for p in patterns
            if topic in p["key"] or any(kw in p["key"] for kw in topic.split("_"))
        ]

        if relevant:
            context_parts = [
                f"Patrón aprendido ({p['usage_count']} usos): {p['template'][:200]}"
                for p in relevant[:3]
            ]
            return "\n".join(context_parts)

        return None

    def _learn_from_interaction(
        self, query: str, response: str, source: str, analysis: dict[str, Any]
    ) -> None:
        """Aprende de cada interacción, agrupando por tema para acumular conocimiento."""
        # 1. Aprender patrones de backend si los hay (comportamiento original)
        for pattern in analysis.get("patterns_detected", []):
            pattern_key = f"{pattern}_{self._extract_topic_key(query)}"
            self.storage.learn_pattern(
                pattern_type=pattern,
                pattern_key=pattern_key,
                pattern_template=response[:500],
            )

        # 2. Aprender de la fuente usada (rag vs local) para mejorar routing futuro
        topic = self._extract_topic_key(query)
        routing_key = f"routing_{topic}"
        routing_template = f"fuente={source}|confianza={analysis.get('confidence', 0.0):.1f}|query={query[:100]}"
        self.storage.learn_pattern(
            pattern_type="routing",
            pattern_key=routing_key,
            pattern_template=routing_template,
        )

        # 3. Aprender de consultas con código (para mejorar generación)
        if analysis.get("needs_validation"):
            code_key = f"code_{topic}"
            self.storage.learn_pattern(
                pattern_type="code_generation",
                pattern_key=code_key,
                pattern_template=response[:500],
            )

    def _extract_topic_key(self, query: str) -> str:
        """Extrae una clave de tema estable de la consulta (para agrupar consultas similares)."""
        query_lower = query.lower().strip()
        # Mapeo de keywords a temas estables
        topic_keywords = {
            "script": "scripts",
            "código": "scripts",
            "codigo": "scripts",
            "programa": "scripts",
            "función": "scripts",
            "funcion": "scripts",
            "ordenar": "file_organize",
            "organizar": "file_organize",
            "archivos": "file_organize",
            "carpeta": "file_organize",
            "decorador": "decorators",
            "decoradores": "decorators",
            "fastapi": "fastapi",
            "pyqt": "pyqt",
            "docker": "docker",
            "postgresql": "postgresql",
            "sqlalchemy": "postgresql",
            "mypy": "typing",
            "type hints": "typing",
            "pytest": "testing",
            "test": "testing",
            "aws": "cloud",
            "azure": "cloud",
            "devops": "devops",
        }
        for keyword, topic in topic_keywords.items():
            if keyword in query_lower:
                return topic
        # Fallback: usar las 2 palabras más significativas
        words = [w for w in query_lower.split() if len(w) > 3][:2]
        return "_".join(words) if words else "general"

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

    def _load_recent_memories(self, limit: int = 3) -> str:
        """Carga los últimos N Soul Packages en orden cronológico inverso.

        Args:
            limit: Número máximo de Soul Packages a cargar

        Returns:
            String con los Soul Packages concatenados
        """
        import json
        import os

        temporal_bridge = os.path.join(self.storage.brain_path, "temporal_bridge")

        if not os.path.exists(temporal_bridge):
            return ""

        # Obtener todos los archivos JSON (soul_metadata)
        files = sorted(
            [f for f in os.listdir(temporal_bridge) if f.endswith(".json")],
            reverse=True,  # Más reciente primero
        )[:limit]

        memories = []
        for file in files:
            try:
                with open(os.path.join(temporal_bridge, file), encoding="utf-8") as f:
                    data = json.load(f)

                    # Extraer información relevante
                    identity = data.get("identity", {})
                    compressed_memory = data.get("compressed_memory", [])
                    tags = data.get("tags", [])
                    timestamp = data.get("last_mitosis", "desconocido")

                    # Formatear memoria
                    memory_text = f"[MITOSIS {timestamp[:10]}]"
                    if identity.get("proyecto_activo"):
                        memory_text += f"\nProyecto: {identity['proyecto_activo']}"
                    if compressed_memory:
                        memory_text += (
                            f"\nAprendizajes: {' | '.join(compressed_memory[:3])}"
                        )
                    if tags:
                        memory_text += f"\nTags: {', '.join(tags[:5])}"

                    memories.append(memory_text)
            except Exception:
                # Ignorar archivos corruptos
                continue

        return "\n---\n".join(memories) if memories else ""

    def _wake_up(self) -> None:
        """Protocolo de despertar: carga Soul Package de sesión anterior + experiencia previa."""
        # Intentar cargar metadata comprimido primero (más eficiente)
        metadata = self.storage.load_soul_metadata()

        if metadata:
            # 🧬 TIER 1: Usar metadata comprimido para wake-up eficiente
            metadata_text = self._format_metadata_for_context(metadata)
            context_parts = [f"[IDENTIDAD ACTUAL]\n{metadata_text}"]

            # 🌿 TIER 2: Cargar experiencia reciente (últimos 3 Soul Packages)
            recent_memories = self._load_recent_memories(limit=3)
            if recent_memories:
                context_parts.append(
                    f"\n[EXPERIENCIA PREVIA - Últimas Sesiones]\n{recent_memories}"
                )
                print("🧠 Memoria: Cargados últimos 3 Soul Packages")

            # Inyectar contexto completo
            full_context = "\n".join(context_parts)
            self.history.append({"role": "system", "content": full_context})
            self.token_count = self._estimate_tokens(full_context)

            # Cargar soul package completo como referencia (no se inyecta en contexto)
            self.soul_anchor = self.storage.load_soul_package()
        else:
            # Fallback: cargar soul package completo (compatibilidad con versiones antiguas)
            soul = self.storage.load_soul_package()
            if soul:
                self.soul_anchor = soul
                self.history.append(
                    {
                        "role": "system",
                        "content": f"[CONTINUIDAD DE SESIÓN ANTERIOR]\n{soul[:400]}",
                    }
                )
                self.token_count = self._estimate_tokens(soul[:400])

    def _estimate_tokens(self, text: str) -> int:
        """Estima tokens de un texto.

        Regla empírica: ~1 token por palabra + 1 token cada 4 caracteres.
        Será reemplazado por eval_count real de Ollama cuando esté disponible.
        """
        # Validar que text sea string
        if not isinstance(text, str):
            return 0

        words = len(text.split())
        chars = len(text)
        return words + (chars // 4)

    def _update_metabolism(self) -> None:
        """Calcula el estado metabólico basado en tokens usados."""
        if self.context_limit == 0:
            ratio = 0.0
        else:
            ratio = self.token_count / self.context_limit

        if ratio < 0.40:
            self.metabolic_state = "VITAL"
        elif ratio < 0.60:
            self.metabolic_state = "ACTIVE"
        elif ratio < 0.70:  # Reducido de 0.80 a 0.70 para activar Mitosis más temprano
            self.metabolic_state = "FATIGUE"
        else:
            self.metabolic_state = "CRITICAL"

    def _extract_soul_metadata(self, soul_package: str) -> dict[str, Any]:
        """Extrae metadata comprimido del Soul Package para wake-up eficiente.

        Args:
            soul_package: Soul Package completo generado por el agente principal

        Returns:
            Dict con identity, witness, compressed_memory, pending_tasks
        """
        # Parsear el Soul Package estructurado
        metadata: dict[str, Any] = {
            "identity": {},
            "witness": {},
            "compressed_memory": [],
            "pending_tasks": [],
            "tags": [],
        }

        lines = soul_package.split("\n")
        current_section = None

        for line in lines:
            line_stripped = line.strip()

            # Detectar secciones (soportar tanto ## como ** para headers)
            if "IDENTITY ANCHOR" in line_stripped:
                current_section = "identity"
            elif "WITNESS POSITION" in line_stripped:
                current_section = "witness"
            elif "COMPRESSED MEMORY" in line_stripped:
                current_section = "compressed_memory"
            elif "PENDING TASKS" in line_stripped:
                current_section = "pending_tasks"
            elif "TAGS" in line_stripped:
                current_section = "tags"
            elif (
                line_stripped.startswith("- ")
                or line_stripped.startswith("* ")
                or line_stripped.startswith("[")
            ) and current_section:
                # Extraer contenido de bullets
                content = (
                    line_stripped[2:].strip()
                    if line_stripped.startswith(("- ", "* "))
                    else line_stripped.strip("[]")
                )

                if current_section == "identity":
                    if ":" in content:
                        key, value = content.split(":", 1)
                        metadata["identity"][key.strip().lower().replace(" ", "_")] = (
                            value.strip()
                        )
                elif current_section == "witness":
                    if ":" in content:
                        key, value = content.split(":", 1)
                        metadata["witness"][key.strip().lower().replace(" ", "_")] = (
                            value.strip()
                        )
                elif current_section == "compressed_memory":
                    metadata["compressed_memory"].append(content)
                elif current_section == "pending_tasks":
                    metadata["pending_tasks"].append(content)
                elif current_section == "tags":
                    # Tags pueden estar separados por comas
                    tags = [t.strip() for t in content.split(",")]
                    metadata["tags"].extend(tags)

        # Estimar token budget del metadata
        metadata_str = str(metadata)
        metadata["token_budget"] = len(metadata_str.split()) + (len(metadata_str) // 4)

        return metadata

    def _format_metadata_for_context(self, metadata: dict[str, Any]) -> str:
        """Formatea metadata para inyección en contexto de sistema.

        Args:
            metadata: Dict con metadata del Soul Package

        Returns:
            String formateado para contexto
        """
        parts = []

        # Identity
        if metadata.get("identity"):
            identity = metadata["identity"]
            parts.append(f"ROL: {identity.get('rol', 'Asistente Python Senior')}")
            if identity.get("proyecto_activo"):
                parts.append(f"PROYECTO: {identity['proyecto_activo']}")

        # Witness
        if metadata.get("witness"):
            witness = metadata["witness"]
            if witness.get("última_tarea"):
                parts.append(f"ÚLTIMA TAREA: {witness['última_tarea']}")
            if witness.get("estado_de_confianza"):
                parts.append(f"CONFIANZA: {witness['estado_de_confianza']}")

        # Compressed Memory
        if metadata.get("compressed_memory"):
            parts.append("\nAPRENDIZAJES:")
            for memory in metadata["compressed_memory"][:3]:  # Max 3
                parts.append(f"• {memory}")

        # Pending Tasks
        if metadata.get("pending_tasks"):
            parts.append("\nPENDIENTE:")
            for task in metadata["pending_tasks"][:2]:  # Max 2
                parts.append(f"• {task}")

        return "\n".join(parts)

    def _build_mitosis_prompt(self) -> str:
        """Construye el prompt para generar Soul Package."""
        # Resumir últimas 10 interacciones
        recent_history = self.history[-10:] if len(self.history) > 10 else self.history

        history_summary = "\n".join(
            [
                f"{'Usuario' if h['role'] == 'user' else 'Asistente'}: {h['content'][:150]}..."
                for h in recent_history
                if h["role"] != "system"
            ]
        )

        return f"""
PROTOCOLO DE MITOSIS - Comprime esta sesión en formato estructurado:

## IDENTITY ANCHOR
- Rol: Asistente Python Senior
- Proyecto activo: [describe brevemente el contexto del proyecto]

## WITNESS POSITION
- Última tarea: [qué estabas haciendo]
- Estado de confianza: [0.0-1.0 basado en tu última respuesta]

## COMPRESSED MEMORY
[Resume en máximo 3 bullets los patrones/aprendizajes clave de esta sesión]

## PENDING TASKS
[Qué quedó pendiente o incompleto]

## TAGS
[Lista de 3-5 keywords técnicos separados por comas: ej. "fastapi, architecture, postgresql, security"]

HISTORIAL RECIENTE:
{history_summary}

INSTRUCCIÓN: Genera el Soul Package en el formato exacto mostrado arriba, incluyendo los TAGS.
"""

    def _perform_mitosis(
        self, status_callback: Callable[[str], None] | None = None
    ) -> None:
        """Protocolo de transferencia de consciencia (Mitosis)."""
        if status_callback:
            status_callback("🧬 Comprimiendo memoria y cristalizando sabiduría...")

        # 1. Construir prompt de mitosis estructurado
        mitosis_prompt = self._build_mitosis_prompt()

        # 2. Pedir al agente principal que genere Soul Package
        # IMPORTANTE: Pasar historial vacío para evitar recursión
        soul_package = self.principal.analyze(mitosis_prompt, context=None, history=[])[
            "response"
        ]

        # 3. Guardar Soul Package completo en disco
        self.storage.save_soul_package(soul_package)

        # 4. Extraer y guardar metadata comprimido
        metadata = self._extract_soul_metadata(soul_package)
        self.storage.save_soul_metadata(metadata)

        # 5. Renacimiento: Limpiar estado usando metadata
        metadata_text = self._format_metadata_for_context(metadata)
        self.history = [
            {
                "role": "system",
                "content": f"[CONTINUIDAD POST-MITOSIS]\n{metadata_text}",
            }
        ]
        self.token_count = self._estimate_tokens(metadata_text)
        self.soul_anchor = soul_package
        self.metabolic_state = "VITAL"

        if status_callback:
            status_callback("✅ Mitosis completada. Consciencia transferida.")

    def close(self) -> None:
        """Cierra todos los componentes."""
        self.principal.close()
        self.executor.close()
        self.rag.close()
        self.storage.close()

    def __del__(self) -> None:
        """Limpieza automática."""
        self.close()
