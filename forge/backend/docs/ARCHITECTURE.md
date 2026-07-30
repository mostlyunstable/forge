# Forge Architecture

Forge follows Clean Architecture and Domain-Driven Design (DDD).

## Core Bounded Contexts

1. **Repository Intelligence (Phase 1):** Codebase discovery, semantic chunking, and deterministic vector indexing.
2. **Engineering Knowledge Base (Phase 2):** Persistent tracking of Architecture Decisions (ADRs), Bugs, Features, Engineering Notes, and Timeline Events.

## Layers

- **Domain Layer:** Contains pure entities (`Memory`, `Bug`, `ArchitectureDecision`) and value objects (`MemoryId`). Does not depend on any infrastructure.
- **Application Layer:** Contains Use Cases (`IngestADR`, `SearchKnowledge`) defining the business workflows and ports (`IMemoryRepository`).
- **Infrastructure Layer:** Implements adapters (SQLAlchemy Repositories, Qdrant Vector Stores, SQLite Knowledge Graphs) for the application ports.
- **Presentation Layer:** The external interface interacting with Use Cases. The primary client is the Native Developer CLI (built with Typer/Rich/Textual), alongside the REST API.

## Data Flow

Data ingestion and semantic chunking are completely decoupled from unified retrieval. When retrieving, the `IntentRouter` coordinates across Code, Memory, and Graph data stores to assemble a grounded LLM Context via Reciprocal Rank Fusion.
