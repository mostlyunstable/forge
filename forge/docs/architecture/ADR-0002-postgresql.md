# ADR-0002: PostgreSQL as Primary Database

## Problem
Forge needs to store projects, decisions, bugs, code entries, commits, and preferences. The storage must support JSON fields, full-text search, and relational queries.

## Options
1. **PostgreSQL**: Mature, JSON support, full-text search, reliable
2. **SQLite**: Simple, no server, but limited concurrency
3. **MongoDB**: Flexible schema, but loses relational guarantees

## Decision
PostgreSQL. It supports JSON columns for flexible metadata, has excellent async support via asyncpg, and provides the reliability needed for a memory system that must never lose data.

## Tradeoffs
- **Pro**: ACID transactions for critical memory data
- **Pro**: JSON columns for flexible metadata without schema changes
- **Pro**: Full-text search via pg_trgm for basic text search
- **Con**: Requires running a server (not embedded)
- **Con**: Heavier than SQLite for single-developer use

## Status
Accepted

## Date
2026-06-18
