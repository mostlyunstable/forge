# Forge - System Architecture Overview

## 1. What Forge Is

Forge is a persistent engineering memory system. It is not a chatbot.
Chat is the interface. Memory is the product.

Forge indexes codebases, tracks architectural decisions, records bug fixes,
accumulates developer preferences, and retrieves relevant context to assist
engineers. The longer it is used, the more valuable it becomes.

## 2. System Overview

```
VS Code Extension
        |
        v
FastAPI Backend
        |
   +----+----+----+
   |         |         |
   v         v         v
PostgreSQL  Qdrant   LLM API
(Structured) (Vectors) (Generation)
```

The system has four external integrations:
- **PostgreSQL**: Structured storage (projects, decisions, bugs, code entries, commits)
- **Qdrant**: Vector storage for semantic search across all memories
- **LLM API**: Code analysis, summarization, and response generation
- **Git**: Repository analysis and commit intelligence

## 3. Domain Boundaries

Forge has five bounded contexts (modules):

### 3.1 Projects Module
- Manages project lifecycle
- Stores project metadata, goals, tech stack
- Owner of Project aggregate root

### 3.2 Memory Module
- Stores architectural decisions (ADRs)
- Stores bug fix records
- Stores developer preferences
- Handles semantic search across all memories

### 3.3 Code Intelligence Module
- Indexes repositories using Tree-sitter
- Extracts structured metadata (classes, functions, interfaces)
- Stores code entries with embeddings for semantic search

### 3.4 Git Intelligence Module
- Analyzes commit history
- Classifies commits (feature, bugfix, refactor, performance, security)
- Builds project timelines

### 3.5 Conversation Module
- Manages chat sessions
- Retrieves context from all modules
- Generates responses using LLM with retrieved context

## 4. Core Modules and Responsibilities

| Module | Responsibility | Owns |
|--------|---------------|------|
| Projects | Project CRUD, metadata | Project entity |
| Memory | Decisions, bugs, preferences | Decision, Bug, Preference entities |
| Code Intelligence | Repo indexing, code search | CodeEntry entity |
| Git Intelligence | Commit analysis, timeline | Commit entity |
| Conversation | Chat, context retrieval, LLM | Session entity |

## 5. Dependency Flow

```
Presentation (FastAPI routes)
        |
        v
Application (Use Cases)
        |
        v
Domain (Entities, Repository Contracts)
        |
        v
Infrastructure (Repository Impls, External Services)
```

Rules:
- Presentation depends on Application only
- Application depends on Domain only
- Domain has zero external dependencies
- Infrastructure implements Domain contracts

## 6. Data Flow

### Index Repository Flow
```
User triggers index
  -> CodeIndexerUseCase
    -> GitAnalyzer reads repo
    -> TreeSitterParser extracts entries
    -> EmbeddingService generates vectors
    -> CodeRepository stores entries (PostgreSQL)
    -> VectorStore stores embeddings (Qdrant)
```

### Chat Flow
```
User sends message
  -> ChatUseCase
    -> RetrievalEngine finds relevant context
      -> VectorStore.search_code()
      -> VectorStore.search_decisions()
      -> VectorStore.search_bugs()
    -> LLMService generates response with context
    -> SessionRepository stores exchange
```

### Save Decision Flow
```
User saves decision
  -> MemoryUseCase.save_decision()
    -> DecisionRepository stores (PostgreSQL)
    -> EmbeddingService generates vector
    -> VectorStore.upsert_decision (Qdrant)
```

## 7. Event Flow

Forge is synchronous for MVP. Events are future extension points:

Potential events:
- `RepositoryIndexed` - triggers knowledge graph update
- `DecisionSaved` - triggers preference learning
- `BugFixed` - triggers pattern detection
- `SessionCompleted` - triggers daily journal generation

## 8. Technology Choices and Rationale

| Technology | Choice | Why |
|-----------|--------|-----|
| Backend Framework | FastAPI | Async, type-safe, fast |
| Database | PostgreSQL | Reliable, JSON support, relational |
| Vector Search | Qdrant | Performance, filtering, easy setup |
| Code Parsing | Tree-sitter | Incremental, multi-language, fast |
| LLM | OpenAI API | Quality, reliability |
| Auth | JWT | Stateless, simple |
| Containerization | Docker | Reproducible deployments |

## 9. Cross-Cutting Concerns

| Concern | Implementation |
|---------|---------------|
| Authentication | JWT middleware in Presentation layer |
| Logging | Structured logging via Python logging |
| Error Handling | Domain exceptions, Application error mapping |
| Validation | Pydantic schemas at Presentation boundary |
| Migrations | Alembic for PostgreSQL schema changes |
| Testing | Architecture tests enforce layer rules |
