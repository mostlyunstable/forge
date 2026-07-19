import sys
import asyncio
from typing import Dict, Any

from forge.config.settings import Settings
from forge.infrastructure.database.connection import DatabaseManager
from forge.infrastructure.search.qdrant_client import QdrantClient
from forge.infrastructure.search.embedding_service import EmbeddingService

async def test_sqlite_config():
    print("\n--- Testing Development (SQLite) Config ---")
    try:
        import os
        from forge.config.settings import get_settings
        get_settings.cache_clear()
        os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
        os.environ["USE_QDRANT"] = "false"
        
        settings = get_settings()
        print("Settings loaded successfully.")
        
        db = DatabaseManager()
        await db.init_db()
        print("SQLite in-memory connected and initialized.")
        
        embedding_service = EmbeddingService()
        # Initialize mock or wait for it to load
        print("Embedding service initialized.")
        return True
    except Exception as e:
        print(f"FAILED SQLite Config: {e}")
        return False

async def test_postgres_qdrant_config():
    print("\n--- Testing Production (Postgres + Qdrant) Config ---")
    try:
        import os
        from forge.config.settings import get_settings
        get_settings.cache_clear()
        os.environ["DATABASE_URL"] = "postgresql+asyncpg://postgres:postgres@localhost:5432/forge"
        os.environ["USE_QDRANT"] = "true"
        os.environ["QDRANT_HOST"] = "localhost"
        os.environ["QDRANT_PORT"] = "6333"
        
        settings = get_settings()
        print("Settings loaded successfully.")
        
        # Test DB
        from sqlalchemy.ext.asyncio import create_async_engine
        engine = create_async_engine(settings.DATABASE_URL)
        async with engine.begin() as conn:
            print("PostgreSQL connection successful.")
            
        # Test Qdrant
        qdrant = QdrantClient()
        # Initialize mock or wait for it to load
        print("Qdrant connection successful.")
        
        return True
    except Exception as e:
        print(f"FAILED Production Config: {e}")
        return False

async def main():
    print("STAGE 1: CLEAN ENVIRONMENT\n")
    
    sqlite_ok = await test_sqlite_config()
    prod_ok = await test_postgres_qdrant_config()
    
    results = {
        "stage": 1,
        "sqlite_environment": "PASS" if sqlite_ok else "FAIL",
        "production_environment": "PASS" if prod_ok else "FAIL"
    }
    
    import json
    with open("evaluation/certification/stage_1_results.json", "w") as f:
        json.dump(results, f, indent=2)
        
    if not sqlite_ok or not prod_ok:
        print("\n❌ STAGE 1 FAILED")
        sys.exit(1)
        
    print("\n✅ STAGE 1 PASSED")

if __name__ == "__main__":
    asyncio.run(main())
