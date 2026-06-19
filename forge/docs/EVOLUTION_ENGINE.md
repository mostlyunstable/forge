# FORGE EVOLUTION ENGINE -- Deep Audit & Strategic Plan

**Date**: 2026-06-18
**Auditor**: Lead Architect
**Scope**: Full codebase audit across all layers

---

## PART 1: CURRENT STATE AUDIT

### Scorecard

| Layer | Score | Status |
|-------|-------|--------|
| Domain | 6.5/10 | Structurally sound, behaviorally anemic |
| Application | 6.5/10 | Clean SRP, missing CRUD and validation |
| Infrastructure | 6.5/10 | 100% contract compliance, critical bugs |
| Presentation | 6.0/10 | REST skeleton, no Update/Delete |
| Tests | 3.5/10 | Architecture tests excellent, everything else hollow |
| VS Code Extension | 3.0/10 | Prototype with stubs |
| DevOps | 5.5/10 | Functional for dev, not production |
| **Overall** | **5.4/10** | **Working prototype, not production system** |

---

### What Is Complete (Done Well)

1. **Architecture enforcement** -- 11 tests that CI-fail on layer violations, file size limits, module isolation. This is genuinely production-grade.
2. **Domain contracts** -- 8 repository interfaces, 4 port interfaces, all async, all in correct layers.
3. **Infrastructure compliance** -- Every domain contract has a working implementation. 100% method coverage.
4. **Dependency graph engine** -- Tree-sitter parsing, dependency extraction (Python/TS/JS), cycle detection, transitive traversal, BFS/DFS algorithms. This is the moat.
5. **Vector search** -- Qdrant + in-memory fallback, deterministic IDs, embedding caching, cosine similarity.
6. **Middleware stack** -- CORS, metrics, request ID, rate limiting, structured error handlers. Correct ordering.
7. **Clean Architecture purity** -- Zero ORM imports in domain, zero HTTP imports in domain, zero infrastructure imports in application.

### What Is Partially Complete

| Component | Done | Missing |
|-----------|------|---------|
| Project CRUD | Create + Read | Update, Delete |
| Memory CRUD | Create + Read (search) | Update, Delete, Get-by-ID |
| Code indexing | Index + Search + File entries | Incremental reindex, delete index |
| Git analysis | Analyze commits | Diff analysis, single commit detail |
| Chat | Blocking LLM call | Streaming, history, context injection |
| Auth | JWT verify | User management, permissions, multi-tenant |

### What Is Missing (Critical Gaps)

1. **Domain events** -- Zero event infrastructure. No `ProjectArchived`, `BugResolved`, `CycleDetected`, `CommitClassified`. This blocks async processing, notifications, audit logging.
2. **Aggregate enforcement** -- No invariant checking at aggregate boundaries. `CodeDependency` allows self-references. `Bug.create()` auto-resolves.
3. **CRUD completeness** -- No Update or Delete use cases for any entity. No PATCH endpoints. The API is read-mostly.
4. **Input validation** -- No bounds checking on limit/skip parameters. No empty-string guards. No schema validation beyond Pydantic field constraints.
5. **Test coverage** -- 9 of 16 use cases untested. Zero API tests. Zero database tests. Zero middleware tests.
6. **Database migrations** -- No Alembic. Schema changes require manual `create_all`. Production blocker.
7. **Foreign key constraints** -- No cascade rules. Project deletion orphans all child records.
8. **Unit of Work** -- `IndexRepositoryUseCase` deletes then indexes without transaction safety. Data loss risk.
9. **VS Code extension** -- 3 of 7 commands are stubs. No tests. No streaming. No markdown rendering.
10. **Docker production readiness** -- Runs as root, no multi-stage build, Docker socket mounted, stale deps.

### What Is Unnecessary

1. `ChatMessage` dataclass in `send_message.py` -- dead code, never used.
2. `ports/dependency_graph.py` in application layer -- duplicate of domain contract, never imported.
3. `create_access_token` in `auth.py` -- never called from presentation layer.
4. `ProjectSummaryResponse` schema -- defined but never referenced as a return type.
5. `escape_like_pattern` in domain `--belongs in infrastructure.

### What Creates the Moat

1. **Dependency graph engine** -- Tree-sitter + cycle detection + transitive traversal + call graphs. Competitors don't have this.
2. **Semantic code understanding** -- Vector embeddings of code, decisions, bugs enable cross-domain retrieval. The RAG pipeline.
3. **Engineering memory model** -- Decisions, bugs, preferences as first-class domain objects with their own bounded contexts. Not just "notes."
4. **Architecture enforcement tests** -- CI-fail on layer violations means the codebase stays clean as it grows.
5. **VS Code integration** -- Memory system embedded where developers work, not a separate tool.

---

## PART 2: PHASE ANALYSIS

### Feature: Domain Events & Event Bus

| Dimension | Assessment |
|-----------|------------|
| Business Value | HIGH -- Enables async processing, notifications, audit trails, reactive indexing |
| Engineering Value | HIGH -- Decouples side effects from domain logic, enables event sourcing later |
| Technical Complexity | MEDIUM -- Base class + event collection on entities + publisher interface + in-memory dispatcher |
| Risk Level | LOW -- Additive, doesn't change existing behavior |
| Dependencies | None |
| Long-term Impact | CRITICAL -- Foundation for every future async feature |

### Feature: Complete CRUD (Update/Delete Use Cases + Endpoints)

| Dimension | Assessment |
|-----------|------------|
| Business Value | HIGH -- Users cannot manage lifecycle of projects, decisions, bugs |
| Engineering Value | MEDIUM -- Standard pattern, low novelty |
| Technical Complexity | LOW -- Follow existing create/read patterns |
| Risk Level | LOW -- Additive endpoints |
| Dependencies | Domain events (for cascade deletes) |
| Long-term Impact | HIGH -- Required for production usability |

### Feature: Database Migrations (Alembic)

| Dimension | Assessment |
|-----------|------------|
| Business Value | MEDIUM -- Invisible to users, critical for ops |
| Engineering Value | HIGH -- Schema evolution without data loss |
| Technical Complexity | LOW -- Standard Alembic setup |
| Risk Level | MEDIUM -- Migration errors can corrupt data |
| Dependencies | Foreign key constraints |
| Long-term Impact | CRITICAL -- Cannot deploy without it |

### Feature: Input Validation & Error Codes

| Dimension | Assessment |
|-----------|------------|
| Business Value | MEDIUM -- Better error messages, fewer bugs |
| Engineering Value | HIGH -- Defensive programming, API contract clarity |
| Technical Complexity | LOW -- Pydantic validators + error code enum |
| Risk Level | LOW -- Additive |
| Dependencies | None |
| Long-term Impact | MEDIUM -- Improves API quality progressively |

### Feature: Comprehensive Test Suite

| Dimension | Assessment |
|-----------|------------|
| Business Value | MEDIUM -- Prevents regressions |
| Engineering Value | HIGH -- Enables confident refactoring |
| Technical Complexity | MEDIUM -- Need fakes, fixtures, TestClient setup |
| Risk Level | LOW -- Additive |
| Dependencies | None |
| Long-term Impact | CRITICAL -- Cannot scale codebase without tests |

### Feature: Streaming LLM Responses

| Dimension | Assessment |
|-----------|------------|
| Business Value | HIGH -- Chat is primary UX, blocking is terrible |
| Engineering Value | MEDIUM -- SSE/WebSocket pattern |
| Technical Complexity | MEDIUM -- Server-sent events + client reassembly |
| Risk Level | MEDIUM -- Changes chat contract |
| Dependencies | None |
| Long-term Impact | HIGH -- Core UX improvement |

### Feature: Aggregate Boundary Enforcement

| Dimension | Assessment |
|-----------|------------|
| Business Value | MEDIUM -- Prevents data corruption |
| Engineering Value | HIGH -- True DDD, invariant enforcement |
| Technical Complexity | MEDIUM -- Aggregate root pattern, repository coordination |
| Risk Level | MEDIUM -- Changes entity construction patterns |
| Dependencies | Domain events |
| Long-term Impact | HIGH -- Data integrity at scale |

### Feature: VS Code Extension Production Quality

| Dimension | Assessment |
|-----------|------------|
| Business Value | HIGH -- Primary developer interface |
| Engineering Value | MEDIUM -- Standard extension patterns |
| Technical Complexity | MEDIUM -- Markdown rendering, streaming, persistence |
| Risk Level | MEDIUM -- UX changes |
| Dependencies | Streaming LLM, CRUD endpoints |
| Long-term Impact | HIGH -- Developer adoption depends on this |

### Feature: Alembic + Foreign Keys + Unit of Work

| Dimension | Assessment |
|-----------|------------|
| Business Value | MEDIUM -- Data integrity |
| Engineering Value | HIGH -- Production database safety |
| Technical Complexity | MEDIUM -- Alembic setup, cascade rules, UoW pattern |
| Risk Level | MEDIUM -- Database changes |
| Dependencies | None |
| Long-term Impact | CRITICAL -- Production blocker |

---

## PART 3: PRIORITIZATION

### Priority 1: Production Blockers (Week 1-2)

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| 1.1 | Domain Events infrastructure | 4h | Foundation for everything |
| 1.2 | Alembic migrations + foreign keys | 4h | Cannot deploy without |
| 1.3 | Fix DependencyModel base class bug | 1h | Table won't exist |
| 1.4 | Input validation on all use cases | 3h | Prevents bad data |
| 1.5 | Error codes in API responses | 2h | API contract clarity |
| 1.6 | Add aiosqlite to pyproject.toml | 10m | Local dev crashes |
| 1.7 | Commit poetry.lock | 30m | Reproducible builds |

### Priority 2: CRUD Completeness (Week 2-3)

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| 2.1 | UpdateProject + DeleteProject use cases + endpoints | 3h | Project lifecycle |
| 2.2 | UpdateBug (mark resolved) + DeleteBug use cases + endpoints | 3h | Bug lifecycle |
| 2.3 | UpdateDecision (supersede) + DeleteDecision use cases + endpoints | 3h | Decision lifecycle |
| 2.4 | GetDecision + GetBug + ListDecisions + ListBugs use cases | 4h | Read completeness |
| 2.5 | DeletePreference endpoint | 1h | Preference lifecycle |

### Priority 3: Test Infrastructure (Week 3-4)

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| 3.1 | conftest.py with shared fixtures + fakes | 3h | Test foundation |
| 3.2 | Unit tests for all 16 use cases | 6h | Use case regression safety |
| 3.3 | API tests with TestClient for all routes | 5h | API contract testing |
| 3.4 | Repository integration tests (SQLite) | 4h | Database correctness |
| 3.5 | Middleware tests (auth, rate limit, error handlers) | 3h | Middleware correctness |

### Priority 4: Streaming & UX (Week 4-5)

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| 4.1 | SSE streaming endpoint for chat | 4h | Core UX |
| 4.2 | VS Code extension: streaming support | 4h | Extension UX |
| 4.3 | VS Code extension: markdown rendering | 3h | Readability |
| 4.4 | VS Code extension: progress indicators | 2h | Feedback |
| 4.5 | VS Code extension: fix stub commands | 4h | Feature completeness |

### Priority 5: Production Hardening (Week 5-6)

| # | Feature | Effort | Impact |
|---|---------|--------|--------|
| 5.1 | Multi-stage Dockerfile + non-root user | 2h | Security |
| 5.2 | .dockerignore | 30m | Build speed |
| 5.3 | Remove Docker socket mount | 15m | Security |
| 5.4 | Unit of Work for IndexRepositoryUseCase | 3h | Data safety |
| 5.5 | CommitClassifier to domain layer | 1h | Architecture purity |
| 5.6 | Extract adapters from presentation routes | 3h | Clean Architecture |

---

## PART 4: ARCHITECTURE REVIEW

### Alignment Check

| Principle | Status | Notes |
|-----------|--------|-------|
| Clean Architecture | ✅ | Domain has zero external imports. Application depends only on domain. |
| DDD | ⚠️ | Bounded contexts are good. Aggregates are not enforced. Events are missing. |
| SOLID | ⚠️ | SRP: good. OCP: good (ports). LSP: untested. ISP: contracts are focused. DIP: followed but ports duplicated. |
| Hexagonal | ✅ | Ports and adapters pattern is correctly applied. |
| Scalability | ⚠️ | In-memory rate limiter won't scale. No caching layer. No async processing. |
| Maintainability | ✅ | File size limits, architecture tests, consistent patterns. |

### Recommendations

1. **Remove duplicate `IDependencyGraph`** from `application/ports/` -- use domain version only.
2. **Move `CommitClassifier`** to `domain/git/services/commit_classifier.py`.
3. **Move `escape_like_pattern`** to `infrastructure/repositories/_utils.py`.
4. **Define abstract ports** for `VectorStore`, `EmbeddingService`, `GitAnalyzer`, `TreeSitterParser`.
5. **Introduce Unit of Work** pattern for transactional operations.

---

## PART 5: IMPLEMENTATION PLAN -- Priority 1 (Domain Events)

### Domain Model

```
domain/
  shared/
    events.py          # DomainEvent base class + EventBus interface
    event_handler.py   # EventHandler protocol
```

### Entities with Events

| Entity | Events Published |
|--------|-----------------|
| Project | `ProjectCreated`, `ProjectUpdated`, `ProjectArchived`, `ProjectDeleted` |
| ArchitectureDecision | `DecisionRecorded`, `DecisionUpdated`, `DecisionSuperseded`, `DecisionDeleted` |
| Bug | `BugRecorded`, `BugResolved`, `BugReopened`, `BugDeleted` |
| DeveloperPreference | `PreferenceRecorded`, `PreferenceStrengthened`, `PreferenceDeleted` |
| CodeEntry | `CodeEntryIndexed`, `CodeEntriesBatchIndexed`, `CodeIndexCleared` |
| CodeDependency | `DependencyGraphBuilt`, `CycleDetected` |
| Commit | `CommitAnalyzed`, `CommitClassified` |

### Use Cases

| Use Case | Event Triggered |
|----------|----------------|
| CreateProjectUseCase | `ProjectCreated` |
| UpdateProjectUseCase | `ProjectUpdated` |
| DeleteProjectUseCase | `ProjectDeleted` |
| SaveDecisionUseCase | `DecisionRecorded` |
| SaveBugUseCase | `BugRecorded` |
| SavePreferenceUseCase | `PreferenceRecorded` or `PreferenceStrengthened` |
| IndexRepositoryUseCase | `CodeEntriesBatchIndexed` |
| BuildDependencyGraphUseCase | `DependencyGraphBuilt`, optionally `CycleDetected` |
| AnalyzeCommitsUseCase | `CommitClassified` (per commit) |

### Repository Interfaces

No new repositories needed. Events are published by use cases, not repositories.

### Services

| Service | Interface | Implementation |
|---------|-----------|----------------|
| `IEventBus` | `domain/shared/events.py` | `InMemoryEventBus` in `infrastructure/events/` |
| `IEventHandler` | `domain/shared/event_handler.py` | Various handlers in `infrastructure/events/handlers/` |

### API Design

No new endpoints. Events are internal. Future: `/api/v1/events` for SSE event stream.

### Database Changes

None. Events are in-memory for MVP. Future: `event_store` table for event sourcing.

### Tests

| Test | Type | What It Covers |
|------|------|----------------|
| `test_domain_events.py` | Unit | Event creation, handler registration, dispatch |
| `test_event_bus.py` | Unit | InMemoryEventBus dispatch, ordering, error isolation |
| `test_use_case_events.py` | Unit | Each use case publishes correct event |
| `test_event_integration.py` | Integration | Event triggers handler side effects |

### Folder Structure

```
src/forge/
  domain/shared/
    events.py
    event_handler.py
  infrastructure/events/
    __init__.py
    in_memory_event_bus.py
    handlers/
      __init__.py
      indexing_handler.py     # Re-indexes vector store on code changes
      notification_handler.py # Logs events for audit trail
```

---

## PART 6: MILESTONES

### Milestone 1: Foundation (Days 1-3)
**Independently shippable**: Domain events + Alembic + bug fixes

1. Domain events infrastructure (base class, in-memory bus, handler protocol)
2. Alembic initialization + initial migration
3. Fix DependencyModel base class bug
4. Add foreign key constraints to all models
5. Add aiosqlite to dev dependencies
6. Commit poetry.lock
7. Add error codes to API error responses
8. Input validation on all request DTOs

### Milestone 2: CRUD (Days 4-6)
**Independently shippable**: Complete entity lifecycle management

1. UpdateProject + DeleteProject use cases + endpoints
2. UpdateBug + DeleteBug use cases + endpoints
3. UpdateDecision + DeleteDecision use cases + endpoints
4. GetDecision + GetBug + ListDecisions + ListBugs use cases + endpoints
5. DeletePreference endpoint
6. Unit of Work for IndexRepositoryUseCase
7. Wire domain events into all use cases

### Milestone 3: Quality (Days 7-10)
**Independently shippable**: Test infrastructure + comprehensive tests

1. conftest.py with shared fixtures and fakes
2. Unit tests for all 16+ use cases
3. API tests with TestClient for all routes
4. Repository integration tests against SQLite
5. Middleware tests (auth, rate limit, error handlers)
6. Domain event tests
7. Move CommitClassifier to domain
8. Move escape_like_pattern to infrastructure
9. Remove duplicate IDependencyGraph

### Milestone 4: Production (Days 11-14)
**Independently shippable**: Streaming, extension, Docker

1. SSE streaming endpoint for chat
2. VS Code extension: streaming support + markdown rendering
3. VS Code extension: fix stub commands (explainRepo, summarizeWork, projectTimeline)
4. VS Code extension: progress indicators + error handling
5. Multi-stage Dockerfile + non-root user
6. .dockerignore
7. Remove Docker socket mount
8. Extract adapters from presentation routes to infrastructure
9. Define abstract ports for VectorStore, EmbeddingService, GitAnalyzer

---

*End of Evolution Engine Report*
