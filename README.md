# 🤖 Sistema de Agentes Híbrido (CLI & RAG)

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Type Checked: mypy](https://img.shields.io/badge/type_checked-mypy-blue.svg)](http://mypy-lang.org/)
[![Code style: ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)

CLI inteligente que combina **modelos locales** (Llama 3.1, Qwen 2.5) con **API externa** de RAG (Gemini + Kimi). Cuando los modelos locales tienen dudas, consultan automáticamente la API para obtener información actualizada.

> **🔗 Conexión Principal:** Este CLI se conecta a [este repositorio API](https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini) que proporciona:
> - 📚 **RAG con Gemini**: Base de conocimientos técnicos indexados
> - 🌐 **Web Search con Kimi**: Búsqueda en tiempo real
> - ⚡ **API REST**: Endpoint `/query` para consultas externas

> **🎯 Características:**
> - 🧠 **Llama 3.1**: Orquestador principal (decide cuándo usar RAG)
> - ✅ **Qwen 2.5**: Validador de código (revisa y corrige respuestas)
> - 🔄 **Routing automático**: Etiquetas `[[RAG]]` activan la API cuando es necesario
> - 💬 **Modo interactivo** con memoria persistente
> - 🔍 **Type-safe** con mypy --strict

> **🎯 Características Principales:**
> - 🚀 Respuestas rápidas con modelos locales (Ollama)
> - 📚 Acceso a base de conocimiento técnica (RAG)
> - 🌐 Búsqueda web en tiempo real (Kimi)
> - 🔍 Routing inteligente basado en contexto
> - ✅ Validación automática de código
> - 💬 Modo interactivo con memoria de conversación
> - 🎨 Arquitectura hexagonal limpia
> - 🔒 Type-safe con mypy --strict

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
CLI (Local)                    API (Remota)
├─ Llama 3.1 (Orquestador) ──→ ├─ Gemini RAG
├─ Qwen 2.5 (Validador)       ├─ Kimi Web Search
└─ Rich CLI (UI)              └─ FastAPI Server
```

**1. Modelos Locales (CLI):**
- **Llama 3.1**: Analiza tu consulta y decide si necesita información externa
- **Qwen 2.5**: Valida y mejora el código generado

**2. API Externa ([Repositorio API](https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini)):**
- **Endpoint**: `POST /query`
- **Gemini**: Base de conocimientos técnicos (libros, documentación)
- **Kimi**: Búsqueda web en tiempo real

**3. Proceso de Decisión:**
1. Llama 3.1 recibe tu pregunta
2. Si detecta necesidad de RAG → agrega etiqueta `[[RAG]]`
3. CLI envía consulta a la API
4. API retorna información actualizada
5. Qwen 2.5 valida la respuesta final

### 🔄 Routing Inteligente

El sistema usa **Action Tags** para decidir automáticamente:
- `[[RAG]]` → Consulta base de conocimientos (Gemini)
- `[[WEB]]` → Búsqueda web en tiempo real (Kimi)
- Sin tags → Respuesta local con modelos

---

## 🛠️ Instalación y Requisitos

### 📋 Requisitos Previos

1. **Python 3.12+**
2. **Ollama local** (para modelos Llama 3.1 y Qwen 2.5)
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
```

#### 2. Configurar API RAG (Servidor)
```bash
# Clonar y configurar el servidor API
git clone https://github.com/Ponce1969/agente_hibrido_texto_Kimi_rag_Gemini.git
cd agente_hibrido_texto_Kimi_rag_Gemini
# Seguir instrucciones del README para configurar Gemini y Kimi
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

- [Ollama](https://ollama.ai/) - Modelos locales (Llama 3.1, Qwen 2.5)
- [FastAPI](https://fastapi.tiangolo.com/) - Framework del servidor RAG
- [Rich](https://rich.readthedocs.io/) - Terminal UI
- [uv](https://github.com/astral-sh/uv) - Gestor de paquetes rápido
- [Google Gemini](https://gemini.google.com/) - RAG y procesamiento
- [Kimi AI](https://kimi.moonshot.cn/) - Web search

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

📁 Estructura Final Organizada
agente/
├── tests/                          # ✅ Tests organizados
│   ├── test_rag_client_refactor.py
│   ├── test_rag_gemini.py
│   └── test_session_fix.py
├── core/                           # Código fuente
│   ├── orchestrator.py
│   ├── storage.py
│   └── rag_client.py
├── agents/
│   ├── principal.py
│   └── executor.py
├── brain/                          # Memoria del sistema
│   ├── temporal_bridge/
│   └── metabolism/
└── cli.py                          # Punto de entrada



---

*Actualizado: 21/12/2025*
