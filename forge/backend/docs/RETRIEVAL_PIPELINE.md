# Unified Retrieval Pipeline

The core engine of Forge Phase 2 is the Unified Retrieval Pipeline, answering engineering queries with high precision by blending Code and Memory.

## Pipeline Steps

1. **Intent Router:** Analyzes the user's query deterministically (using heuristics and keywords) to assign weights across `code`, `bugs`, and `decisions` contexts. (e.g., "Why did we switch to PostgreSQL?" -> High `decisions` intent).
2. **Multi-Stream Search:**
    - Queries the Vector Database for Code chunks.
    - Queries the SQL Database/Embeddings for relevant Memories (ADRs, Bugs).
    - Traverses the Knowledge Graph for explicitly linked files/entities.
3. **Reciprocal Rank Fusion (RRF):** Merges the results of Code, Memory, and Graph streams based on semantic relevance and lexical match scores, scaled by the Intent Router weights.
4. **Deduplication:** Removes overlapping or redundant chunks.
5. **Token Budgeting:** Trims the tail of the ranked results to fit precisely within the LLM's context window.
6. **Context Assembly:** Structures the retrieved payloads clearly (e.g. `<Relevant Code>`, `<Relevant Decisions>`) for the LLM to consume.
