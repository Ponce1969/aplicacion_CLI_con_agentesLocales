# 🤖 Sistema de Agentes Híbrido (CLI & RAG)

Este proyecto implementa un sistema de agentes inteligente e híbrido que combina la velocidad y privacidad de modelos locales con la potencia y conocimiento actualizado de modelos grandes remotos (RAG).

## 🏗️ Arquitectura del Sistema

El sistema opera en dos capas principales:

### 1. Capa Local (El Cerebro Inmediato)
Ejecutada completamente en tu máquina para máxima velocidad y privacidad.
- **Orquestador**: Gestiona el flujo de la conversación y decide qué agente usar.
- **Agente Principal (`llama3.1:8b`)**: Analiza la intención del usuario, detecta patrones y genera respuestas iniciales. Es el "router" inteligente.
- **Agente Ejecutor (`qwen2.5:7b-instruct`)**: Especialista en código. Valida, corrige y mejora los snippets de código generados.
- **Memoria/Cache (SQLite)**: Almacena patrones frecuentes y respuestas anteriores para evitar consultas repetitivas.

### 2. Capa Remota (El Experto con Recursos)
Se activa solo cuando el agente local tiene "baja confianza" o detecta la necesidad de información externa.
- **Gateway Interno**: Un servidor intermedio protegido por API Key.
- **RAG (Gemini)**: Consulta bases de conocimientos (PDFs, documentación técnica) para respuestas profundas.
- **Kimi-k2 (Búsqueda Web)**: Realiza búsquedas en internet para información en tiempo real (ej. "precio de bitcoin", "novedades Python 3.14").

---

## 🔄 Flujo de Decisión (Cómo funciona)

1.  **Entrada del Usuario**: El usuario escribe una consulta en el CLI.
2.  **Análisis Local**:
    -   El **Orquestador** busca en caché primero.
    -   Si no está en caché, **Llama 3.1** analiza la consulta.
    -   Calcula un puntaje de **Confianza** (0.0 - 1.0).
3.  **Toma de Decisión**:
    -   Si `Confianza > Umbral` (y no hay frases de incertidumbre): Responde localmente.
    -   Si `Confianza < Umbral` O detecta "no sé", "buscar": **Activa RAG**.
4.  **Ejecución**:
    -   **Local**: Qwen valida el código si es necesario.
    -   **Remota**: Se consulta al Gateway (`/api/internal/llm-gateway`) usando el modo adecuado (`rag` o `kimi`).

---

## 🧠 Aprendizajes y Diagnóstico (Sesión Reciente)

Durante la implementación y pruebas del CLI, descubrimos y solucionamos varios comportamientos críticos del servidor remoto:

### 1. El Problema de la "Sesión No Encontrada" (Error 500)
-   **Síntoma**: El servidor RAG fallaba con Error 500 al enviar un `session_id` aleatorio o basado en tiempo.
-   **Causa**: El backend requiere que la sesión exista en su BD o que se use `session_id=0` para iniciar una nueva.
-   **Solución**: El cliente RAG ahora reintenta automáticamente con `session_id=0` si recibe un error de sesión no encontrada.

### 2. El Problema del "Placeholder" (Cache Corrupto)
-   **Síntoma**: Gemini respondía siempre *"Voy a buscar información actualizada sobre esto"* sin traer datos reales.
-   **Causa**: El servidor devolvía una respuesta cacheada vacía o de "preparación" en lugar del resultado final.
-   **Solución**: Se implementó un filtro en el cliente local que detecta esta frase específica, descarta la respuesta y fuerza un fallo para que el sistema lo maneje (o intente otra fuente).

### 3. El Desafío de la Confianza de Llama
-   **Observación**: `llama3.1:8b` es muy confiado. A menudo responde preguntas desconocidas con alucinaciones convincentes o negativas educadas ("No sé") pero con un puntaje de confianza alto, lo que impedía activar el RAG.
-   **Ajuste**: Se modificó el prompt para que indique explícitamente su incertidumbre y se ajustó el algoritmo de cálculo de confianza para penalizar drásticamente frases como "no tengo información".

---

## ⚙️ Configuración (.env)

El sistema requiere las siguientes variables para conectar con el Gateway seguro:

```ini
# Configuración del Gateway RAG
RAG_BASE_URL="https://swagger-rag.loquinto.com"
RAG_API_KEY="tu_clave_generada_segura"  # Debe coincidir con el servidor

# Configuración Ollama Local
OLLAMA_BASE_URL="http://localhost:11434"
```

---

## 📝 Roadmap: Estrategia y Tareas Pendientes

### Estrategia de Evolución del Agente
1.  **Integración Profunda de RAG (El "Libro de Estudio")**:
    -   Llama 3.1 debe ver al RAG no solo como un fallback, sino como su base de conocimiento autoritativa.
    -   Debemos mostrarle a Llama qué documentos tiene disponibles (ver lista abajo) para que sepa cuándo vale la pena consultar. Es como si un estudiante tuviera sus libros subrayados a mano.
    -   *Meta*: Que el router sepa "Esto seguro está en el libro de Python de Ramalho" y consulte con precisión.

2.  **Potenciar Kimi (Chat Texto Plano)**:
    -   Kimi tiene un potencial enorme para respuestas rápidas y fiables en texto plano.
    -   Puede ser una alternativa más veloz que el RAG completo para consultas generales o de actualidad que no requieren citar un PDF específico.

3.  **Maduración del Caché (SQLite)**:
    -   El objetivo a largo plazo es reducir la dependencia de las APIs (RAG/Kimi) a medida que el caché local crece.
    -   Sin embargo, Llama **nunca** debe volverse arrogante. Siempre debe mantener la humildad de consultar si tiene dudas, incluso con un caché grande.

4.  **Rol de Qwen**:
    -   Mantener a Qwen estrictamente como el **Validador de Código Impecable**. Su función es asegurar que cualquier código generado (sea por memoria o por consulta) funcione perfectamente.

### 📚 Base de Conocimiento Actual (RAG Index)
Para que el agente decida con criterio, debe conocer su "biblioteca". Estos son los documentos actualmente indexados y disponibles para consulta:

| ID | Título del Documento | Estado | Páginas | Temática Principal |
|:--:|:---|:--:|:--:|:---|
| **5** | *97 Things Every Programmer Should Know* | ✅ Indexed | 107 | Consejos generales, sabiduría de software |
| **6** | *FastAPI: Modern Python Web Development* | ✅ Indexed | 280 | Backend, APIs, Python moderno |
| **7** | *Fluent Python (Luciano Ramalho)* | ✅ Indexed | 1011 | Python avanzado, estructuras de datos |
| **9** | *Create GUI Applications with PyQt6* | ✅ Indexed | 758 | Interfaces gráficas desktop en Python |
| **10** | *El Programador Pragmático* | ✅ Indexed | 431 | Metodologías, filosofía de desarrollo |
| **11** | *Ciencia de Datos desde Cero* | ✅ Indexed | 300 | Data Science, algoritmos básicos |
| **12** | *Prompt Engineering for LLMs* | ✅ Indexed | 282 | Optimización de prompts, LLMs |
| **14** | *Google TechAI: Prompt Engineering Whitepaper* | ✅ Indexed | 65 | Guías técnicas oficiales de Google |
| **15** | *Think Python (Allen Downey)* | ✅ Indexed | 630 | Fundamentos de programación en Python |
| **16** | *Ciencia de Datos desde Cero (Duplicado/Ver)* | ✅ Indexed | 300 | Refuerzo de Data Science |

### Tareas Técnicas Inmediatas
1.  **Refinar el Prompt del Router**: ✅ Hecho. Inyectado resumen de tabla y sistema de "Action Tags" (`[[RAG]]`, `[[WEB]]`) para decisión determinista.
2.  **Mejoras Visuales (Rich)**: ✅ Hecho. Feedback en tiempo real ("Consultando Biblioteca...", "Buscando en Web...") y spinners conectados al orquestador.
3.  **Tipado Estricto (Mypy)**: ✅ Hecho. Código 100% compliant con `mypy --strict`.
4.  **Testing Integral**: Probar flujos completos (Local -> RAG -> Kimi) con preguntas trampa.

---

*Documento generado automáticamente por Cascade el 18/12/2025.*
