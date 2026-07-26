# Knowledge Graph Model

Forge uses a multi-hop Knowledge Graph to understand relationships across the repository and historical context.

## Entity: `Relationship`
The `Relationship` entity represents a directed edge between two entities (e.g., File to File, Bug to File, ADR to Feature).

**Fields:**
- `id`
- `source_entity` (MemoryId or NodeId)
- `target_entity` (MemoryId or NodeId)
- `relationship_type` (Enum)
- `confidence`
- `provenance`
- `metadata`
- `created_at`

## Supported Types
- `affects`, `references`, `implements`, `fixes`, `supersedes`, `caused_by`, `depends_on`, `introduced`, `removed`, `documents`, `discusses`, `related_to`.

## Traversal
The `SQLiteGraphAdapter` allows queries to retrieve 1st, 2nd, and Nth degree connections, providing the Retrieval engine with profound context (e.g., finding the ADR that justifies the code that caused a specific Bug).
