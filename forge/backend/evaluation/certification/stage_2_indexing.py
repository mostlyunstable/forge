import os
import sys
import asyncio
import json
import uuid
import shutil
from pathlib import Path
from fastapi.testclient import TestClient
from forge.presentation.app import create_app

def setup_fixture(fixture_dir: Path):
    if fixture_dir.exists():
        shutil.rmtree(fixture_dir)
    fixture_dir.mkdir(parents=True)
    
    (fixture_dir / "main.py").write_text("def hello():\n    print('hello')\n")
    (fixture_dir / "utils.py").write_text("def add(a, b):\n    return a + b\n")

def mutate_fixture(fixture_dir: Path):
    (fixture_dir / "main.py").write_text("def hello():\n    print('hello world')\n")
    (fixture_dir / "utils.py").unlink()
    (fixture_dir / "new_file.py").write_text("def sub(a, b):\n    return a - b\n")

async def get_index_state(client: TestClient, project_id: str):
    # For now, we will query the SQLite directly to dump the DB state.
    # We can also hit search endpoint, but the internal vector/graph tables are what matter.
    from forge.infrastructure.database.connection import database_manager
    from forge.infrastructure.search.qdrant_client import QdrantClient
    
    qdrant = QdrantClient()
    collection_name = f"forge_code_{project_id}"
    try:
        points = await qdrant.query_points(
            collection_name=collection_name,
            query=[0.0]*1024,
            limit=10000,
            with_payload=True
        )
        vectors = {p.id: p.payload for p in points}
    except Exception:
        vectors = {}
        
    return vectors

async def async_main():
    # Setup test env
    import os
    os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
    os.environ["USE_QDRANT"] = "false"
    
    from forge.config.settings import get_settings
    get_settings.cache_clear()
    
    from forge.infrastructure.database.connection import database_manager
    from forge.presentation.app import create_app
    from forge.presentation.middleware.auth import verify_token
    
    # Must use a physical file for sqlite to share between connections if not using StaticPool
    # Actually, memory with aiosqlite creates per-connection DBs. Let's use a file.
    db_path = "/tmp/forge-certification/stage2.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{db_path}"
    get_settings.cache_clear()
    
    # recreate database_manager engine
    database_manager._engine = None
    database_manager._session_maker = None
    
    await database_manager.init_db()
    
    app = create_app()
    app.dependency_overrides[verify_token] = lambda: {"sub": "test"}
    client = TestClient(app)
    
    print("STAGE 2: INDEXING VALIDATION\n")
    
    project_name = f"stage2_test_{uuid.uuid4().hex[:8]}"
    fixture_dir = Path(f"/tmp/forge-certification/stage2_{uuid.uuid4().hex[:8]}")
    setup_fixture(fixture_dir)
    
    print("Creating project...")
    res = client.post("/api/v1/projects", json={
        "name": project_name,
        "path": str(fixture_dir)
    })
    res.raise_for_status()
    project_id = res.json()["id"]
    print(f"Project created: {project_id}")
    
    # 2. Full index
    print("Running full index...")
    res = client.post("/api/v1/index/jobs", json={
        "project_id": project_id,
        "repo_path": str(fixture_dir),
        "type": "full"
    })
    if res.status_code != 201:
        print(f"Full index failed: {res.text}")
        sys.exit(1)
    
    state_after_full = await get_index_state(client, project_id)
    
    # 3. Mutate
    print("Mutating fixture...")
    mutate_fixture(fixture_dir)
    
    # 4. Incremental index
    print("Running incremental index...")
    res = client.post("/api/v1/index/jobs", json={
        "project_id": project_id,
        "repo_path": str(fixture_dir),
        "type": "incremental"
    })
    if res.status_code != 201:
        print(f"Incremental index failed: {res.text}")
        sys.exit(1)
    state_after_incremental = await get_index_state(client, project_id)
    
    # 5. Full index again (simulating clean DB)
    print("Running full index again...")
    res = client.post("/api/v1/index/jobs", json={
        "project_id": project_id,
        "repo_path": str(fixture_dir),
        "type": "full"
    })
    if res.status_code != 201:
        print(f"Second full index failed: {res.text}")
        sys.exit(1)
    state_after_refull = await get_index_state(client, project_id)
    
    # Compare
    # The incremental should match the re-full
    diff_keys = set(state_after_incremental.keys()) ^ set(state_after_refull.keys())
    
    if diff_keys:
        print("❌ Incremental Index mismatch!")
        print(f"Diff keys: {diff_keys}")
        sys.exit(1)
        
    print("\n✅ STAGE 2 PASSED")

if __name__ == "__main__":
    asyncio.run(async_main())
