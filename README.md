# 🤖 Sistema de Agentes Híbrido (CLI & RAG)

Un asistente de codificación inteligente que combina la velocidad de modelos locales (**Llama 3.1**, **Qwen 2.5**) con la autoridad de una base de conocimientos remota (**RAG Gemini**, **Web Kimi**).

---

## 🚀 Cómo Usarlo

El sistema está diseñado para ser flexible. Puedes usarlo para consultas rápidas o sesiones de trabajo profundas.

### 1. Modo "Disparo Único" (Single-Shot)
Ideal para scripts rápidos, definiciones o consultas puntuales. El agente responde y termina.

```powershell
# Pregunta directa
uv run python cli.py "Escribe un script en Python para descargar videos de YouTube"

# Consulta de conocimiento
uv run python cli.py "¿Cuáles son las novedades de Python 3.14?"
```

### 2. Modo Interactivo (Chat Continuo)
Usa la bandera `-i` o `--interactive`. El agente responde tu consulta inicial y **mantiene la sesión abierta**, recordando el contexto de la conversación.

```powershell
# Inicia una sesión de trabajo
uv run python cli.py "Explícame cómo funciona asyncio" -i
```
*Una vez dentro, puedes seguir preguntando: "¿Y cómo se compara con threading?" (El agente sabrá de qué hablas).*

### 3. Comandos Internos
Dentro del modo interactivo, tienes herramientas de control:

| Comando | Descripción |
| :--- | :--- |
| `/help` | Muestra la ayuda y modelos activos. |
| `/stats` | Ver estadísticas de uso (RAG vs Local, Cache hits). |
| `/patterns` | Ver qué patrones técnicos ha aprendido el sistema. |
| `/clear` | Limpia la pantalla. |
| `/exit` | Cierra la sesión y guarda el aprendizaje. |

---

## 🧠 Arquitectura del Sistema

El cerebro del sistema es un **Orquestador** que decide dinámicamente quién debe responder:

1.  **Router (Llama 3.1:8b)**:
    *   Analiza tu consulta.
    *   Si es lógica pura o conocimiento básico → **Responde Localmente**.
    *   Si detecta bibliotecas complejas (FastAPI, PyQt6) o necesidad de datos actuales → **Activa RAG/Web**.
    *   *Nota: Ahora tiene "humildad". Si no sabe, prefiere preguntar al RAG que inventar.*

2.  **Executor (Qwen 2.5:7b-instruct)**:
    *   Actúa como **Senior Code Reviewer**.
    *   Si Llama o RAG generan código, Qwen lo analiza, busca errores y lo valida antes de mostrártelo.
    *   Garantiza que el código cumpla estándares modernos (Type Hints, PEP8).

3.  **Capa Remota (RAG + Web)**:
    *   **Gemini RAG**: Consulta libros técnicos indexados (Fluent Python, Clean Code, etc.).
    *   **Kimi Web**: Busca en internet información de tiempo real.

---

## 🛠️ Instalación y Requisitos

Requiere **Python 3.12+** y acceso a un servidor Ollama local.

1.  **Dependencias**:
    ```bash
    pip install uv
    uv sync
    ```

2.  **Configuración (.env)**:
    ```ini
    RAG_BASE_URL="https://swagger-rag.loquinto.com"
    RAG_API_KEY="tu_clave_aquí"
    OLLAMA_BASE_URL="http://localhost:11434"
    ```

3.  **Verificación**:
    ```bash
    uv run mypy .  # El código es 100% Type Safe
    ```

---

## 📚 Base de Conocimiento (RAG)

El agente tiene acceso prioritario a estos documentos técnicos:

*   *Fluent Python (Luciano Ramalho)*
*   *FastAPI: Modern Python Web Development*
*   *Create GUI Applications with PyQt6*
*   *The Pragmatic Programmer*
*   *Google TechAI: Prompt Engineering*

---

## ✅ Estado del Proyecto

| Característica | Estado | Notas |
| :--- | :--- | :--- |
| **Routing Inteligente** | 🟢 Completo | Detecta temas y usa Tags `[[RAG]]`. |
| **Validación de Código** | 🟢 Completo | Qwen 2.5 corrige errores automáticamente. |
| **CLI Interactivo** | 🟢 Completo | Soporte para `-i` y argumentos. |
| **Memoria de Chat** | 🟢 Completo | Mantiene el hilo de conversación. |
| **Tipado Estricto** | 🟢 Completo | Pasa `mypy --strict`. |
| **Feedback UI** | 🟢 Completo | Spinners y mensajes claros con Rich. |

---
*Actualizado: 20/12/2025*
