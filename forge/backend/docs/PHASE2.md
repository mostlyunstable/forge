# Forge Phase 2: Engineering Knowledge Base

Phase 2 successfully evolves Forge from a Repository Intelligence engine into a comprehensive AI Engineering Companion.

## Features Introduced
- **Persistent Memory Hierarchy:** A generic `Memory` base entity extended by `ArchitectureDecision`, `Bug`, `Feature`, `EngineeringNote`, `DecisionLog`, and `EngineeringEvent`.
- **Versioning System:** Mutable memories maintain history via `version_number`, `previous_version_id`, and `superseded_by_id`.
- **Knowledge Graph:** A generic `Relationship` graph spanning Code, Memories, and Events with multi-hop capabilities.
- **Independent Ingestion:** Ingest engineering notes, meeting summaries, and markdown ADRs separately from code indexing.
- **Unified Retrieval:** A deterministic `IntentRouter` that fuses code context with historical memory context to provide accurate, grounded responses.

Phase 1 capabilities remain 100% operational.
