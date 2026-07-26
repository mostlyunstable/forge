# Migration Guide

Upgrading Forge from Phase 1 to Phase 2.

## Pre-requisites
- Ensure the Forge Phase 1 backend is stopped.
- Backup your SQLite database (`forge.db`) or PostgreSQL database.

## Applying Migrations
Forge uses Alembic to manage database schema updates. Phase 2 introduces Joined Table Inheritance for the `Memory` models and generic relationships for the Knowledge Graph.

```bash
# Verify current migration status
alembic current

# Run the upgrade script
alembic upgrade head
```

## Downgrade
Migrations are fully reversible. If you need to roll back to Phase 1:

```bash
alembic downgrade -1
```

## Data Integrity
No Phase 1 data (indexed repositories, code vectors) is modified or destroyed during the upgrade. The graph edge migrations will gracefully convert hardcoded edge types to the new generic `Relationship` entities.
