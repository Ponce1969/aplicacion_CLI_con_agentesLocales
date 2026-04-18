# 🤖 Sistema de Agentes Inteligentes (CLI & RAG)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Type Checked: mypy](https://img.shields.io/badge/type_checked-mypy-blue.svg)](http://mypy-lang.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

CLI inteligente que combina **modelos locales** (Qwen 3.5 + Qwen 2.5 Coder) con **API externa** RAG (DeepSeek + Gemini). Cuando los modelos locales tienen dudas, consultan automáticamente la API para obtener información actualizada.

> **🔗 Conexión Principal:** Este CLI se conecta a [este repositorio API](https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini) que proporciona:
> - 🌐 **DeepSeek**: Consultor senior con 5 roles especializados (fuente primaria externa)
> - 📚 **Gemini RAG**: Base de conocimientos con libros indexados (citas textuales)
> - ⚡ **API REST**: Endpoint `/api/internal/llm-gateway` para consultas externas

> **🎯 Características:**
> - 🧠 **Qwen 3.5 (9B)**: Orquestador principal (decide cuándo consultar externo)
> - ✅ **Qwen 2.5 Coder (7B)**: Validador de código (revisa y corrige respuestas)
> - 🔄 **Routing automático**: Etiquetas `[[WEB]]` y `[[RAG]]` activan fuentes externas
> - 💬 **Modo interactivo** con memoria persistente y aprendizaje
> - 🔍 **Type-safe** con mypy --strict

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

### 🔗 Flujo de Conexión CLI ↔ API

```
CLI (Local)                         API (Remota)
├─ qwen-orchestrator (Qwen 3.5) ──→ ├─ DeepSeek (5 roles senior)
├─ qwen-validator (Qwen Coder)     ├─ Gemini RAG (libros indexados)
└─ Rich CLI (UI)                   └─ FastAPI Server (Cloudflare Tunnel)
```

**1. Modelos Locales (Ollama):**
- **qwen-orchestrator** (Qwen 3.5 9B): Analiza tu consulta y decide si necesita información externa. System prompt horneado en Modelfile.
- **qwen-validator** (Qwen 2.5 Coder 7B): Valida y mejora el código generado. Especializado en Python 3.12+ moderno.

**2. API Externa ([Repositorio API](https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini)):**
- **Endpoint**: `POST /api/internal/llm-gateway`
- **DeepSeek**: Consultor senior con 5 roles (Arquitecto, Ingeniero de Código, Auditor de Seguridad, Especialista BD, Ingeniero de Refactoring)
- **Gemini RAG**: Base de conocimientos con libros PDF indexados (citas textuales)

**3. Proceso de Decisión:**
1. qwen-orchestrator recibe tu pregunta
2. Si necesita info externa → agrega etiqueta `[[WEB]]` o `[[RAG]]`
3. CLI envía consulta a la API (DeepSeek primero, Gemini como fallback)
4. API retorna información actualizada
5. qwen-validator valida la respuesta final

### 🔄 Routing Inteligente

El sistema usa **Action Tags** para decidir automáticamente:
- `[[WEB]]` → DeepSeek (consultas conceptuales, mejores prácticas, arquitectura, seguridad)
- `[[RAG]]` → Gemini + libros indexados (citas textuales exactas de páginas)
- Sin tags → Respuesta local con Qwen (código, scripts, correcciones)

---

## 🛠️ Instalación y Requisitos

### 📋 Requisitos Previos

1. **Python 3.12+**
2. **Ollama local** (para modelos qwen-orchestrator y qwen-validator)
3. **API RAG externa**: [Repositorio API](https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini)

### 🔧 Instalación Completa

#### 1. Instalar CLI Local
```bash
# Clonar este repositorio
git clone https://github.com/Ponce1969/aplicacion_CLI_con_agentesLocales.git
cd aplicacion_CLI_con_agentesLocales

# Instalar dependencias
pip install uv
uv sync

# Crear modelos en Ollama desde Modelfiles
ollama create qwen-orchestrator -f modelfiles/Modelfile.orchestrator
ollama create qwen-validator -f modelfiles/Modelfile.validator
```

#### 2. Configurar API RAG (Servidor)
```bash
# Clonar y configurar el servidor API
git clone https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini.git
cd agente_hibrido_texto_Kimi_rag_Gemini
# Seguir instrucciones del README para configurar DeepSeek y Gemini
```

#### 3. Configurar Variables de Entorno
```bash
# Copiar archivo de ejemplo
cp .env.example .env

# Editar .env con tus valores
# RAG_BASE_URL=http://localhost:8000  # URL del servidor API
# RAG_API_KEY=tu_clave_api           # Generada con scripts/generar_clave.py
# OLLAMA_BASE_URL=http://localhost:11434  # URL de Ollama
```

### ✅ Verificación de Instalación

```bash
# Verificar conexión con API
uv run python cli.py "test connection"

# Verificar modelos locales
uv run python cli.py --check-models

# Ejecutar tests
uv run pytest
```

---

## 📚 Base de Conocimiento (RAG)

El agente tiene acceso a estos libros técnicos indexados (Gemini RAG):

| ID | Libro | Temas |
|---|---|---|
| 30 | FastAPI Modern Python Web Dev | backend, api, python web |
| 31 | El Programador Pragmático | methodology, career, coding philosophy |
| 32 | Effective Python | best practices, python tips |
| 34 | High Performance Python | optimization, performance, profiling |
| 35 | Architecture Patterns with Python | ddd, architecture, hexagonal |
| 36 | Patrones de Diseño | design patterns, gof, software design |
| 37 | Clean Architecture | architecture, solid, robert martin |
| 38 | Marco de Decisión | decision making, framework |
| 39 | Fluent Python | advanced python, internals, data structures |
| 40 | Designing Data-Intensive Applications | data, distributed systems, kleppmann |

---

## ✅ Estado del Proyecto

| Característica | Estado | Notas |
| :--- | :--- | :--- |
| **Routing Inteligente** | 🟢 Completo | Tags `[[WEB]]` (DeepSeek) y `[[RAG]]` (Gemini). |
| **Validación de Código** | 🟢 Completo | qwen-validator corrige errores automáticamente. |
| **CLI Interactivo** | 🟢 Completo | Soporte para `-i` y argumentos. |
| **Memoria de Chat** | 🟢 Completo | Mantiene el hilo de conversación. |
| **Aprendizaje** | 🟢 Completo | Detecta patrones (backend, routing, code_generation). |
| **Modelfiles** | 🟢 Completo | System prompts horneados en modelos (0 tokens extra). |
| **Tipado Estricto** | 🟢 Completo | Pasa `mypy --strict`. |
| **Feedback UI** | 🟢 Completo | Spinners y mensajes claros con Rich. |

---

## 🤝 Contribuir

¡Las contribuciones son bienvenidas! Por favor lee [CONTRIBUTING.md](CONTRIBUTING.md) para conocer los lineamientos.

### Quick Start para Contribuidores

```bash
# Fork y clonar
git clone https://github.com/tu-usuario/agente.git
cd agente

# Instalar dependencias de desarrollo
uv sync

# Ejecutar tests
uv run pytest

# Verificar calidad de código
uv run mypy .
uv run ruff check .
```

---

## 📄 Licencia

Este proyecto está bajo la licencia MIT. Ver [LICENSE](LICENSE) para más detalles.

---

## � Repositorios Relacionados

- **CLI (Este repositorio)**: [aplicacion_CLI_con_agentesLocales](https://github.com/Ponce1969/aplicacion_CLI_con_agentesLocales)
- **API RAG**: [agente_hibrido_texto_Kimi_rag_Gemini](https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini)

---

## �🙏 Agradecimientos

- [Ollama](https://ollama.ai/) - Modelos locales (Qwen 3.5, Qwen 2.5 Coder)
- [FastAPI](https://fastapi.tiangolo.com/) - Framework del servidor RAG
- [Rich](https://rich.readthedocs.io/) - Terminal UI
- [uv](https://github.com/astral-sh/uv) - Gestor de paquetes rápido
- [Google Gemini](https://gemini.google.com/) - RAG con libros indexados
- [DeepSeek](https://deepseek.com/) - Consultor senior con 5 roles

---

## 📞 Contacto y Soporte

¿Preguntas sobre la conexión CLI ↔ API? 

- **Issues CLI**: [Crear issue aquí](https://github.com/Ponce1969/aplicacion_CLI_con_agentesLocales/issues)
- **Issues API**: [Crear issue en API](https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini/issues)
- **Discussions**: [Discusiones CLI](https://github.com/Ponce1969/aplicacion_CLI_con_agentesLocales/discussions)

---

## 🚀 Guía Rápida para Clonar

### Opción 1: Solo CLI (usa API externa)
```bash
git clone https://github.com/Ponce1969/aplicacion_CLI_con_agentesLocales.git
cd aplicacion_CLI_con_agentesLocales
pip install uv
uv sync
cp .env.example .env
# Configurar RAG_BASE_URL con API pública
```

### Opción 2: CLI + API Local
```bash
# 1. API RAG
git clone https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini.git
cd agente_hibrido_texto_Kimi_rag_Gemini
# Configurar según README

# 2. CLI
git clone https://github.com/Ponce1969/aplicacion_CLI_con_agentesLocales.git
cd aplicacion_CLI_con_agentesLocales
pip install uv
uv sync
cp .env.example .env
# Configurar RAG_BASE_URL=http://localhost:8000
```

---

📁 Estructura del Proyecto
agente/
├── modelfiles/                     # Modelfiles de Ollama (system prompts horneados)
│   ├── Modelfile.orchestrator      # qwen-orchestrator (Qwen 3.5 9B)
│   └── Modelfile.validator         # qwen-validator (Qwen 2.5 Coder 7B)
├── tests/                          # Tests organizados
├── core/                           # Código fuente
│   ├── orchestrator.py             # Orquestador principal (routing, aprendizaje)
│   ├── storage.py                  # SQLite (patrones, cache, soul packages)
│   └── rag_client.py               # Cliente API (DeepSeek + Gemini)
├── agents/
│   ├── principal.py                # Agente principal (Qwen 3.5)
│   └── executor.py                # Agente validador (Qwen Coder)
├── brain/                          # Memoria del sistema
│   ├── temporal_bridge/            # Soul Packages (mitosis entre sesiones)
│   └── metabolism/                 # Presupuesto de tokens
├── utils/
│   └── display.py                  # UI con Rich
├── config.py                       # Configuración centralizada
└── cli.py                          # Punto de entrada

---

## 🗺️ Roadmap Futuro

### Mini-OpenCode (Generación de Proyectos)

Idea: Transformar el CLI de "chatbot que muestra código" a "generador que escribe archivos y crea proyectos".

**Fases propuestas:**

| Fase | Comando | Qué hace | Esfuerzo |
|---|---|---|---|
| 1 | `/save` | Guarda último código generado a archivo | ~50 líneas |
| 2 | `/run` | Ejecuta comandos shell (`uv init`, `python script.py`) | ~40 líneas |
| 3 | `/load` | Lee archivos del directorio actual como contexto | ~30 líneas |
| 4 | `/init` | Scaffolding: carpeta + `uv init` + estructura básica | ~60 líneas |

**RAG local para código generado:**
- Indexar código generado en SQLite FTS5 (sin modelo extra de embeddings)
- Búsqueda por archivo y tema (no por "último generado")
- Cache con TTL por sesión (persiste mientras CLI abierto, RAG persiste entre sesiones)
- Flujo: generar → `/save` → indexar → próxima consulta recupera solo lo relevante

**Limitaciones actuales a resolver:**
- `num_ctx: 4096` — suficiente para scripts, insuficiente para proyectos enteros
- `num_predict: 1024` — limita longitud de código generado
- Velocidad 28-90s — usable para generación, lento para iteración rápida

---

*Actualizado: 04/2026*
