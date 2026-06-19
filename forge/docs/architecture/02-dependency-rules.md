# Forge - Dependency Rules

These rules are enforced by architecture tests in CI.
Any violation fails the build.

## Layer Dependency Rules

```
Presentation Layer
        |
        v
Application Layer
        |
        v
Domain Layer
        ^
        |
Infrastructure Layer
```

## Allowed Dependencies

| Source | Target | Allowed |
|--------|--------|---------|
| Presentation | Application | YES |
| Presentation | Domain | NO |
| Presentation | Infrastructure | NO |
| Application | Domain | YES |
| Application | Infrastructure | NO |
| Domain | anything | NO |
| Infrastructure | Domain | YES (implements contracts) |

## Detailed Rules

### Domain Layer
- MUST NOT import from Application
- MUST NOT import from Infrastructure
- MUST NOT import from Presentation
- MUST NOT use SQLAlchemy, FastAPI, or any framework
- MUST NOT have external service calls
- Repository contracts are INTERFACES defined here
- Entities contain business logic, not data access

### Application Layer
- MUST import from Domain only
- MUST NOT import from Infrastructure
- MUST NOT import from Presentation
- Contains use cases (one class per use case)
- Use cases depend on domain repository contracts
- No database access, no HTTP, no external services

### Infrastructure Layer
- MUST import from Domain (to implement contracts)
- MUST NOT import from Application
- MUST NOT import from Presentation
- Repository implementations live here
- External service adapters live here
- ORM models are INTERNAL to infrastructure only

### Presentation Layer
- MUST import from Application (to call use cases)
- MUST NOT import from Domain directly
- MUST NOT import from Infrastructure directly
- Controllers/Route handlers validate input, call use cases, return responses
- No business logic in routes

## Module Isolation Rules

Modules MUST NOT import from each other directly.

```
projects/domain  --X-->  memory/domain
projects/application  --X-->  memory/application
```

Cross-module communication goes through:
1. Application layer orchestration
2. Domain events (future)

## File Size Limits

| Type | Max Lines | Max Bytes |
|------|-----------|-----------|
| Component | 300 | 10KB |
| Service | 300 | 10KB |
| Class | 250 | 8KB |
| Function | 50 | 2KB |
| File (any) | 500 | 15KB |

Exceeding any limit fails CI.

## Naming Conventions

| Layer | Pattern | Example |
|-------|---------|---------|
| Entity | PascalCase | `Project`, `Decision` |
| Value Object | PascalCase | `ProjectId`, `EntryType` |
| Repository Contract | I-prefix | `IProjectRepository` |
| Repository Impl | No prefix | `ProjectRepository` |
| Use Case | VerbNoun | `CreateProject`, `SendMessage` |
| Schema | Suffixed | `ProjectCreateRequest`, `ProjectResponse` |
| Route | plural nouns | `/api/v1/projects` |
| ORM Model | Suffixed | `ProjectModel` |

## Architecture Test Enforcement

CI runs these checks:

1. **test_no_circular_dependencies**: Import graph has no cycles
2. **test_domain_has_no_imports**: Domain imports only stdlib
3. **test_application_imports_domain_only**: Application imports only domain
4. **test_infrastructure_does_not_import_application**: Infrastructure skips application
5. **test_presentation_does_not_import_domain**: Presentation skips domain
6. **test_no_oversized_files**: All files under size limits
7. **test_no_dead_code**: No unused exports
8. **test_module_isolation**: Modules do not cross-import

Build fails on ANY violation.
