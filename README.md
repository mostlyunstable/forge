# Forge

**Persistent engineering memory. Not a chatbot. Memory is the product.**

Forge indexes codebases, tracks architectural decisions, records bug fixes, accumulates developer preferences, and retrieves relevant context. The longer it is used, the more valuable it becomes.

```
VS Code Extension ──> FastAPI Backend ──> PostgreSQL (structured)
                                      ──> Qdrant (vectors)
                                      ──> LLM API (generation)
```

## Features

- **Decision Tracking** — Record and retrieve architectural decisions (ADRs) with context
- **Bug Memory** — Capture bug fixes with root cause, solution, and affected files
- **Developer Preferences** — Accumulate team coding patterns and conventions
- **Code Intelligence** — Index repos with Tree-sitter, extract structured metadata, semantic search
- **Git Intelligence** — Commit analysis, classification (feature/bugfix/refactor), project timelines
- **Semantic Search** — Vector-powered search across all memories via Qdrant
- **VS Code Extension** — 7 commands, sidebar tree view, webview chat
- **Full REST API** — 33 endpoints with JWT auth, rate limiting, structured error codes

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

## VS Code Extension

```bash
cd vscode-extension
npm install
npm run compile
# Open in VS Code and press F5 to launch extension host
```

Commands:
| Command | Description |
|---------|-------------|
| `Forge: Chat` | Ask questions about your codebase |
| `Forge: Explain File` | Explain the current file with context |
| `Forge: Explain Repo` | High-level repo walkthrough |
| `Forge: Find Similar Bug` | Search bug memory for similar issues |
| `Forge: Summarize Work` | Daily/weekly work summary from git history |
| `Forge: Save Decision` | Record an architectural decision |
| `Forge: Project Timeline` | Visual timeline of project activity |

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

131 tests across four layers:

```bash
cd backend
rm -f forge.db
PYTHONPATH=src python3 -m pytest tests/ -v
# architecture/  - 11 tests (dependency rules)
# unit/          - 65 tests (use cases, domain, events, middleware)
# integration/   - 20 tests (SQLite repository tests)
# api/           - 15 tests (HTTP endpoint tests)
```

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Database | PostgreSQL (prod) / SQLite (dev) |
| Vectors | Qdrant |
| Code Parsing | Tree-sitter (Python, TypeScript, JavaScript) |
| LLM | OpenAI API |
| Auth | JWT (PyJWT) |
| Frontend | VS Code Extension (TypeScript) |
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
├── vscode-extension/        # VS Code extension
├── docs/                    # ADRs, architecture docs
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
| `LLM_API_KEY` | — | OpenAI API key |
| `LLM_MODEL` | `gpt-4` | LLM model name |
| `JWT_SECRET_KEY` | — | JWT signing secret |
| `DEBUG` | `false` | Enable debug mode |

## License

MIT
