import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

class KnowledgeIngester:
    """
    Ingests codebase files, documentation, and ADRs into the Forge SQLite knowledge base.
    """
    def __init__(self, db_path: str, project_id: str = "00000000-0000-0000-0000-000000000001"):
        self.db_path = db_path
        self.project_id = project_id
        
        # Determine paths relative to this file
        # This assumes the file is in src/forge/application/training/
        backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
        forge_dir = backend_dir.parent
        self.root_dir = forge_dir.parent
        
        self.include_extensions = {".py", ".md", ".toml", ".yml", ".yaml", ".txt", ".sh"}
        self.exclude_dirs = {
            "__pycache__", ".git", ".venv", "venv", "node_modules",
            ".mypy_cache", ".pytest_cache", "dist", "build", "*.egg-info",
            "alembic"
        }
        self.max_chunk_chars = 2000
        self.min_chunk_chars = 80
        
        # By default, index backend src and docs
        self.index_roots = [
            backend_dir / "src",
            forge_dir / "docs",
        ]

    def _should_skip(self, path: Path) -> bool:
        for part in path.parts:
            if part in self.exclude_dirs or part.endswith(".egg-info"):
                return True
        return False

    def _chunk_text(self, text: str) -> list[str]:
        if len(text) <= self.max_chunk_chars:
            return [text]
        chunks = []
        step = self.max_chunk_chars - 200  # Overlap
        for i in range(0, len(text), step):
            chunk = text[i : i + self.max_chunk_chars]
            if chunk.strip():
                chunks.append(chunk)
        return chunks

    async def ingest(self) -> dict:
        """
        Runs the ingestion process.
        Returns a dict with statistics.
        """
        files_processed = 0
        entries_written = 0

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("DROP TABLE IF EXISTS code_entries_fts")
            await db.execute("""
                CREATE VIRTUAL TABLE code_entries_fts
                USING fts5(id, name, file_path, content, tokenize='porter ascii')
            """)
            await db.execute("DELETE FROM code_entries WHERE project_id = ?", (self.project_id,))

            for root_dir in self.index_roots:
                if not root_dir.exists():
                    continue

                for file_path in root_dir.rglob("*"):
                    if not file_path.is_file() or self._should_skip(file_path):
                        continue
                    if file_path.suffix not in self.include_extensions:
                        continue

                    try:
                        text = file_path.read_text(encoding="utf-8", errors="replace")
                    except Exception:
                        continue

                    if len(text.strip()) < self.min_chunk_chars:
                        continue

                    try:
                        rel_path = str(file_path.relative_to(self.root_dir))
                    except ValueError:
                        rel_path = str(file_path)

                    chunks = self._chunk_text(text)
                    for i, chunk in enumerate(chunks):
                        entry_id = str(uuid.uuid4())
                        name = f"{file_path.name}" if i == 0 else f"{file_path.name}:chunk{i+1}"
                        entry_type = "file" if file_path.suffix == ".py" else "doc"
                        language = "python" if file_path.suffix == ".py" else "markdown"
                        now = datetime.now(timezone.utc).isoformat()

                        await db.execute("""
                            INSERT INTO code_entries
                                (id, project_id, file_path, entry_type, name, content,
                                 language, start_line, end_line, metadata, created_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, '{}', ?)
                        """, (
                            entry_id, self.project_id, rel_path, entry_type,
                            name, chunk, language,
                            i * (self.max_chunk_chars // 60), (i + 1) * (self.max_chunk_chars // 60),
                            now,
                        ))

                        await db.execute("""
                            INSERT INTO code_entries_fts (id, name, file_path, content)
                            VALUES (?, ?, ?, ?)
                        """, (entry_id, name, rel_path, chunk))
                        entries_written += 1

                    files_processed += 1

            await db.commit()

        return {
            "files_processed": files_processed,
            "entries_written": entries_written
        }
