"""SQLite Embedding Cache."""
import sqlite3
import json
import hashlib
from typing import Optional
from contextlib import contextmanager

from forge.config.settings import get_settings


class SQLiteEmbeddingCache:
    """Caches embeddings to prevent redundant LLM API calls."""

    def __init__(self, db_path: str = "forge_cache.db") -> None:
        self.db_path = db_path
        self._init_db()

    @contextmanager
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_db(self):
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS embeddings (
                    hash TEXT PRIMARY KEY,
                    model_name TEXT NOT NULL,
                    model_version TEXT,
                    embedding JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def get(self, content: str, model_name: str, model_version: str) -> Optional[list[float]]:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT embedding FROM embeddings WHERE hash = ? AND model_name = ? AND model_version = ?",
                (content_hash, model_name, model_version)
            )
            row = cursor.fetchone()
            if row:
                return json.loads(row[0])
        return None

    def set(self, content: str, model_name: str, model_version: str, embedding: list[float]) -> None:
        content_hash = hashlib.sha256(content.encode()).hexdigest()
        with self._get_connection() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO embeddings (hash, model_name, model_version, embedding)
                VALUES (?, ?, ?, ?)
                """,
                (content_hash, model_name, model_version, json.dumps(embedding))
            )
            conn.commit()

    def clear(self):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM embeddings")
            conn.commit()
