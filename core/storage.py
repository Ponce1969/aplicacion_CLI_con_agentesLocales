"""Sistema de almacenamiento inteligente con SQLite para aprendizaje incremental."""

import sqlite3
from pathlib import Path
from typing import Any

from config import DB_PATH, LEARNING_THRESHOLD


class KnowledgeStorage:
    """Base de datos SQLite para patrones aprendidos y cache inteligente."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_tables()

    def _init_tables(self) -> None:
        """Inicializa las tablas optimizadas para aprendizaje."""
        cursor = self.conn.cursor()

        # Tabla de interacciones
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_query TEXT NOT NULL,
                agent_response TEXT NOT NULL,
                agent_used TEXT NOT NULL,
                pattern_detected TEXT,
                rag_used BOOLEAN DEFAULT 0,
                execution_time REAL,
                success BOOLEAN DEFAULT 1,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de patrones aprendidos (falso fine-tuning)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS learned_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pattern_type TEXT NOT NULL,
                pattern_key TEXT NOT NULL UNIQUE,
                pattern_template TEXT NOT NULL,
                usage_count INTEGER DEFAULT 1,
                success_rate REAL DEFAULT 1.0,
                last_used DATETIME DEFAULT CURRENT_TIMESTAMP,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Tabla de cache de respuestas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS response_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_hash TEXT NOT NULL UNIQUE,
                query_text TEXT NOT NULL,
                cached_response TEXT NOT NULL,
                hit_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_hit DATETIME
            )
        """)

        # Índices para búsquedas rápidas
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_pattern_type
            ON learned_patterns(pattern_type)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_query_hash
            ON response_cache(query_hash)
        """)

        self.conn.commit()

    def save_interaction(
        self,
        user_query: str,
        agent_response: str,
        agent_used: str,
        pattern_detected: str | None = None,
        rag_used: bool = False,
        execution_time: float = 0.0,
        success: bool = True,
    ) -> int:
        """Guarda una interacción para aprendizaje."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO interactions
            (user_query, agent_response, agent_used, pattern_detected,
             rag_used, execution_time, success)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_query,
                agent_response,
                agent_used,
                pattern_detected,
                rag_used,
                execution_time,
                success,
            ),
        )
        self.conn.commit()
        return cursor.lastrowid or 0

    def learn_pattern(
        self, pattern_type: str, pattern_key: str, pattern_template: str
    ) -> bool:
        """Aprende un nuevo patrón o incrementa su uso."""
        cursor = self.conn.cursor()

        # Verificar si ya existe
        cursor.execute(
            "SELECT id, usage_count FROM learned_patterns WHERE pattern_key = ?",
            (pattern_key,),
        )
        existing = cursor.fetchone()

        if existing:
            # Incrementar uso
            cursor.execute(
                """
                UPDATE learned_patterns
                SET usage_count = usage_count + 1,
                    last_used = CURRENT_TIMESTAMP
                WHERE pattern_key = ?
                """,
                (pattern_key,),
            )
        else:
            # Nuevo patrón
            cursor.execute(
                """
                INSERT INTO learned_patterns
                (pattern_type, pattern_key, pattern_template)
                VALUES (?, ?, ?)
                """,
                (pattern_type, pattern_key, pattern_template),
            )

        self.conn.commit()
        return True

    def get_frequent_patterns(
        self, min_usage: int = LEARNING_THRESHOLD
    ) -> list[dict[str, Any]]:
        """Obtiene patrones frecuentes (aprendidos)."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            SELECT pattern_type, pattern_key, pattern_template,
                   usage_count, success_rate
            FROM learned_patterns
            WHERE usage_count >= ?
            ORDER BY usage_count DESC, success_rate DESC
            LIMIT 50
            """,
            (min_usage,),
        )

        return [
            {
                "type": row[0],
                "key": row[1],
                "template": row[2],
                "usage_count": row[3],
                "success_rate": row[4],
            }
            for row in cursor.fetchall()
        ]

    def cache_response(self, query: str, response: str) -> None:
        """Cachea una respuesta para reutilización."""
        query_hash = str(hash(query.lower().strip()))
        cursor = self.conn.cursor()

        cursor.execute(
            """
            INSERT OR REPLACE INTO response_cache
            (query_hash, query_text, cached_response, hit_count, last_hit)
            VALUES (?, ?, ?,
                    COALESCE((SELECT hit_count FROM response_cache WHERE query_hash = ?), 0),
                    CURRENT_TIMESTAMP)
            """,
            (query_hash, query, response, query_hash),
        )
        self.conn.commit()

    def get_cached_response(self, query: str) -> str | None:
        """Obtiene respuesta cacheada si existe."""
        query_hash = str(hash(query.lower().strip()))
        cursor = self.conn.cursor()

        cursor.execute(
            """
            SELECT cached_response FROM response_cache
            WHERE query_hash = ?
            """,
            (query_hash,),
        )
        row = cursor.fetchone()

        if row:
            # Incrementar hit count
            cursor.execute(
                """
                UPDATE response_cache
                SET hit_count = hit_count + 1,
                    last_hit = CURRENT_TIMESTAMP
                WHERE query_hash = ?
                """,
                (query_hash,),
            )
            self.conn.commit()
            return str(row[0])
        return None

    def get_stats(self) -> dict[str, Any]:
        """Obtiene estadísticas del sistema de aprendizaje."""
        cursor = self.conn.cursor()

        # Total interacciones
        cursor.execute("SELECT COUNT(*) FROM interactions")
        total_interactions = cursor.fetchone()[0]

        # Patrones aprendidos
        cursor.execute(
            "SELECT COUNT(*) FROM learned_patterns WHERE usage_count >= ?",
            (LEARNING_THRESHOLD,),
        )
        learned_patterns = cursor.fetchone()[0]

        # Cache hits
        cursor.execute("SELECT SUM(hit_count) FROM response_cache")
        cache_hits = cursor.fetchone()[0] or 0

        # Uso de RAG
        cursor.execute("SELECT COUNT(*) FROM interactions WHERE rag_used = 1")
        rag_usage = cursor.fetchone()[0]

        # Tasa de éxito
        cursor.execute("SELECT AVG(success) FROM interactions")
        success_rate = cursor.fetchone()[0] or 0.0

        return {
            "total_interactions": total_interactions,
            "learned_patterns": learned_patterns,
            "cache_hits": cache_hits,
            "rag_usage": rag_usage,
            "success_rate": round(success_rate * 100, 2),
        }

    def close(self) -> None:
        """Cierra la conexión."""
        self.conn.close()

    def __del__(self) -> None:
        """Limpieza automática."""
        if hasattr(self, "conn"):
            self.conn.close()
