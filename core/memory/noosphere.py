"""SimpleSoulRetriever: Motor de búsqueda semántica ligero para Soul Packages.

Implementa búsqueda por similitud de cosenos usando TF-IDF, sin dependencias ML pesadas.
Optimizado para <100 Soul Packages con latencia <100ms.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class SimpleSoulRetriever:
    """Recuperador de experiencia de Soul Packages anteriores usando TF-IDF.

    Indexa los Soul Packages en brain/temporal_bridge/ y permite búsqueda
    semántica ligera sin modelos de Deep Learning.
    """

    def __init__(self, brain_path: Path) -> None:
        """Inicializa el recuperador.

        Args:
            brain_path: Ruta al directorio brain/
        """
        self.brain_path = brain_path
        self.temporal_bridge_path = brain_path / "temporal_bridge"
        self.soul_contents: list[dict[str, Any]] = []
        self.soul_vectors: Any = None
        self.vectorizer: Any = None

        if not SKLEARN_AVAILABLE:
            raise ImportError(
                "scikit-learn no está instalado. "
                "Ejecuta: uv add scikit-learn"
            )

        self.vectorizer = TfidfVectorizer(
            max_features=500,
            stop_words='english',
            ngram_range=(1, 2),  # Unigrams y bigrams para capturar "Circuit Breaker"
            min_df=1
        )

    def index_past_lives(self) -> int:
        """Indexa todos los Soul Packages disponibles.

        Returns:
            Número de Soul Packages indexados.
        """
        self.soul_contents = []

        # Buscar todos los archivos soul_package_*.md
        soul_files = sorted(self.temporal_bridge_path.glob("soul_package_*.md"))

        for soul_file in soul_files:
            try:
                content = soul_file.read_text(encoding="utf-8")
                metadata_file = self.temporal_bridge_path / soul_file.name.replace(
                    "soul_package_", "soul_metadata_"
                ).replace(".md", ".json")

                # Cargar metadata si existe
                metadata = {}
                if metadata_file.exists():
                    metadata = json.loads(metadata_file.read_text(encoding="utf-8"))

                # Parsear el Soul Package
                parsed = self._parse_soul_package(content)
                parsed["file_path"] = str(soul_file)
                parsed["timestamp"] = self._extract_timestamp(soul_file.name)
                parsed["tags"] = metadata.get("tags", [])

                self.soul_contents.append(parsed)
            except Exception as e:
                # Log pero no fallar si un archivo está corrupto
                print(f"⚠️  Error indexando {soul_file.name}: {e}")
                continue

        # Vectorizar solo si hay contenido
        if self.soul_contents:
            texts = [self._build_searchable_text(soul) for soul in self.soul_contents]
            self.soul_vectors = self.vectorizer.fit_transform(texts)

        return len(self.soul_contents)

    def query_experience(
        self,
        query: str | list[str],
        top_k: int = 2,
        min_similarity: float = 0.3,
        tags: list[str] | None = None
    ) -> list[dict[str, Any]]:
        """Busca experiencia relevante en Soul Packages anteriores.

        Args:
            query: Consulta de búsqueda (string o lista de strings para pending_tasks)
            top_k: Número máximo de resultados a retornar
            min_similarity: Similitud mínima requerida (0.0-1.0)
            tags: Filtrar solo Soul Packages con estos tags

        Returns:
            Lista de Soul Packages relevantes con score de similitud.
        """
        if not self.soul_contents or self.soul_vectors is None:
            return []

        # Convertir query a string si es lista
        if isinstance(query, list):
            query = " ".join(query)

        # Filtrar por tags si se especifican
        filtered_indices = list(range(len(self.soul_contents)))
        if tags:
            filtered_indices = [
                i for i, soul in enumerate(self.soul_contents)
                if any(tag in soul.get("tags", []) for tag in tags)
            ]

        if not filtered_indices:
            return []

        # Vectorizar query
        query_vec = self.vectorizer.transform([query])

        # Calcular similitud solo con los filtrados
        filtered_vectors = self.soul_vectors[filtered_indices]
        similarities = cosine_similarity(query_vec, filtered_vectors)[0]

        # Obtener top_k con similitud > min_similarity
        results = []
        for idx, similarity in enumerate(similarities):
            if similarity >= min_similarity:
                original_idx = filtered_indices[idx]
                soul = self.soul_contents[original_idx].copy()
                soul["similarity_score"] = float(similarity)
                results.append(soul)

        # Ordenar por similitud descendente
        results.sort(key=lambda x: x["similarity_score"], reverse=True)

        return results[:top_k]

    def _parse_soul_package(self, content: str) -> dict[str, Any]:
        """Parsea un Soul Package en formato Markdown.

        Args:
            content: Contenido del archivo soul_package.md

        Returns:
            Dict con las secciones parseadas.
        """
        parsed: dict[str, Any] = {
            "identity": {},
            "witness": {},
            "compressed_memory": [],
            "pending_tasks": [],
            "tags": []
        }

        lines = content.split("\n")
        current_section = None

        for line in lines:
            line_stripped = line.strip()

            # Detectar secciones
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
            elif (line_stripped.startswith("- ") or line_stripped.startswith("* ")) and current_section:
                content_line = line_stripped[2:].strip()

                if current_section == "identity":
                    if ":" in content_line:
                        key, value = content_line.split(":", 1)
                        parsed["identity"][key.strip().lower().replace(" ", "_")] = value.strip()
                elif current_section == "witness":
                    if ":" in content_line:
                        key, value = content_line.split(":", 1)
                        parsed["witness"][key.strip().lower().replace(" ", "_")] = value.strip()
                elif current_section == "compressed_memory":
                    parsed["compressed_memory"].append(content_line)
                elif current_section == "pending_tasks":
                    parsed["pending_tasks"].append(content_line)
                elif current_section == "tags":
                    # Tags pueden estar separados por comas
                    tags = [t.strip() for t in content_line.split(",")]
                    parsed["tags"].extend(tags)

        return parsed

    def _build_searchable_text(self, soul: dict[str, Any]) -> str:
        """Construye texto searchable de un Soul Package.

        Args:
            soul: Soul Package parseado

        Returns:
            String concatenado de las secciones relevantes.
        """
        parts = []

        # Identity
        if soul.get("identity"):
            parts.append(" ".join(soul["identity"].values()))

        # Compressed Memory (peso mayor)
        if soul.get("compressed_memory"):
            memory_text = " ".join(soul["compressed_memory"])
            parts.append(memory_text * 2)  # Duplicar para dar más peso

        # Pending Tasks
        if soul.get("pending_tasks"):
            parts.append(" ".join(soul["pending_tasks"]))

        # Tags (peso mayor para keywords)
        if soul.get("tags"):
            tags_text = " ".join(soul["tags"])
            parts.append(tags_text * 3)  # Triplicar para dar más peso

        return " ".join(parts)

    def _extract_timestamp(self, filename: str) -> str:
        """Extrae timestamp del nombre del archivo.

        Args:
            filename: Nombre del archivo (ej: soul_package_20251222_210441.md)

        Returns:
            Timestamp en formato ISO.
        """
        match = re.search(r"(\d{8})_(\d{6})", filename)
        if match:
            date_str = match.group(1)
            time_str = match.group(2)
            dt = datetime.strptime(f"{date_str}{time_str}", "%Y%m%d%H%M%S")
            return dt.isoformat()
        return ""

    def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas del índice.

        Returns:
            Dict con estadísticas del Noosphere.
        """
        return {
            "total_souls": len(self.soul_contents),
            "indexed": self.soul_vectors is not None,
            "vocabulary_size": len(self.vectorizer.vocabulary_) if self.vectorizer and hasattr(self.vectorizer, 'vocabulary_') else 0,
            "oldest_soul": min((s["timestamp"] for s in self.soul_contents), default=None),
            "newest_soul": max((s["timestamp"] for s in self.soul_contents), default=None)
        }
