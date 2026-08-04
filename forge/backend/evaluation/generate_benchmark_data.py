import json
import os

questions = [
    {"id": "q1", "question": "Where is the Qdrant client connection configured?"},
    {
        "id": "q2",
        "question": "How does the ContextRetriever manage the token budget for LLM contexts?",
    },
    {"id": "q3", "question": "Where is the dependency graph stored and managed?"},
    {"id": "q4", "question": "How are OpenAI embeddings fetched and cached?"},
    {"id": "q5", "question": "What is the entry point for indexing a full repository?"},
    {
        "id": "q6",
        "question": "Where is the logic for incrementally syncing changes to the vector index?",
    },
    {"id": "q7", "question": "How is a file indexed and its metadata stored?"},
    {"id": "q8", "question": "Which component uses Tree-sitter for AST parsing?"},
    {"id": "q9", "question": "How are memories extracted from code comments?"},
    {
        "id": "q10",
        "question": "Where are the application settings and environment variables defined?",
    },
    {"id": "q11", "question": "How does the ContextRetriever perform hybrid search using RRF?"},
    {"id": "q12", "question": "Where is the local lexical scorer implemented for BM25 fallback?"},
    {
        "id": "q13",
        "question": "How does the vector store generate deterministic IDs for code points?",
    },
    {"id": "q14", "question": "Where does the system handle database migrations or schemas?"},
    {
        "id": "q15",
        "question": "How are repository graphs updated incrementally when a file is modified?",
    },
    {"id": "q16", "question": "Where is the FastAPI routing for the vector search?"},
    {"id": "q17", "question": "How does the full index usecase traverse the repository?"},
    {"id": "q18", "question": "Where are the Prometheus metrics defined for search latency?"},
    {"id": "q19", "question": "How does the system ignore files based on .gitignore?"},
    {"id": "q20", "question": "Where are the core domain entities for decisions and bugs?"},
]

ground_truth = {
    "q1": ["infrastructure/search/qdrant_client.py", "config/settings.py"],
    "q2": ["application/conversation/token_manager.py"],
    "q3": [
        "infrastructure/search/graph_adapter.py",
        "domain/code/repository_contracts/dependency_graph.py",
    ],
    "q4": ["infrastructure/search/embedding_service.py"],
    "q5": ["application/indexing/full_index_usecase.py", "application/code/index_repository.py"],
    "q6": [
        "application/indexing/incremental_index_usecase.py",
        "application/indexing/reindex_detector.py",
    ],
    "q7": [
        "domain/indexing/entities/file_index.py",
        "domain/indexing/repository_contracts/file_index_repository.py",
    ],
    "q8": ["infrastructure/code_indexer/tree_sitter_code_indexer.py"],
    "q9": ["application/indexing/memory_extractor.py"],
    "q10": ["config/settings.py"],
    "q11": [
        "infrastructure/search/context_retriever.py",
        "infrastructure/search/lexical_scorer.py",
    ],
    "q12": ["infrastructure/search/lexical_scorer.py"],
    "q13": ["infrastructure/search/qdrant_client.py"],
    "q14": ["infrastructure/database/"],
    "q15": [
        "infrastructure/search/graph_adapter.py",
        "application/indexing/incremental_index_usecase.py",
        "application/indexing/reindex_detector.py",
    ],
    "q16": ["presentation/routes/"],
    "q17": ["application/indexing/full_index_usecase.py"],
    "q18": [
        "config/metrics.py",
        "infrastructure/search/qdrant_client.py",
        "presentation/routes/metrics.py",
    ],
    "q19": [
        "application/indexing/full_index_usecase.py",
        "domain/indexing/services/file_discovery.py",
    ],
    "q20": [
        "domain/memories/entities/decision.py",
        "domain/memories/entities/bug.py",
        "domain/shared/events.py",
    ],
}

base_dir = "/Users/caffinelove/FORGE AI/forge/backend/evaluation"
with open(os.path.join(base_dir, "questions.json"), "w") as f:
    json.dump(questions, f, indent=2)
with open(os.path.join(base_dir, "ground_truth.json"), "w") as f:
    json.dump(ground_truth, f, indent=2)

print("Benchmark data generated.")
