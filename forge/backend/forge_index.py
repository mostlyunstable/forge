"""
forge_index.py — index the Forge codebase into SQLite code_entries table.

Run once (or after big changes) from forge/backend/:
    export PYTHONPATH="$(pwd)/src"
    ../../.venv/bin/python forge_index.py
"""
from __future__ import annotations
import asyncio
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite

# ── Config ────────────────────────────────────────────────────────────────────
# forge_index.py lives at: FORGE AI/forge/backend/forge_index.py
BACKEND_DIR = Path(__file__).parent.resolve()           # FORGE AI/forge/backend
FORGE_DIR   = BACKEND_DIR.parent.resolve()              # FORGE AI/forge
ROOT        = FORGE_DIR.parent.resolve()                # FORGE AI
DB_PATH     = BACKEND_DIR / "forge.db"

INCLUDE_EXTENSIONS = {".py", ".md", ".toml", ".yml", ".yaml", ".txt", ".sh"}
EXCLUDE_DIRS = {
    "__pycache__", ".git", ".venv", "venv", "node_modules",
    ".mypy_cache", ".pytest_cache", "dist", "build", "*.egg-info",
    "alembic",  # skip migration files
}
MAX_CHUNK_CHARS = 2000   # chars per code entry
MIN_CHUNK_CHARS = 80     # skip tiny files

# Index backend/src (all Python) + docs
INDEX_ROOTS = [
    BACKEND_DIR / "src",
    FORGE_DIR / "docs",
]

PROJECT_ID = "00000000-0000-0000-0000-000000000001"  # sentinel project


def should_skip(path: Path) -> bool:
    for part in path.parts:
        if part in EXCLUDE_DIRS or part.endswith(".egg-info"):
            return True
    return False


def chunk_text(text: str, chunk_size: int = MAX_CHUNK_CHARS) -> list[str]:
    """Split large files into overlapping chunks."""
    if len(text) <= chunk_size:
        return [text]
    chunks = []
    step = chunk_size - 200  # 200-char overlap
    for i in range(0, len(text), step):
        chunk = text[i : i + chunk_size]
        if chunk.strip():
            chunks.append(chunk)
    return chunks


async def index_codebase():
    print(f"🔍 Indexing Forge codebase into {DB_PATH} …")
    files_processed = 0
    entries_written = 0

    async with aiosqlite.connect(str(DB_PATH)) as db:
        # Create FTS5 virtual table — simple standalone (not content-linked)
        await db.execute("DROP TABLE IF EXISTS code_entries_fts")
        
        await db.execute("""
            CREATE VIRTUAL TABLE code_entries_fts
            USING fts5(id, name, file_path, content, tokenize='porter ascii')
        """)

        # Wipe old entries for this project so re-indexing is clean
        await db.execute(
            "DELETE FROM code_entries WHERE project_id = ?", (PROJECT_ID,)
        )
        # (No need to DELETE FROM code_entries_fts since we just dropped/recreated it)

        for root_dir in INDEX_ROOTS:
            if not root_dir.exists():
                print(f"  ⚠️  Skipping missing dir: {root_dir}")
                continue

            for file_path in root_dir.rglob("*"):
                if not file_path.is_file():
                    continue
                if should_skip(file_path):
                    continue
                if file_path.suffix not in INCLUDE_EXTENSIONS:
                    continue

                try:
                    text = file_path.read_text(encoding="utf-8", errors="replace")
                except Exception as e:
                    print(f"  ⚠️  Cannot read {file_path}: {e}")
                    continue

                if len(text.strip()) < MIN_CHUNK_CHARS:
                    continue

                # Relative path for display
                try:
                    rel_path = str(file_path.relative_to(ROOT))
                except ValueError:
                    rel_path = str(file_path.relative_to(BACKEND_DIR) if BACKEND_DIR in file_path.parents else file_path)

                chunks = chunk_text(text)
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
                        entry_id, PROJECT_ID, rel_path, entry_type,
                        name, chunk, language,
                        i * (MAX_CHUNK_CHARS // 60), (i + 1) * (MAX_CHUNK_CHARS // 60),
                        now,
                    ))

                    # Insert into FTS
                    await db.execute("""
                        INSERT INTO code_entries_fts (id, name, file_path, content)
                        VALUES (?, ?, ?, ?)
                    """, (entry_id, name, rel_path, chunk))

                    entries_written += 1

                files_processed += 1
                if files_processed % 20 == 0:
                    print(f"  … {files_processed} files indexed")

        await db.commit()

    print(f"✅ Done — {files_processed} files → {entries_written} entries in SQLite")


if __name__ == "__main__":
    asyncio.run(index_codebase())
