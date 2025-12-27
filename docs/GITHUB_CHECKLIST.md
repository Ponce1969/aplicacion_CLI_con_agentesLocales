# ✅ Checklist de Pre-Publicación en GitHub

**Fecha:** 21 Diciembre 2025  
**Versión:** 1.0.0

---

## 🔒 Seguridad (CRÍTICO)

- [x] `.env` está en `.gitignore`
- [x] `.env.local` y `.env.*.local` están en `.gitignore`
- [x] No hay API Keys hardcodeadas en el código
- [x] No hay passwords o tokens en el código
- [x] **Verificar que NO existe archivo `.env` con secretos reales**
- [x] **Ejecutar:** `git status` y confirmar que `.env` NO aparece
- [x] `.env.example` existe y está documentado
- [x] Archivos de base de datos (`*.db`) están en `.gitignore`

### Comando de Verificación de Seguridad

```bash
# Verificar que .env no está trackeado
git ls-files | grep -E "\.env$"
# Debe devolver: (nada)

# Verificar que no hay secretos en el código
git grep -E "(password|secret|token|key)\s*=\s*['\"][a-zA-Z0-9]{20,}"
# Debe devolver: (nada o solo comentarios)
```

---

## 📄 Documentación

- [x] `README.md` actualizado con badges
- [x] `README.md` tiene instrucciones claras de instalación
- [x] `README.md` tiene ejemplos de uso
- [x] `LICENSE` creado (MIT)
- [x] `CONTRIBUTING.md` creado
- [x] `.env.example` documentado
- [x] `docs/comportamiento-routing.md` creado
- [x] `docs/api-cli-contract.md` existe

---

## 🧪 Calidad de Código

- [x] **Ejecutar:** `uv run pytest` (todos los tests pasan)
- [x] **Ejecutar:** `uv run mypy .` (sin errores)
- [x] **Ejecutar:** `uv run ruff check .` (sin warnings críticos)
- [x] **Ejecutar:** `uv run ruff format .` (código formateado)

### Comandos de Verificación

```bash
# Tests
uv run pytest -v

# Type checking
uv run mypy . --config-file pyproject.toml

# Linting
uv run ruff check .

# Formateo
uv run ruff format .
```

---

## 📦 Estructura del Proyecto

- [x] `.gitignore` completo y actualizado
- [x] `pyproject.toml` con dependencias correctas
- [x] `uv.lock` actualizado
- [x] Estructura de carpetas clara (`core/`, `agents/`, `storage/`, `tests/`)
- [x] No hay archivos `__pycache__/` o `.pyc` trackeados

---

## 🔍 Revisión de Código

- [x] No hay URLs personales hardcodeadas (excepto en `config.py` como default)
- [x] No hay paths absolutos hardcodeados
- [x] No hay `print()` de debug olvidados (usar logging)
- [x] No hay `TODO` o `FIXME` críticos sin resolver
- [x] Código sigue arquitectura hexagonal
- [x] Type hints en todas las funciones públicas

---

## 🚀 Preparación del Repositorio

### Antes del Primer Push

```bash
# 1. Verificar estado de git
git status

# 2. Verificar que .env NO está en staging
git ls-files --stage | grep .env
# Debe devolver: (nada)

# 3. Agregar todos los archivos
git add .

# 4. Verificar qué se va a commitear
git status

# 5. Commit inicial
git commit -m "feat: initial commit - Sistema de Agentes Híbrido v1.0.0"

# 6. Crear tag de versión
git tag -a v1.0.0 -m "Release v1.0.0 - Sistema de Agentes Híbrido"
```

### Crear Repositorio en GitHub

1. Ve a https://github.com/new
2. Nombre: `aplicacion_CLI_con_agentesLocales` (o el que prefieras)
3. Descripción: "CLI inteligente con modelos locales (Llama 3.1, Qwen 2.5) que se conecta a API RAG (Gemini + Kimi) para consultas complejas"
4. **Público** (para recibir estrellas)
5. **NO** inicializar con README (ya tienes uno)
6. **NO** agregar .gitignore (ya tienes uno)
7. **NO** agregar licencia (ya tienes una)

### Push al Repositorio

```bash
# Agregar remote
git remote add origin https://github.com/Ponce1969/aplicacion_CLI_con_agentesLocales.git

# Push inicial con tags
git push -u origin main
git push --tags
```

---

## 🎨 Configuración de GitHub

### Después del Push

1. **Descripción del Repositorio:**
   - Agregar descripción corta
   - Agregar topics: `python`, `ai`, `llm`, `cli`, `rag`, `ollama`, `agents`

2. **README.md:**
   - Verificar que se ve bien en GitHub
   - Verificar que los badges funcionan

3. **Issues:**
   - Habilitar Issues
   - Crear templates (opcional):
     - Bug report
     - Feature request

4. **Discussions:**
   - Habilitar Discussions (opcional)
   - Crear categorías: Q&A, Ideas, Show and tell

5. **GitHub Actions (opcional):**
   - CI para ejecutar tests automáticamente
   - Linting automático

---

## 🔐 Verificación Final de Seguridad

### ANTES de hacer público el repositorio

```bash
# Verificar historial de commits por secretos
git log --all --full-history --source -- .env

# Buscar secretos en todo el historial
git grep -E "(password|secret|token|key)\s*=\s*['\"][a-zA-Z0-9]{20,}" $(git rev-list --all)

# Verificar archivos grandes (>50MB)
git rev-list --objects --all | git cat-file --batch-check='%(objecttype) %(objectname) %(objectsize) %(rest)' | awk '/^blob/ {print substr($0,6)}' | sort -n -k 2 | tail -10
```

**Si encuentras secretos en el historial:**
- **NO** hagas push
- Usa `git filter-branch` o `BFG Repo-Cleaner` para limpiar el historial
- Regenera todos los secretos expuestos

---

## 📢 Promoción (Opcional)

Después de publicar:

1. **Tweet/Post:**
   - Compartir en redes sociales
   - Usar hashtags: #Python #AI #LLM #OpenSource

2. **Reddit:**
   - r/Python
   - r/LocalLLaMA
   - r/opensource

3. **Dev.to / Medium:**
   - Escribir artículo explicando el proyecto

4. **Awesome Lists:**
   - Buscar "awesome-python-ai" o similares
   - Hacer PR para agregar tu proyecto

---

## ✅ Checklist Final

Antes de hacer el repositorio público:

- [x] Todos los tests pasan
- [x] Mypy sin errores
- [x] Ruff sin warnings críticos
- [x] `.env` NO está en el repositorio
- [x] No hay secretos en el historial de git
- [ ] README.md se ve bien en GitHub
- [x] LICENSE existe
- [x] CONTRIBUTING.md existe
- [x] `.env.example` está documentado
- [ ] Descripción y topics configurados en GitHub
- [ ] Primera release (v1.0.0) taggeada

---

## 🚨 Si Algo Sale Mal

### Si accidentalmente subes un secreto:

1. **Inmediatamente:**
   ```bash
   # Eliminar el archivo del último commit
   git rm --cached .env
   git commit --amend -m "fix: remove .env file"
   git push --force
   ```

2. **Regenerar el secreto expuesto:**
   - Crear nueva API Key
   - Actualizar `.env` local
   - **NUNCA** reutilizar un secreto expuesto

3. **Limpiar historial (si el secreto está en commits antiguos):**
   ```bash
   # Usar BFG Repo-Cleaner (más seguro)
   bfg --delete-files .env
   git reflog expire --expire=now --all
   git gc --prune=now --aggressive
   git push --force
   ```

---

## 📝 Notas Finales

- **Privacidad:** Si el servidor RAG es personal, considera no exponer la URL o hacerla configurable
- **Mantenimiento:** Responde a Issues y PRs de forma profesional
- **Actualizaciones:** Mantén el proyecto actualizado con nuevas versiones de dependencias
- **Comunidad:** Sé receptivo a contribuciones y feedback

---

**¡Listo para GitHub!** 🎉

Una vez completado este checklist, tu proyecto estará listo para recibir estrellas ⭐
