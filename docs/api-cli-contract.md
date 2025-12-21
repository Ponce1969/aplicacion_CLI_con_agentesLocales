# Contrato API ↔ CLI: Manejo de Errores y Decisiones

**Versión**: 1.0  
**Fecha**: 21/12/2025  
**Propósito**: Definir el lenguaje común entre la API FastAPI y el CLI para manejo de fallos y degradación elegante.

---

## 🎯 Principio Fundamental

> **La API describe el problema. El CLI decide la acción.**

- La API **NO sugiere** soluciones (ej: "intenta de nuevo")
- El CLI **NO adivina** causas (ej: "tal vez fue la red")
- El contrato es **semántico**, no técnico
- El contrato es **estable**, no cambia con la implementación

---

## 📊 Clasificación de Fallos (Nivel Arquitectura)

Antes de hablar de HTTP, clasificamos los fallos por naturaleza:

| Categoría | ¿Quién la causa? | ¿Es recuperable? | Estrategia CLI |
|-----------|------------------|------------------|----------------|
| **Infraestructura** | Red, túnel, proxy | ✅ Sí | Retry corto |
| **Proveedor IA** | Gemini, Kimi, Brave | ⚠️ A veces | Retry → Fallback |
| **Seguridad** | Guardian, Auth | ❌ No | Abort |
| **Entrada** | Usuario | ❌ No | Mostrar error |
| **Bug interno** | Código API | ❌ No | Abort + Log |

---

## 🔄 Contrato HTTP → Semántica → Decisión CLI

### 🟢 Respuestas Exitosas

| HTTP | Significado API | Decisión CLI | UX |
|------|-----------------|--------------|-----|
| **200** | Respuesta completa del agente | Usar directamente | Mostrar respuesta |
| **206** | Respuesta parcial (ej: RAG sin fuentes) | Usar + marcar degradación | "⚠️ Respuesta parcial" |

**Ejemplo 206**:
```json
{
  "answer": "FastAPI es un framework...",
  "mode_used": "rag",
  "sources": [],
  "partial": true
}
```

---

### 🟡 Degradación Recuperable (Retry/Fallback)

| HTTP | Significado API | Decisión CLI | Retry | Fallback |
|------|-----------------|--------------|-------|----------|
| **503** | Proveedor IA no disponible | Retry 1x → Cache → Local | ✅ 1x | ✅ Cache/LLM |
| **504** | Timeout externo (Gemini/Kimi) | Retry 1x → Cache | ✅ 1x | ✅ Cache |
| **502** | Error upstream (Cloudflare) | Retry 2x corto | ✅ 2x | ❌ |
| **429** | Rate limit alcanzado | Backoff exponencial | ✅ 3x | ❌ |
| **408** | Request timeout | Retry 1x | ✅ 1x | ❌ |

**Estrategia de Retry**:
- **503/504**: 1 retry con 2s de espera → Fallback
- **502**: 2 retries con 1s, 2s → Fallo
- **429**: 3 retries con backoff exponencial (5s, 10s, 20s)
- **408**: 1 retry inmediato

**Ejemplo 503**:
```json
{
  "error": "GeminiUnavailable",
  "message": "El servicio Gemini no está disponible temporalmente",
  "retry_after": null
}
```

---

### 🔴 Fallos Definitivos (No Retry)

| HTTP | Significado API | Decisión CLI | Acción |
|------|-----------------|--------------|--------|
| **400** | Request inválido (malformado) | Mostrar error técnico | Abort |
| **401** | Auth inválida/expirada | Detener + avisar config | Abort |
| **403** | Guardian bloqueó la consulta | Mostrar razón + no reintentar | Abort |
| **404** | Endpoint no existe | Bug del CLI | Abort + Log |
| **422** | Error semántico (ej: sesión inválida) | Mostrar detalle | Abort |
| **500** | Bug interno de la API | Detener + reportar | Abort |

**Ejemplo 403**:
```json
{
  "error": "GuardianBlocked",
  "message": "La consulta fue bloqueada por el sistema de seguridad",
  "reason": "contenido_inapropiado"
}
```

**Ejemplo 422**:
```json
{
  "error": "InvalidSession",
  "message": "La sesión especificada no existe o expiró",
  "session_id": 123
}
```

---

## 🛡️ Casos Especiales (Edge Cases)

### 1. Error 500 con "Sesión no encontrada" (Caso Actual)

**Estado actual**: El CLI hace retry automático con `session_id=0`

**Propuesta**: Cambiar a **422** (Unprocessable Entity)

```python
# API debe devolver:
HTTP 422
{
  "error": "SessionNotFound",
  "message": "Sesión 123 no encontrada",
  "session_id": 123
}

# CLI debe:
# 1. Detectar 422 + "SessionNotFound"
# 2. Reintentar UNA VEZ con session_id=0
# 3. Si falla de nuevo, abort
```

### 2. Respuesta Placeholder (Cache Corrupto)

**Estado actual**: El CLI detecta texto placeholder y devuelve `None`

**Propuesta**: La API debe validar antes de devolver

```python
# API debe:
# - Detectar respuestas placeholder
# - Devolver 206 (Partial Content) en lugar de 200
# - Incluir flag "partial": true

# CLI debe:
# - Aceptar 206 como válido pero degradado
# - Mostrar warning: "⚠️ Respuesta parcial (fuentes no disponibles)"
```

### 3. Timeout de Red (httpx.TimeoutException)

**Estado actual**: El CLI captura `Exception` genérica

**Propuesta**: Mapear a decisión específica

```python
# CLI debe distinguir:
try:
    response = self.client.post(...)
except httpx.TimeoutException:
    # Timeout de red → Retry 1x → Cache
    return self._retry_with_fallback(query)
except httpx.ConnectError:
    # API no alcanzable → Cache directo
    return self._use_cache_or_local(query)
except httpx.HTTPStatusError as e:
    # Error HTTP → Seguir contrato
    return self._handle_http_error(e.response)
```

---

## 📋 Matriz de Decisión del CLI (Completa)

| HTTP | Retry | Backoff | Fallback | Cache | Local LLM | Abort | UX Message |
|------|-------|---------|----------|-------|-----------|-------|------------|
| 200 | ❌ | - | ❌ | ❌ | ❌ | ❌ | ✅ Respuesta |
| 206 | ❌ | - | ❌ | ❌ | ❌ | ❌ | ⚠️ Parcial |
| 400 | ❌ | - | ❌ | ❌ | ❌ | ✅ | ❌ Request inválido |
| 401 | ❌ | - | ❌ | ❌ | ❌ | ✅ | ❌ Auth inválida |
| 403 | ❌ | - | ❌ | ❌ | ❌ | ✅ | ❌ Bloqueado |
| 404 | ❌ | - | ❌ | ❌ | ❌ | ✅ | ❌ Bug CLI |
| 408 | ✅ 1x | 0s | ❌ | ❌ | ❌ | Si falla | ⏱️ Timeout |
| 422 | ⚠️ * | - | ❌ | ❌ | ❌ | Si falla | ❌ Error semántico |
| 429 | ✅ 3x | Exp | ❌ | ❌ | ❌ | Si falla | ⏳ Rate limit |
| 500 | ❌ | - | ❌ | ❌ | ❌ | ✅ | ❌ Bug API |
| 502 | ✅ 2x | 1s, 2s | ❌ | ❌ | ❌ | Si falla | 🔌 Upstream |
| 503 | ✅ 1x | 2s | ✅ | ✅ | ✅ | ❌ | 🔄 Degradado |
| 504 | ✅ 1x | 2s | ✅ | ✅ | ❌ | Si falla | ⏱️ Timeout |
| Timeout | ✅ 1x | 2s | ✅ | ✅ | ✅ | ❌ | 🔌 Sin conexión |
| ConnectError | ❌ | - | ✅ | ✅ | ✅ | ❌ | 🔌 API no alcanzable |

**Notas**:
- `*` 422: Solo retry si es `SessionNotFound` con `session_id=0`
- Exp: Backoff exponencial (5s, 10s, 20s)

---

## 💬 Mensajes UX (Parte del Contrato)

El CLI debe comunicar claramente al usuario qué está pasando:

### Mensajes de Degradación (🟡)

```python
# 503 - Proveedor no disponible
"🔄 Servicio de conocimiento remoto no disponible. Usando conocimiento local."

# 504 - Timeout
"⏱️ El servicio remoto tardó demasiado. Usando respuesta en caché."

# 429 - Rate limit
"⏳ Límite de consultas alcanzado. Reintentando en {seconds}s..."

# 502 - Upstream error
"🔌 Error de conexión con el servidor. Reintentando..."
```

### Mensajes de Fallo (🔴)

```python
# 401 - Auth
"❌ Autenticación inválida. Verifica RAG_API_KEY en .env"

# 403 - Guardian
"🛡️ La consulta fue bloqueada por el sistema de seguridad: {reason}"

# 422 - Sesión inválida
"⚠️ Sesión inválida. Creando nueva sesión..."

# 500 - Bug interno
"❌ Error interno del servidor. Por favor reporta este problema."
```

### Mensajes de Éxito Parcial (🟢)

```python
# 206 - Respuesta parcial
"⚠️ Respuesta generada sin acceso a todas las fuentes."
```

---

## 🔧 Implementación en el CLI

### Estructura Propuesta

```
core/
├── rag_client.py          # HTTP + Retry + Mapeo a excepciones
├── exceptions.py          # Excepciones de dominio (NEW)
└── orchestrator.py        # Decisiones de fallback
```

### Excepciones de Dominio (NEW)

```python
# core/exceptions.py

class RAGException(Exception):
    """Base para errores de RAG."""
    pass

class RAGUnavailable(RAGException):
    """Proveedor IA no disponible (503)."""
    pass

class RAGTimeout(RAGException):
    """Timeout externo (504)."""
    pass

class RAGRateLimited(RAGException):
    """Rate limit alcanzado (429)."""
    retry_after: int | None

class RAGBlocked(RAGException):
    """Guardian bloqueó la consulta (403)."""
    reason: str

class RAGInvalidRequest(RAGException):
    """Request inválido (400/422)."""
    pass

class RAGConnectionError(RAGException):
    """Error de red (Timeout/ConnectError)."""
    pass
```

### Flujo Propuesto en `rag_client.py`

```python
def query(self, question: str, mode: str = "auto") -> str:
    """
    Consulta al gateway con manejo de errores según contrato.
    
    Raises:
        RAGUnavailable: Proveedor no disponible (503)
        RAGTimeout: Timeout externo (504)
        RAGRateLimited: Rate limit (429)
        RAGBlocked: Guardian bloqueó (403)
        RAGInvalidRequest: Request inválido (400/422)
        RAGConnectionError: Error de red
    """
    try:
        response = self.client.post("/api/internal/llm-gateway", json=payload)
        
        if response.status_code == 200:
            return response.json()["answer"]
        
        if response.status_code == 206:
            console.print("[yellow]⚠️ Respuesta parcial[/yellow]")
            return response.json()["answer"]
        
        # Mapeo HTTP → Excepciones de dominio
        if response.status_code == 503:
            raise RAGUnavailable("Proveedor IA no disponible")
        
        if response.status_code == 504:
            raise RAGTimeout("Timeout externo")
        
        if response.status_code == 429:
            retry_after = response.json().get("retry_after")
            raise RAGRateLimited(retry_after=retry_after)
        
        if response.status_code == 403:
            reason = response.json().get("reason", "unknown")
            raise RAGBlocked(reason=reason)
        
        if response.status_code in (400, 422):
            raise RAGInvalidRequest(response.text)
        
        # Otros errores
        raise RAGException(f"HTTP {response.status_code}: {response.text}")
    
    except httpx.TimeoutException:
        raise RAGConnectionError("Timeout de red")
    
    except httpx.ConnectError:
        raise RAGConnectionError("API no alcanzable")
```

### Flujo Propuesto en `orchestrator.py`

```python
def _try_rag_with_fallback(self, query: str) -> tuple[str, str] | None:
    """Intenta RAG con fallback inteligente según tipo de error."""
    
    try:
        response = self.rag.query_gemini_rag(query)
        return response, "rag_gemini"
    
    except RAGUnavailable:
        # Proveedor no disponible → Cache → Local
        console.print("[yellow]🔄 RAG no disponible, usando conocimiento local[/yellow]")
        cached = self.storage.get_cached_response(query)
        if cached:
            return cached, "cache"
        return self.principal.generate_local_fallback(query), "principal_fallback"
    
    except RAGTimeout:
        # Timeout → Retry 1x → Cache
        console.print("[yellow]⏱️ Timeout, reintentando...[/yellow]")
        time.sleep(2)
        try:
            response = self.rag.query_gemini_rag(query)
            return response, "rag_gemini"
        except RAGException:
            cached = self.storage.get_cached_response(query)
            if cached:
                return cached, "cache"
            raise
    
    except RAGRateLimited as e:
        # Rate limit → Backoff → Retry
        wait = e.retry_after or 5
        console.print(f"[yellow]⏳ Rate limit. Esperando {wait}s...[/yellow]")
        time.sleep(wait)
        response = self.rag.query_gemini_rag(query)
        return response, "rag_gemini"
    
    except RAGBlocked as e:
        # Guardian bloqueó → Abort (no retry)
        console.print(f"[red]🛡️ Consulta bloqueada: {e.reason}[/red]")
        return None
    
    except RAGConnectionError:
        # Sin conexión → Cache → Local
        console.print("[yellow]🔌 Sin conexión a la API, usando modo offline[/yellow]")
        cached = self.storage.get_cached_response(query)
        if cached:
            return cached, "cache"
        return self.principal.generate_local_fallback(query), "principal_fallback"
    
    except RAGInvalidRequest as e:
        # Request inválido → Abort
        console.print(f"[red]❌ Request inválido: {e}[/red]")
        return None
```

---

## ✅ Garantías del Contrato

Este contrato garantiza:

- ✅ La API puede cambiar internamente sin romper el CLI
- ✅ Puedes cambiar Gemini por otro proveedor
- ✅ Puedes cambiar Cloudflare por otro proxy
- ✅ Puedes agregar más agentes
- ✅ El CLI puede evolucionar su estrategia de fallback
- ✅ Los tests pueden simular errores con solo HTTP mocks

**Sin**:
- ❌ Duplicar lógica de retry
- ❌ Ifs caóticos en el orchestrator
- ❌ Acoplar CLI a detalles de implementación de la API
- ❌ Romper la arquitectura hexagonal

---

## 🔓 Cómo Este Contrato Desbloquea Todo

### 1. Endpoint `/health` (Siguiente Paso)

Ahora sabes qué estados devolver:

```json
{
  "api": "ok",
  "providers": {
    "gemini": {"status": "ok", "latency_ms": 120},
    "kimi": {"status": "degraded", "latency_ms": 5000},
    "brave": {"status": "down", "error": "timeout"}
  },
  "circuit_breakers": {
    "gemini": "closed",
    "kimi": "half_open",
    "brave": "open"
  }
}
```

### 2. Flujo Completo (Siguiente Paso)

El flujo se dibuja con la tabla de decisiones.

### 3. Hardening (Siguiente Paso)

Retry, circuit breaker, backoff se implementan para **cumplir el contrato**.

### 4. Tests (Siguiente Paso)

Puedes testear el CLI simulando solo HTTP:

```python
def test_rag_unavailable_fallback():
    mock_response = Mock(status_code=503)
    # Verificar que usa cache → local
    
def test_rate_limit_backoff():
    mock_response = Mock(status_code=429, json={"retry_after": 10})
    # Verificar que espera 10s y reintenta
```

---

## 📝 Próximos Pasos

1. ✅ **Contrato definido** (este documento)
2. ⏳ **Implementar excepciones de dominio** (`core/exceptions.py`)
3. ⏳ **Refactorizar `rag_client.py`** (mapeo HTTP → excepciones)
4. ⏳ **Refactorizar `orchestrator.py`** (decisiones basadas en excepciones)
5. ⏳ **Diseñar `/health` endpoint** en la API
6. ⏳ **Implementar circuit breaker** en la API
7. ⏳ **Tests de contrato** (CLI y API)

---

**Mantenido por**: Sistema Híbrido CLI + API  
**Última actualización**: 21/12/2025  
**Estado**: ✅ Validado con código real
