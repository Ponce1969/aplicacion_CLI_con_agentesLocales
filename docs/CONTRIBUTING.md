# 🤝 Contribuyendo al Sistema de Agentes Inteligentes

¡Gracias por tu interés en contribuir! Este documento te guiará en el proceso.

---

## 📋 Tabla de Contenidos

- [Código de Conducta](#código-de-conducta)
- [¿Cómo Puedo Contribuir?](#cómo-puedo-contribuir)
- [Configuración del Entorno de Desarrollo](#configuración-del-entorno-de-desarrollo)
- [Estándares de Código](#estándares-de-código)
- [Proceso de Pull Request](#proceso-de-pull-request)

---

## 📜 Código de Conducta

Este proyecto se adhiere a un código de conducta profesional y respetuoso. Al participar, te comprometes a mantener un ambiente inclusivo y colaborativo.

---

## 🎯 ¿Cómo Puedo Contribuir?

### Reportar Bugs

Si encuentras un bug, por favor abre un **Issue** con:
- Descripción clara del problema
- Pasos para reproducirlo
- Comportamiento esperado vs. comportamiento actual
- Versión de Python y sistema operativo
- Logs relevantes (sin exponer secretos)

### Sugerir Mejoras

Para nuevas funcionalidades o mejoras:
- Abre un **Issue** describiendo la propuesta
- Explica el caso de uso y beneficios
- Discute el diseño antes de implementar

### Contribuir Código

1. **Fork** el repositorio
2. Crea una **rama** para tu feature: `git checkout -b feature/mi-mejora`
3. Implementa tus cambios siguiendo los [estándares de código](#estándares-de-código)
4. Escribe **tests** para tu código
5. Asegúrate de que todos los tests pasen
6. Haz **commit** con mensajes descriptivos
7. Abre un **Pull Request**

---

## 🛠️ Configuración del Entorno de Desarrollo

### Requisitos Previos

- Python 3.12+
- [uv](https://github.com/astral-sh/uv) (gestor de paquetes)
- [Ollama](https://ollama.ai/) con modelos `qwen-orchestrator` (Qwen 3.5 9B) y `qwen-validator` (Qwen 2.5 Coder 7B)

### Instalación

```bash
# Clonar el repositorio
git clone https://github.com/tu-usuario/agente.git
cd agente

# Instalar dependencias
uv sync

# Copiar configuración de ejemplo
cp .env.example .env

# Editar .env con tus valores
# RAG_API_KEY, RAG_BASE_URL, etc.

# Verificar instalación
uv run python -m pytest
uv run mypy .
uv run ruff check .
```

---

## 📐 Estándares de Código

### Type Hints Estrictos

Este proyecto usa **type hints estrictos** con `mypy --strict`:

```python
# ✅ Correcto
def procesar_query(query: str, timeout: float = 30.0) -> dict[str, Any]:
    ...

# ❌ Incorrecto
def procesar_query(query, timeout=30):
    ...
```

### Linting con Ruff

Usamos `ruff` para mantener el código limpio:

```bash
# Verificar código
uv run ruff check .

# Auto-formatear
uv run ruff format .
```

### Estilo de Código

- **PEP 8** como base
- **Docstrings** en funciones públicas (estilo Google)
- **Nombres descriptivos** (no abreviaturas crípticas)
- **Funciones pequeñas** (máximo 50 líneas)
- **Separación de responsabilidades** (arquitectura hexagonal)

### Ejemplo de Docstring

```python
def analyze_query(query: str, context: str | None = None) -> dict[str, Any]:
    """
    Analiza una consulta del usuario y determina la estrategia de respuesta.

    Args:
        query: La consulta del usuario.
        context: Contexto previo de la conversación (opcional).

    Returns:
        Un diccionario con:
        - intent: "local", "rag", o "web"
        - confidence: float entre 0 y 1
        - response: str con la respuesta generada

    Raises:
        ValueError: Si la query está vacía.
    """
    ...
```

---

## 🧪 Tests

### Escribir Tests

Todos los cambios deben incluir tests:

```python
# tests/test_mi_feature.py
import pytest
from core.mi_modulo import mi_funcion

def test_mi_funcion_caso_basico() -> None:
    """Test del caso básico de mi_funcion."""
    resultado = mi_funcion("input")
    assert resultado == "expected_output"

def test_mi_funcion_caso_error() -> None:
    """Test que mi_funcion lanza error cuando debe."""
    with pytest.raises(ValueError):
        mi_funcion("")
```

### Ejecutar Tests

```bash
# Todos los tests
uv run pytest

# Con cobertura
uv run pytest --cov=core --cov-report=html

# Tests específicos
uv run pytest tests/test_orchestrator.py -v
```

---

## 🔄 Proceso de Pull Request

### Antes de Abrir el PR

1. ✅ Todos los tests pasan: `uv run pytest`
2. ✅ Mypy sin errores: `uv run mypy .`
3. ✅ Ruff sin warnings: `uv run ruff check .`
4. ✅ Código formateado: `uv run ruff format .`
5. ✅ Commits descriptivos y atómicos

### Mensaje de Commit

Usa [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: agregar soporte para streaming de respuestas
fix: corregir timeout en llamadas RAG
docs: actualizar README con ejemplos de uso
test: agregar tests para orchestrator
refactor: simplificar lógica de routing
```

### Descripción del PR

Tu PR debe incluir:

- **Título claro** (ej: "feat: agregar modo de debug")
- **Descripción** de qué cambia y por qué
- **Issue relacionado** (si aplica): "Closes #123"
- **Checklist**:
  ```markdown
  - [x] Tests agregados/actualizados
  - [x] Documentación actualizada
  - [x] Mypy y Ruff pasan
  - [x] Probado localmente
  ```

### Revisión de Código

- Sé receptivo a feedback
- Responde a comentarios de forma constructiva
- Haz cambios solicitados en commits separados
- No hagas force-push después de la revisión inicial

---

## 🎨 Arquitectura del Proyecto

Este proyecto sigue **Arquitectura Hexagonal** (Ports & Adapters):

```
core/               # Lógica de dominio (sin dependencias externas)
├── orchestrator.py # Coordinación de agentes
├── rag_client.py   # Cliente RAG (puerto)
└── exceptions.py   # Excepciones de dominio

agents/             # Agentes especializados
├── principal.py    # qwen-orchestrator (routing)
└── executor.py     # qwen-validator (validación)

storage/            # Persistencia (adaptador)
└── local_storage.py

cli.py              # Interfaz de usuario (adaptador)
```

**Reglas:**
- `core/` no debe importar de `agents/` o `storage/`
- Usa inyección de dependencias
- Interfaces claras entre capas

---

## 📚 Recursos Útiles

- [Documentación de Type Hints](https://docs.python.org/3/library/typing.html)
- [Guía de Mypy](https://mypy.readthedocs.io/)
- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [Pytest Best Practices](https://docs.pytest.org/en/stable/goodpractices.html)
- [Arquitectura Hexagonal](https://alistair.cockburn.us/hexagonal-architecture/)

---

## 💬 ¿Preguntas?

Si tienes dudas, abre un **Issue** con la etiqueta `question` o contacta a los maintainers.

---

**¡Gracias por contribuir!** 🎉
