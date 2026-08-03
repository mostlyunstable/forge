"""
forge_index.py — index the Forge codebase into SQLite code_entries table.

Run once (or after big changes) from forge/backend/:
    export PYTHONPATH="$(pwd)/src"
    ../../.venv/bin/python forge_index.py
"""
"""
forge_index.py — index the Forge codebase into SQLite code_entries table.

Run once (or after big changes) from forge/backend/:
    export PYTHONPATH="$(pwd)/src"
    ../../.venv/bin/python forge_index.py
"""
import asyncio
from pathlib import Path
from forge.application.training.knowledge_ingester import KnowledgeIngester

async def index_codebase():
    db_path = str(Path(__file__).parent.resolve() / "forge.db")
    print(f"🔍 Indexing Forge codebase into {db_path} …")
    
    ingester = KnowledgeIngester(db_path=db_path)
    stats = await ingester.ingest()
    
    print(f"✅ Done — {stats['files_processed']} files → {stats['entries_written']} entries in SQLite")

if __name__ == "__main__":
    asyncio.run(index_codebase())
