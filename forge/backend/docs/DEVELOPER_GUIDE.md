# Forge Backend - Developer Quickstart

## Prerequisites

- Python 3.12+
- PostgreSQL 15+
- Qdrant (vector database)
- Docker (optional)

## Quick Start with Docker

```bash
cd forge/backend
docker-compose up -d
```

This starts:
- PostgreSQL on port 5432
- Qdrant on port 6333
- Backend API on port 8000

## Manual Setup

### 1. Create Virtual Environment

```bash
cd forge/backend
python3 -m venv .venv
source .venv/bin/activate
```

### 2. Install Dependencies

```bash
pip install -e .
```

### 3. Configure Environment

Create `.env` file:
```env
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/forge
QDRANT_HOST=localhost
QDRANT_PORT=6333
JWT_SECRET_KEY=your-secret-key-change-in-production
LLM_API_KEY=your-openai-api-key
LLM_MODEL=gpt-4
```

### 4. Start Services

```bash
# Start PostgreSQL and Qdrant
docker-compose up -d postgres qdrant

# Start the API
uvicorn forge.presentation.app:create_app --factory --reload --host 0.0.0.0 --port 8000
```

## Running Tests

```bash
# Run all tests
PYTHONPATH=src python3 -m pytest tests/ -v

# Run only unit tests
PYTHONPATH=src python3 -m pytest tests/unit/ -v

# Run architecture tests
PYTHONPATH=src python3 -m pytest tests/architecture/ -v

# Run performance benchmarks
PYTHONPATH=src python3 -m pytest tests/performance/ -v

# Run with coverage
PYTHONPATH=src python3 -m pytest tests/ --cov=forge --cov-report=html
```

## Project Structure

```
forge/backend/
├── src/forge/
│   ├── domain/           # Business entities and rules
│   │   ├── code/         # Code entry, dependency, value objects
│   │   ├── git/          # Commit, classification
│   │   ├── memory/       # Decision, bug, preference
│   │   └── projects/     # Project aggregate
│   ├── application/      # Use cases and ports
│   │   ├── code/         # Index, search, dependencies
│   │   ├── chat/         # Send message
│   │   ├── git/          # Analyze commits
│   │   ├── memory/       # Save/query memories
│   │   ├── projects/     # CRUD operations
│   │   └── ports.py      # Port interfaces
│   ├── infrastructure/   # Adapters and implementations
│   │   ├── code_indexer/ # Tree-sitter parser
│   │   ├── database/     # SQLAlchemy models
│   │   ├── git/          # GitPython analyzer
│   │   ├── llm/          # OpenAI client
│   │   ├── repositories/ # Repository implementations
│   │   └── search/       # Qdrant, embeddings, graph
│   ├── presentation/     # API layer
│   │   ├── middleware/    # Auth, rate limit, metrics
│   │   ├── routes/       # FastAPI routers
│   │   └── schemas/      # Pydantic models
│   └── config/           # Settings, logging, metrics
├── tests/
│   ├── unit/             # Unit tests
│   ├── integration/      # Integration tests
│   ├── performance/      # Benchmarks
│   └── architecture/     # Architecture enforcement
├── docs/                 # Documentation
├── pyproject.toml        # Project config
└── docker-compose.yml    # Services
```

## Architecture Rules

The codebase enforces Clean Architecture:

1. **Domain** has no imports from Application, Infrastructure, or Presentation
2. **Application** has no imports from Infrastructure or Presentation
3. **Infrastructure** has no imports from Application or Presentation
4. **Presentation** has no business logic

Run architecture tests to verify:
```bash
PYTHONPATH=src python3 -m pytest tests/architecture/ -v
```

## API Usage Example

```bash
# 1. Create a project
curl -X POST http://localhost:8000/api/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "My Project", "description": "Test", "stack": ["python"]}'

# 2. Index a repository
curl -X POST http://localhost:8000/api/v1/code/index \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"project_id": "PROJECT_ID", "repo_path": "/path/to/repo"}'

# 3. Search code
curl "http://localhost:8000/api/v1/code/search?q=my_function&project_id=PROJECT_ID" \
  -H "Authorization: Bearer $TOKEN"

# 4. Get dependency graph
curl "http://localhost:8000/api/v1/dependencies/import-graph/PROJECT_ID?file_path=src/main.py" \
  -H "Authorization: Bearer $TOKEN"
```

## Monitoring

- **Metrics**: `GET /metrics` (Prometheus format)
- **Logs**: JSON structured logs via structlog
- **Request IDs**: Every request gets a unique ID in `X-Request-ID` header

## Common Issues

### Database Connection
Ensure PostgreSQL is running and accessible:
```bash
docker-compose up -d postgres
```

### Qdrant Connection
Ensure Qdrant is running:
```bash
docker-compose up -d qdrant
```

### Import Errors
Ensure you're running from the backend directory with PYTHONPATH set:
```bash
cd forge/backend
PYTHONPATH=src python3 -m pytest tests/
```
