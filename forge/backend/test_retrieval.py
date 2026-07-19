import asyncio
import os
import uuid

os.environ["QDRANT_HOST"] = "memory"
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["LLM_API_KEY"] = "mock-key"

from forge.infrastructure.search.qdrant_client import vector_store
from evaluation.certification import MockEmbeddingService, MockFileRepo, MockCandidateRepo, MockMemoryExtractor, MockGitDiff, MockCommitParser, MockGitHistoryIngester, MockJobRepo
from forge.infrastructure.search.graph_adapter import SQLiteDependencyGraph
from forge.application.indexing.full_index_usecase import FullIndexUseCase
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.infrastructure.search.context_retriever import ContextRetriever

import tempfile
async def run():
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
    
    repo_path = "/Users/caffinelove/FORGE AI/forge/backend/src/forge"
    project_id = ProjectId(uuid.uuid4())
    print("Indexing...")
    await indexer.execute(project_id, repo_path)
    
    retriever = ContextRetriever(vector_store=vector_store, dependency_graph=dep_graph)
    retriever._embedding_service = MockEmbeddingService()
    
    results = await retriever.retrieve("Which component uses Tree-sitter for AST parsing?", project_id)
    print("TOP RESULTS:")
    for i, r in enumerate(results["relevant_code"][:5]):
        print(f"{i+1}. {r['payload']['file_path']} - Score: {r['score']}")
        print(f"Content: {r['payload'].get('content', '')[:100]}...")

if __name__ == "__main__":
    asyncio.run(run())
