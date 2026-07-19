import asyncio
import os
import json
import time
import sqlite3
import tempfile
import uuid

os.environ["QDRANT_HOST"] = "memory"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["LLM_API_KEY"] = "mock-key"

from forge.infrastructure.search.qdrant_client import vector_store
from forge.infrastructure.search.graph_adapter import SQLiteDependencyGraph
from forge.infrastructure.search.context_retriever import ContextRetriever
from forge.application.indexing.full_index_usecase import FullIndexUseCase
from forge.domain.projects.value_objects.project_id import ProjectId

# --- Monkeypatch EmbeddingService ---
from forge.infrastructure.search import embedding_service
class MockEmbeddingService:
    def __init__(self):
        from sentence_transformers import SentenceTransformer
        # using a fast tiny model
        self.model = SentenceTransformer("BAAI/bge-small-en-v1.5")
        
    def _text_to_vector(self, text: str):
        vec = self.model.encode(text).tolist()
        # pad to 1536 to match Qdrant's schema
        if len(vec) < 1536:
            vec.extend([0.0] * (1536 - len(vec)))
        return vec
        
    async def get_embedding(self, text: str, *args, **kwargs):
        import asyncio
        return await asyncio.to_thread(self._text_to_vector, text)
        
    async def get_embeddings(self, texts, *args, **kwargs):
        import asyncio
        return await asyncio.to_thread(lambda: [self._text_to_vector(t) for t in texts])

embedding_service.EmbeddingService = MockEmbeddingService

# --- Monkeypatch ContextRetriever to fetch more docs so LexicalScorer works ---
original_search_code = vector_store.search_code
async def mock_search_code(*args, **kwargs):
    kwargs["limit"] = 1000  # Fetch all docs for lexical scorer
    return await original_search_code(*args, **kwargs)
vector_store.search_code = mock_search_code

class MockJobRepo:
    async def create(self, *args, **kwargs):
        class Job:
            id = uuid.uuid4()
            def start(self): pass
            def update_progress(self, *args): pass
            def complete(self, *args): pass
            def fail(self, *args): pass
        return Job()
    async def save(self, *args, **kwargs): pass
    async def update_status(self, *args, **kwargs): pass
    async def log_error(self, *args, **kwargs): pass


class MockFileRepo:
    def __init__(self):
        self.files = {}
    async def save(self, file_index):
        self.files[file_index.file_path] = file_index
    async def save_many(self, file_indices):
        for fi in file_indices:
            self.files[fi.file_path] = fi
    async def get_by_project(self, project_id):
        return list(self.files.values())
    async def get_by_project_and_path(self, project_id, path):
        return self.files.get(path)
    async def delete_by_project(self, project_id):
        self.files.clear()

class MockCandidateRepo:
    async def save_batch(self, *args, **kwargs): pass
    async def save_many(self, *args, **kwargs): pass
    async def save(self, *args, **kwargs): pass

class MockMemoryExtractor:
    def extract_from_code_comments(self, *args, **kwargs): return []
    def extract_from_commit(self, *args, **kwargs): return []
    def extract_from_issue(self, *args, **kwargs): return []

class MockGitDiff:
    def get_changed_files(self, *args, **kwargs):
        return [{"status": "added", "path": "test.py"}]
    def get_latest_commit(self, *args, **kwargs): return "123"

class MockCommitParser:
    def get_recent_commits(self, *args, **kwargs): return []
    def get_file_metadata(self, *args, **kwargs): return {}

class MockGitHistoryIngester:
    async def ingest_commit_history(self, *args, **kwargs): pass
    async def ingest(self, *args, **kwargs): return {}


async def run_benchmark():
    print("Initializing environment...")
    await vector_store.init_collections()
    db_fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(db_fd)
    dep_graph = SQLiteDependencyGraph(db_path=db_path)
    
    indexer = FullIndexUseCase(
        job_repo=MockJobRepo(),
        file_index_repo=MockFileRepo(),
        candidate_repo=MockCandidateRepo(),
        memory_extractor=MockMemoryExtractor(),
        vector_store=vector_store,
        embedding_service=MockEmbeddingService(),
        dep_graph=dep_graph,
        git_diff_provider=MockGitDiff(),
        commit_parser=MockCommitParser(),
        git_history_ingester=MockGitHistoryIngester(),
    )
    indexer._code_indexer._embedding_service = MockEmbeddingService()
    
    retriever = ContextRetriever(vector_store=vector_store, dependency_graph=dep_graph)
    retriever._embedding_service = MockEmbeddingService()
    
    repo_path = "/Users/caffinelove/FORGE AI/forge/backend/src/forge"
    project_id = ProjectId(uuid.uuid4())
    print(f"Indexing repository {repo_path}...")
    await indexer.execute(project_id, repo_path)
    print("Indexing complete.")
    
    
    questions_path = "/Users/caffinelove/FORGE AI/forge/backend/evaluation/questions.json"
    ground_truth_path = "/Users/caffinelove/FORGE AI/forge/backend/evaluation/ground_truth.json"
    
    with open(questions_path, 'r') as f:
        questions = json.load(f)
    
    # Generate dummy ground truth if it doesn't match keys
    # But ideally it should exist. 
    # Actually, the subagent created ground_truth.json
    try:
        with open(ground_truth_path, 'r') as f:
            ground_truth = json.load(f)
    except FileNotFoundError:
        ground_truth = {}
        
    total_precision_5 = 0.0
    total_recall_10 = 0.0
    valid_questions = 0

    print(f"Running evaluation for {len(questions)} questions...")
    for q in questions:
        q_id = q["id"]
        query = q["question"]
        expected_files = ground_truth.get(q_id, [])
        if not expected_files:
            continue
            
        valid_questions += 1
        results = await retriever.retrieve(query, project_id)
        
        raw_paths = [r["payload"]["file_path"] for r in results["relevant_code"]]
        
        # Deduplicate paths preserving order
        retrieved_paths = []
        for p in raw_paths:
            if p not in retrieved_paths:
                retrieved_paths.append(p)
        
        # Normalize expected files
        expected_files = [e.replace("src/forge/", "") for e in expected_files]

        # Precision@5
        top_5 = retrieved_paths[:5]
        hits_5 = sum(1 for p in top_5 if any(e in p for e in expected_files))
        precision = hits_5 / min(len(top_5), len(expected_files)) if top_5 and expected_files else 0.0
        
        # Recall@10
        top_10 = retrieved_paths[:10]
        hits_10 = sum(1 for e in expected_files if any(e in p for p in top_10))
        recall = hits_10 / len(expected_files) if expected_files else 0
        
        total_precision_5 += precision
        total_recall_10 += recall
        print(f"Q: {query} -> P@5: {precision:.2f}, R@10: {recall:.2f}")
        if recall == 0:
            print(f"  Expected: {expected_files}")
            print(f"  Got (Top 3): {retrieved_paths[:3]}")

    if valid_questions > 0:
        print(f"Avg P@5: {total_precision_5 / valid_questions:.2f}")
        print(f"Avg R@10: {total_recall_10 / valid_questions:.2f}")
    else:
        print("No valid questions with ground truth found.")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
