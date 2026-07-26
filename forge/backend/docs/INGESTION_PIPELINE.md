# Ingestion Pipeline

Forge Phase 2 decouples memory ingestion from code indexing to ensure timeline facts can be safely recorded without modifying source code context.

## Workflow

1. **Input:** Receives Markdown files (ADRs, meeting notes), JSON payloads (Bugs, Features), or string events.
2. **Parsing:** Extracts structured metadata (title, author, timestamp) and unstructured text.
3. **Deduplication:** Hashes the content and metadata. If an identical hash exists, ingestion skips creation to prevent duplication.
4. **Embedding Generation:** Connects to `IEmbeddingService` to compute semantic vectors for the text content.
5. **Persistence:** Saves the new `Memory` to the SQL database using `IMemoryRepository`.
6. **Graph Linking:** Connects the Memory to specific source files or other memories using `IGraphAdapter` based on provided `related_commits` or `related_files`.
