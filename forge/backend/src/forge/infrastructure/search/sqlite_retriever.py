"""
SqliteRetriever — fast keyword search over code_entries using SQLite FTS5.

No Qdrant, no embeddings needed. Works out of the box.
"""
from __future__ import annotations

import re
from pathlib import Path

import aiosqlite

DB_PATH = Path(__file__).parent.parent.parent.parent.parent.parent / "forge" / "backend" / "forge.db"
PROJECT_ID = "00000000-0000-0000-0000-000000000001"
MAX_RESULTS = 8
MAX_CONTENT_CHARS = 800  # truncate each snippet for context budget


def _resolve_db() -> Path:
    """Find forge.db relative to this file at runtime."""
    here = Path(__file__).resolve()
    # Walk up until we find forge/backend/forge.db
    for parent in here.parents:
        candidate = parent / "forge" / "backend" / "forge.db"
        if candidate.exists():
            return candidate
        # Also try current dir
        candidate2 = parent / "forge.db"
        if candidate2.exists():
            return candidate2
    # Fallback: next to this file's package root
    return here.parent / "forge.db"


class SqliteRetriever:
    """
    Retrieves relevant code/doc snippets from SQLite FTS5 index.

    Usage:
        retriever = SqliteRetriever()
        results = await retriever.retrieve("ConversationRepository save method")
    """

    def __init__(self, db_path: str | Path | None = None):
        self._db_path = Path(db_path) if db_path else _resolve_db()

    async def retrieve(self, query: str, top_k: int = MAX_RESULTS) -> list[dict]:
        """
        Search the indexed codebase for chunks relevant to `query`.

        Returns list of dicts: {file_path, name, content, score}
        """
        if not self._db_path.exists():
            return []

        # Build FTS query: each word as a separate term (AND semantics)
        clean = re.sub(r"[^\w\s]", " ", query)
        words = [w for w in clean.split() if len(w) > 2]
        if not words:
            return []

        # Try exact phrase first, fall back to individual terms
        fts_query = " ".join(words)

        async with aiosqlite.connect(str(self._db_path)) as db:
            db.row_factory = aiosqlite.Row

            # Check FTS table exists
            cur = await db.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='code_entries_fts'"
            )
            if not await cur.fetchone():
                # FTS table not yet built — fall back to LIKE search
                return await self._like_search(db, words, top_k)

            try:
                cur = await db.execute(
                    """
                    SELECT
                        c.id,
                        c.file_path,
                        c.name,
                        c.content,
                        rank
                    FROM code_entries_fts f
                    JOIN code_entries c ON c.id = f.id
                    WHERE code_entries_fts MATCH ?
                      AND c.project_id = ?
                    ORDER BY rank
                    LIMIT ?
                    """,
                    (fts_query, PROJECT_ID, top_k),
                )
                rows = await cur.fetchall()
            except Exception:
                # FTS match syntax error — fall back
                return await self._like_search(db, words, top_k)

        if not rows:
            # No FTS hits → fall back to LIKE
            async with aiosqlite.connect(str(self._db_path)) as db2:
                db2.row_factory = aiosqlite.Row
                return await self._like_search(db2, words, top_k)

        return [
            {
                "file_path": row["file_path"],
                "name": row["name"],
                "content": (row["content"] or "")[:MAX_CONTENT_CHARS],
                "score": abs(row["rank"]) if row["rank"] else 1.0,
            }
            for row in rows
        ]

    async def _like_search(self, db, words: list[str], top_k: int) -> list[dict]:
        """LIKE-based fallback when FTS table isn't available."""
        conditions = " AND ".join(
            f"(content LIKE ? OR name LIKE ? OR file_path LIKE ?)"
            for _ in words
        )
        params: list[str] = []
        for w in words:
            pat = f"%{w}%"
            params.extend([pat, pat, pat])
        params.append(PROJECT_ID)
        params.append(top_k)

        cur = await db.execute(
            f"""
            SELECT file_path, name, content
            FROM code_entries
            WHERE {conditions}
              AND project_id = ?
            LIMIT ?
            """,
            params,
        )
        rows = await cur.fetchall()
        return [
            {
                "file_path": row[0],
                "name": row[1],
                "content": (row[2] or "")[:MAX_CONTENT_CHARS],
                "score": 1.0,
            }
            for row in rows
        ]

    def format_for_llm(self, results: list[dict]) -> str:
        """Format retrieved snippets into a readable string for the LLM."""
        if not results:
            return ""
        parts = []
        for r in results:
            parts.append(
                f"### {r['file_path']} ({r['name']})\n```\n{r['content']}\n```"
            )
        return "\n\n".join(parts)
