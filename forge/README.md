# Forge

**Persistent engineering memory. Not a chatbot. Memory is the product.**

Forge indexes codebases, tracks architectural decisions, records bug fixes, accumulates developer preferences, and retrieves relevant context. The longer it is used, the more valuable it becomes.

```
Native CLI (Typer) ──> FastAPI Backend ──> PostgreSQL (structured)
                 (Internal)          ──> Qdrant (vectors)
                                      ──> NVIDIA NIM (embeddings + generation)
```

## Features

- **Decision Tracking** — Record and retrieve architectural decisions (ADRs) with context
- **Bug Memory** — Capture bug fixes with root cause, solution, and affected files
- **Developer Preferences** — Accumulate team coding patterns and conventions
- **Code Intelligence** — Index repos with Tree-sitter, extract structured metadata, semantic search
- **Git Intelligence** — Commit analysis, classification (feature/bugfix/refactor), project timelines
- **Semantic Search** — Vector-powered search across all memories via Qdrant
- **Knowledge Graph** — D3 force-directed graph showing relationships between decisions, bugs, and reports
- **Native Developer CLI** — Built with Typer, Rich, and Textual. An interactive terminal dashboard with Natural Language routing, streaming Markdown, and zero context switching.
- **Full REST API** — 33 endpoints with JWT auth, rate limiting, structured error codes
- **LLM-Optional** — Returns raw context when no LLM API key is configured

## Quick Start

### Docker (Recommended)

```bash
git clone https://github.com/mostlyunstable/forge.git
cd forge

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Start everything
docker compose up -d

# Server runs at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### Local Development

```bash
cd forge/backend

# Install dependencies
poetry install

# Copy env and configure
cp ../.env.example ../.env

# Run with SQLite (no Docker needed)
DATABASE_URL=sqlite+aiosqlite:///./forge.db USE_QDRANT=false \
  poetry run uvicorn forge.presentation.app:app --reload

# Run tests
rm -f forge.db && PYTHONPATH=src poetry run pytest tests/ -v
```

## Native Developer CLI

Forge is interacted with primarily through its native terminal interface (`forge`).

```bash
# Global interactive dashboard with F1-F7 shortcuts
forge

# Or use specific subcommands
forge chat "Explain the intent routing mechanism"
forge search "ADR for PostgreSQL"
forge explain src/forge/presentation/cli/main.py
forge memory list
forge graph
forge index
```

Commands:
| Command | Description |
|---------|-------------|
| `forge chat` | Interactive multiline chat with history and streaming responses |
| `forge search` | Search codebase, ADRs, bugs, and history |
| `forge explain` | Explain the architecture or file with full dependency context |
| `forge memory` | Navigate Engineering Knowledge Base (ADRs, bugs, features) |
| `forge graph` | Traverse dependency and memory graph |
| `forge index` | Index local repository via Tree-sitter |
| `forge doctor` | Diagnostics and connection health checks |

*(Note: The `desktop/` and `vscode-extension/` directories contain experimental/legacy clients from earlier phases. The Native CLI is the first-class presentation layer for Forge.)*

## API Endpoints

### Projects
| Method | Path | Description |
|--------|------|-------------|
| POST | `/projects` | Create project |
| GET | `/projects` | List projects |
| GET | `/projects/{id}` | Get project |
| PUT | `/projects/{id}` | Update project |
| DELETE | `/projects/{id}` | Delete project |

### Memory
| Method | Path | Description |
|--------|------|-------------|
| POST | `/memory/decisions` | Record decision |
| GET | `/memory/decisions` | List decisions |
| GET | `/memory/decisions/{id}` | Get decision |
| PUT | `/memory/decisions/{id}` | Update decision |
| DELETE | `/memory/decisions/{id}` | Delete decision |
| POST | `/memory/bugs` | Record bug |
| GET | `/memory/bugs` | List bugs |
| GET | `/memory/bugs/{id}` | Get bug |
| PUT | `/memory/bugs/{id}` | Update bug |
| DELETE | `/memory/bugs/{id}` | Delete bug |
| GET | `/memory/preferences` | Get preferences |
| DELETE | `/memory/preferences/{key}` | Delete preference |
| GET | `/memory/search` | Semantic search |

### Code
| Method | Path | Description |
|--------|------|-------------|
| POST | `/code/index` | Index repository |
| GET | `/code/search` | Search code |
| GET | `/code/files` | List file entries |
| GET | `/code/dependencies` | Dependency graph |
| GET | `/code/import-graph` | Import graph |
| GET | `/code/call-graph` | Call graph |

### Other
| Method | Path | Description |
|--------|------|-------------|
| POST | `/chat` | Chat with context |
| POST | `/git/analyze` | Analyze commits |
| GET | `/health` | Health check |
| GET | `/metrics` | Prometheus metrics |

## Architecture

Clean Architecture with Domain-Driven Design:

```
presentation/   → Routes, schemas, middleware (FastAPI)
application/    → Use cases, request/response DTOs
domain/         → Entities, value objects, repository contracts
infrastructure/ → Repository implementations, external services
```

**Dependency rule:** Domain has zero external dependencies. Infrastructure implements domain contracts. Presentation wires everything together.

### Bounded Contexts

| Context | Entities | Responsibility |
|---------|----------|----------------|
| Projects | Project | Project lifecycle, metadata |
| Memory | Decision, Bug, Preference | Engineering knowledge |
| Code | CodeEntry, Dependency | Codebase intelligence |
| Git | Commit | Version control intelligence |

### Test Suite

214 tests across four layers:

```bash
cd backend
rm -f forge.db
PYTHONPATH=src python3 -m pytest tests/ -v
# architecture/  - 11 tests (dependency rules)
# unit/          - 105 tests (use cases, domain, events, middleware)
# integration/   - 31 tests (SQLite repository tests)
# api/           - 26 tests (HTTP endpoint tests)
# analysis/      - 30 tests (PR analysis engine)
# indexing/      - 46 tests (code indexing engine)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Vectors | Qdrant |
| Code Parsing | Tree-sitter (Python, TypeScript, JavaScript) |
| LLM | NVIDIA NIM (optional, Meta Llama 3.1) |
| Embeddings | NVIDIA NV-EmbedQA-E5-V5 (1024 dimensions) |
| Auth | JWT (PyJWT) |
| Presentation Layer | Typer, Rich, Textual, Prompt Toolkit (Native CLI) |
| Legacy Clients | Tauri 2 (Desktop), VS Code Extension API |
| Containerization | Docker, Docker Compose |
| Testing | pytest, pytest-asyncio |
| Linting | Ruff, mypy |

## Project Structure

```
forge/
├── backend/
│   ├── src/forge/
│   │   ├── domain/          # Entities, value objects, repository contracts
│   │   ├── application/     # Use cases (one per operation)
│   │   ├── infrastructure/  # DB models, repositories, external services
│   │   ├── presentation/    # FastAPI routes, schemas, middleware
│   │   └── config/          # Settings, logging, metrics
│   ├── tests/
│   │   ├── architecture/    # Dependency rule enforcement
│   │   ├── unit/            # Use case and domain tests
│   │   ├── integration/     # Repository tests with SQLite
│   │   └── api/             # HTTP endpoint tests
│   └── pyproject.toml
├── desktop/forge-desktop/   # Tauri 2 desktop app
│   ├── src/                 # React components, hooks, stores
│   └── src-tauri/           # Tauri Rust backend
├── vscode-extension/        # VS Code extension
├── docs/                    # ADRs, architecture docs
├── Dockerfile
├── docker-compose.yml
└── Makefile
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite+aiosqlite:///./forge.db` | Database connection string |
| `QDRANT_HOST` | `localhost` | Qdrant host |
| `QDRANT_PORT` | `6333` | Qdrant port |
| `USE_QDRANT` | `true` | Set `false` for in-memory vector store |
| `LLM_API_KEY` | — | NVIDIA NIM API key (optional: chat returns raw context without it) |
| `LLM_MODEL` | `gpt-4` | LLM model name (default: meta/llama-3.1-8b-instruct via NVIDIA NIM) |
| `JWT_SECRET_KEY` | — | JWT signing secret |
| `DEBUG` | `false` | Enable debug mode |

## License

MIT
