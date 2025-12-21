# 🧭 Comportamiento y Routing del Sistema CLI

**Versión:** 1.0.0  
**Fecha:** 21 Diciembre 2025  
**Estado:** Producción - Fase de Observación

---

## 📋 Propósito de Este Documento

Este documento describe cómo el sistema CLI toma decisiones de routing entre:
- **Respuesta local** (Llama 3.1 8B)
- **RAG remoto** (Gemini + búsqueda semántica)
- **Búsqueda web** (Kimi)

El objetivo es entender el comportamiento actual y documentar mejoras futuras basadas en observaciones reales.

---

## 🎯 Arquitectura de Decisión

### Flujo de Decisión del Orquestador

```
┌─────────────────────────────────────────────────────────────┐
│                    Usuario hace pregunta                     │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  1. Verificar caché (solo si no hay historial previo)       │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  2. Buscar patrones aprendidos (contexto previo)            │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  3. Agente Principal (Llama 3.1) analiza la consulta        │
│     - Devuelve: intent, confidence, response                │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  4. Routing Inteligente (Intent vs Confianza)               │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ if intent == "rag":                                   │  │
│  │     → Consultar RAG (Gemini)                         │  │
│  │                                                       │  │
│  │ elif intent == "web":                                │  │
│  │     → Consultar Kimi (búsqueda web)                  │  │
│  │                                                       │  │
│  │ elif confidence < 0.4:  ← UMBRAL CRÍTICO             │  │
│  │     → Consultar RAG (modo auto)                      │  │
│  │                                                       │  │
│  │ else:                                                 │  │
│  │     → Responder con Llama localmente                 │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## ⚙️ Parámetros Actuales

### Umbral de Confianza

**Ubicación:** `core/orchestrator.py:89`

```python
elif analysis["confidence"] < 0.4:
    needs_rag = True
    target_mode = "auto"
```

| Parámetro | Valor Actual | Descripción |
|-----------|--------------|-------------|
| **Umbral de confianza** | `0.4` (40%) | Si Llama tiene menos de 40% de confianza, consulta RAG |
| **Intent "rag"** | Forzado | Palabras clave detectadas → RAG obligatorio |
| **Intent "web"** | Forzado | Búsqueda web detectada → Kimi obligatorio |

### Patrones de Detección

**Palabras clave que fuerzan RAG:**
- `fastapi`, `pydantic`, `sqlalchemy`, `alembic`
- `pytest`, `unittest`, `mock`
- `docker`, `kubernetes`, `microservicios`
- `clean architecture`, `hexagonal`, `ddd`
- Y otros frameworks/conceptos específicos

**Palabras clave que fuerzan Kimi (web):**
- `busca`, `investiga`, `encuentra`
- `noticias`, `actualidad`, `últimas`
- `comparar`, `diferencias entre`

---

## 📊 Comportamiento Observado (21 Dic 2025)

### Caso 1: "¿Qué es FastAPI?"
- **Decisión:** RAG (Gemini)
- **Tiempo:** 22.42s
- **Evaluación:** ✅ **Correcto** - Framework específico, requiere info actualizada
- **Razón:** Patrón "fastapi" detectado → `intent = "rag"`

### Caso 2: "Explícame cómo funciona asyncio"
- **Decisión:** RAG (Gemini)
- **Tiempo:** 79.11s
- **Evaluación:** ⚠️ **Cuestionable** - Concepto fundamental de Python, Llama podría responder
- **Razón:** Probablemente `confidence < 0.4` → RAG automático
- **Observación:** Llama 3.1 8B **sí conoce** asyncio, pero fue conservador

### Caso 3: "Función que devuelva una lista"
- **Decisión:** Llama local
- **Tiempo:** 36.90s
- **Evaluación:** ✅ **Correcto** - Pregunta trivial, no requiere búsqueda
- **Razón:** `confidence >= 0.4` → Respuesta local

---

## 🎯 Análisis del Comportamiento Actual

### Fortalezas

1. **Conservador en temas específicos** ✅
   - Frameworks modernos → RAG
   - Librerías especializadas → RAG
   - Conceptos arquitectónicos → RAG

2. **Eficiente en preguntas triviales** ✅
   - Código básico → Llama local
   - Sintaxis simple → Llama local

3. **Fallback robusto** ✅
   - Si RAG falla → Llama responde
   - Si Gemini falla → Kimi como fallback
   - Si todo falla → Respuesta local de emergencia

### Debilidades Potenciales

1. **Demasiado conservador en conceptos fundamentales** ⚠️
   - `asyncio`, `decoradores`, `context managers` → Podrían responderse localmente
   - Tiempo extra: 60-80s vs 10-15s
   - Costo: Llamadas API innecesarias

2. **Umbral de confianza fijo** ⚠️
   - No distingue entre "concepto fundamental" vs "framework específico"
   - Llama podría ser más preciso en su autoevaluación

---

## 💡 Mejoras Futuras (NO Implementar Sin Observación)

### Opción 1: Ajustar Umbral de Confianza

**Cambio mínimo (conservador):**
```python
elif analysis["confidence"] < 0.45:  # Era 0.4
    needs_rag = True
```

**Efecto esperado:**
- Llama responderá conceptos fundamentales de Python
- Sigue siendo conservador para frameworks específicos
- Riesgo: **Bajo**

**Cambio moderado:**
```python
elif analysis["confidence"] < 0.5:  # Era 0.4
    needs_rag = True
```

**Efecto esperado:**
- Llama responderá más preguntas solo
- Reducción de llamadas RAG innecesarias
- Riesgo: **Medio** - Podría no consultar cuando debería

### Opción 2: Categorización de Temas

**Implementar lógica de categorías:**

```python
# Conceptos fundamentales de Python (confianza alta requerida: 0.7+)
PYTHON_FUNDAMENTALS = ["asyncio", "decoradores", "context managers", "generators"]

# Frameworks/librerías (confianza baja requerida: 0.3+)
FRAMEWORKS = ["fastapi", "django", "sqlalchemy", "pydantic"]

# Ajustar umbral dinámicamente según categoría
if topic in PYTHON_FUNDAMENTALS:
    threshold = 0.7  # Llama debe estar muy seguro
elif topic in FRAMEWORKS:
    threshold = 0.3  # Casi siempre ir a RAG
else:
    threshold = 0.4  # Umbral por defecto
```

**Efecto esperado:**
- Routing más inteligente
- Menos llamadas RAG innecesarias
- Riesgo: **Medio** - Más complejo de mantener

### Opción 3: Mejorar Prompt de Llama

**Hacer que Llama sea más preciso al evaluar su confianza:**

```
Para conceptos fundamentales de Python (asyncio, decoradores, etc.):
  → Confianza alta (0.8+) si conoces bien el tema

Para frameworks/librerías específicas (FastAPI, Pydantic, etc.):
  → Confianza baja (0.3-) para forzar búsqueda externa

Para código simple (funciones básicas):
  → Confianza muy alta (0.9+)
```

**Efecto esperado:**
- Llama más preciso en autoevaluación
- No requiere cambiar código de routing
- Riesgo: **Bajo** - Solo ajusta el prompt

---

## 📝 Plan de Observación

### Fase 1: Recolección de Datos (3-5 días)

**Anotar en este documento:**

```markdown
### Consultas RAG Cuestionables
- [ ] "asyncio" → RAG (79s) - Llama podría responder
- [ ] "decoradores" → RAG (?) - Pendiente de probar
- [ ] "context managers" → RAG (?) - Pendiente de probar

### Consultas RAG Correctas
- [x] "FastAPI" → RAG (22s) - Correcto
- [ ] "Pydantic 2.0 features" → RAG (?) - Pendiente de probar

### Consultas Locales Correctas
- [x] "función que devuelva lista" → Llama (37s) - Correcto
```

### Fase 2: Análisis (después de 3-5 días)

**Preguntas a responder:**
1. ¿Cuántas consultas RAG fueron innecesarias?
2. ¿Cuánto tiempo extra se perdió?
3. ¿Afecta la UX negativamente?
4. ¿Hay un patrón claro de temas que Llama podría responder?

### Fase 3: Decisión

**Si >30% de consultas RAG son innecesarias:**
- Implementar **Opción 1** (ajustar umbral a 0.45)
- Observar 2-3 días más
- Si funciona bien, considerar **Opción 3** (mejorar prompt)

**Si <10% de consultas RAG son innecesarias:**
- **NO cambiar nada**
- El sistema está bien calibrado

**Si 10-30% de consultas RAG son innecesarias:**
- Implementar **Opción 3** (mejorar prompt de Llama)
- Más preciso, menos riesgo

---

## 🔍 Métricas a Monitorear

| Métrica | Cómo Medirla | Objetivo |
|---------|--------------|----------|
| **Tasa de consultas RAG** | Contar consultas RAG vs total | <70% |
| **Tiempo promedio de respuesta** | Medir tiempos de cada tipo | <30s promedio |
| **Precisión de routing** | Evaluar si la decisión fue correcta | >90% |
| **Satisfacción del usuario** | Subjetivo - ¿la respuesta fue útil? | Alta |

---

## 🚫 Reglas de Cambio

**NO cambiar el código de routing sin:**
1. ✅ Al menos 3-5 días de observación
2. ✅ Datos concretos de consultas innecesarias
3. ✅ Análisis de impacto en UX
4. ✅ Plan de rollback si falla

**Razón:** El sistema está funcionando. Es mejor consultar de más que de menos.

---

## 📚 Referencias

- **Código de routing:** `core/orchestrator.py:74-120`
- **Análisis de Llama:** `core/orchestrator.py:72`
- **Fallback logic:** `core/orchestrator.py:122-129`
- **Contrato API-CLI:** `docs/api-cli-contract.md`

---

## 📝 Historial de Cambios

| Fecha | Cambio | Razón | Resultado |
|-------|--------|-------|-----------|
| 21 Dic 2025 | Documento creado | Documentar comportamiento actual | - |
| - | - | - | - |

---

**Última actualización:** 21 Diciembre 2025  
**Próxima revisión:** 24-26 Diciembre 2025 (después de observación)
