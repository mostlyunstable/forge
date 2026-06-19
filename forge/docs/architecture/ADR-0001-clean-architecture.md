# ADR-0001: Use Clean Architecture with DDD

## Problem
Forge is a complex system with multiple bounded contexts (projects, memory, code intelligence, git intelligence, chat). Without clear boundaries, the codebase will degrade into spaghetti code within months.

## Options
1. **Clean Architecture + DDD**: Strict layer separation with domain as the core
2. **Service-oriented**: Flat services with shared models
3. **Monolith with modules**: Python packages with soft boundaries

## Decision
Clean Architecture with Domain Driven Design. Four layers:
- Domain: entities, value objects, repository contracts (zero dependencies)
- Application: use cases (depends only on domain)
- Infrastructure: adapters implementing domain contracts
- Presentation: FastAPI routes (depends on application)

## Tradeoffs
- **Pro**: Enforceable boundaries via architecture tests
- **Pro**: Domain logic is testable without infrastructure
- **Pro**: Infrastructure can be swapped (e.g., PostgreSQL to SQLite for tests)
- **Con**: More boilerplate (interfaces, mappers)
- **Con**: Steeper learning curve for contributors

## Status
Accepted

## Date
2026-06-18
