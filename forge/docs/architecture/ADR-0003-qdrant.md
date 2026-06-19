# ADR-0003: Qdrant for Vector Search

## Problem
Forge must perform semantic search across code entries, decisions, and bugs. Keyword search is insufficient for finding related content.

## Options
1. **Qdrant**: High performance, easy setup, filtering support
2. **Pinecone**: Managed, but vendor lock-in
3. **pgvector**: PostgreSQL extension, but slower at scale
4. **Chroma**: Simple, but less mature

## Decision
Qdrant. It provides excellent performance for cosine similarity search, supports metadata filtering (essential for scoping to a project), and runs as a single Docker container.

## Tradeoffs
- **Pro**: Purpose-built for vector search
- **Pro**: Filtering by project_id before search (performance)
- **Pro**: Easy Docker deployment
- **Con**: Additional service to maintain
- **Con**: Separate data store from PostgreSQL

## Status
Accepted

## Date
2026-06-18
