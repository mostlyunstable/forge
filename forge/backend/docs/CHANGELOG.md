# Changelog

## [2.0.0] - 2026-07-20

### Added
- **Persistent Engineering Memory:** New polymorphic domain model tracking Architecture Decisions, Bugs, Features, and Notes.
- **Knowledge Graph Extension:** Replaced hardcoded edges with generic `Relationship` models supporting multi-hop traversals.
- **Version Tracking:** Added `version_number`, `previous_version_id`, and `superseded_by_id` support to track the chronological evolution of memories.
- **Unified Retrieval Engine:** Context retrieval now intelligently fuses codebase chunks with historical memories and architecture decisions using Reciprocal Rank Fusion.
- **Intent Router:** Fast deterministic semantic matcher that identifies whether a query needs Code, Bugs, or Decision context.
- **Phase 2 Evaluation Suite:** New `benchmark_v2.py` capable of testing historical and graphical reasoning capabilities.

### Changed
- Refactored `SQLiteDependencyGraph` to support generic relationships.
- Updated `ContextRetriever` to orchestrate multiple retrieval streams and manage dynamic token budgeting across diverse payload types.
- Fixed layer violation by injecting `IEmbeddingService` into application use cases from the presentation layer.

### Maintained
- **Phase 1 Feature Freeze:** All Repository Intelligence capabilities, including incremental indexing and AST parsing, remain fully backward compatible.
