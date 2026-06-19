# Forge - Folder Structure

Every folder has a single responsibility.
Every file has a single responsibility.
No folder is a dumping ground.

## Backend

```
backend/
├── src/
│   └── forge/
│       ├── __init__.py
│       │
│       ├── domain/                          # CORE: Zero dependencies
│       │   ├── __init__.py
│       │   │
│       │   ├── projects/                    # Projects bounded context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   ├── __init__.py
│       │   │   │   └── project.py           # Project aggregate root
│       │   │   ├── value_objects/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── project_id.py        # ProjectId VO
│       │   │   │   └── tech_stack.py        # TechStack VO
│       │   │   ├── repository_contracts/
│       │   │   │   ├── __init__.py
│       │   │   │   └── project_repository.py  # IProjectRepository interface
│       │   │   └── exceptions.py            # Domain exceptions
│       │   │
│       │   ├── memory/                      # Memory bounded context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── decision.py          # ArchitectureDecision entity
│       │   │   │   ├── bug.py               # Bug entity
│       │   │   │   └── preference.py        # DeveloperPreference entity
│       │   │   ├── value_objects/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── decision_id.py
│       │   │   │   ├── bug_id.py
│       │   │   │   └── preference_key.py
│       │   │   ├── repository_contracts/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── decision_repository.py
│       │   │   │   ├── bug_repository.py
│       │   │   │   └── preference_repository.py
│       │   │   └── exceptions.py
│       │   │
│       │   ├── code/                        # Code Intelligence bounded context
│       │   │   ├── __init__.py
│       │   │   ├── entities/
│       │   │   │   ├── __init__.py
│       │   │   │   └── code_entry.py        # CodeEntry entity
│       │   │   ├── value_objects/
│       │   │   │   ├── __init__.py
│       │   │   │   ├── entry_type.py        # EntryType enum
│       │   │   │   └── code_location.py     # FilePath, LineRange VOs
│       │   │   ├── repository_contracts/
│       │   │   │   ├── __init__.py
│       │   │   │   └── code_repository.py
│       │   │   └── exceptions.py
│       │   │
│       │   └── git/                         # Git Intelligence bounded context
│       │       ├── __init__.py
│       │       ├── entities/
│       │       │   ├── __init__.py
│       │       │   └── commit.py            # Commit entity
│       │       ├── value_objects/
│       │       │   ├── __init__.py
│       │       │   ├── commit_sha.py
│       │       │   └── commit_classification.py
│       │       ├── repository_contracts/
│       │       │   ├── __init__.py
│       │       │   └── commit_repository.py
│       │       └── exceptions.py
│       │
│       ├── application/                     # USE CASES: Depends only on domain
│       │   ├── __init__.py
│       │   │
│       │   ├── projects/
│       │   │   ├── __init__.py
│       │   │   ├── create_project.py        # CreateProjectUseCase
│       │   │   ├── get_project.py           # GetProjectUseCase
│       │   │   └── list_projects.py         # ListProjectsUseCase
│       │   │
│       │   ├── memory/
│       │   │   ├── __init__.py
│       │   │   ├── save_decision.py         # SaveDecisionUseCase
│       │   │   ├── save_bug.py              # SaveBugUseCase
│       │   │   ├── save_preference.py       # SavePreferenceUseCase
│       │   │   ├── search_memories.py       # SearchMemoriesUseCase
│       │   │   └── get_preferences.py       # GetPreferencesUseCase
│       │   │
│       │   ├── code/
│       │   │   ├── __init__.py
│       │   │   ├── index_repository.py      # IndexRepositoryUseCase
│       │   │   ├── search_code.py           # SearchCodeUseCase
│       │   │   └── get_file_entries.py      # GetFileEntriesUseCase
│       │   │
│       │   ├── git/
│       │   │   ├── __init__.py
│       │   │   ├── analyze_commits.py       # AnalyzeCommitsUseCase
│       │   │   └── get_project_timeline.py  # GetProjectTimelineUseCase
│       │   │
│       │   └── chat/
│       │       ├── __init__.py
│       │       ├── send_message.py          # SendMessageUseCase
│       │       └── retrieve_context.py      # RetrieveContextUseCase
│       │
│       ├── infrastructure/                  # ADAPTERS: Implements domain contracts
│       │   ├── __init__.py
│       │   │
│       │   ├── database/
│       │   │   ├── __init__.py
│       │   │   ├── connection.py            # Database connection manager
│       │   │   ├── session.py               # Session factory
│       │   │   ├── base.py                  # SQLAlchemy Base
│       │   │   └── models/                  # ORM models (internal to infra)
│       │   │       ├── __init__.py
│       │   │       ├── project_model.py
│       │   │       ├── decision_model.py
│       │   │       ├── bug_model.py
│       │   │       ├── code_entry_model.py
│       │   │       ├── commit_model.py
│       │   │       └── preference_model.py
│       │   │
│       │   ├── repositories/                # Repository implementations
│       │   │   ├── __init__.py
│       │   │   ├── project_repository.py
│       │   │   ├── decision_repository.py
│       │   │   ├── bug_repository.py
│       │   │   ├── code_repository.py
│       │   │   ├── commit_repository.py
│       │   │   └── preference_repository.py
│       │   │
│       │   ├── search/                      # Vector search adapters
│       │   │   ├── __init__.py
│       │   │   ├── qdrant_client.py
│       │   │   └── embedding_service.py
│       │   │
│       │   ├── code_indexer/                # Code parsing adapter
│       │   │   ├── __init__.py
│       │   │   └── tree_sitter_parser.py
│       │   │
│       │   ├── git/                         # Git analysis adapter
│       │   │   ├── __init__.py
│       │   │   └── git_analyzer.py
│       │   │
│       │   └── llm/                         # LLM adapter
│       │       ├── __init__.py
│       │       └── llm_service.py
│       │
│       ├── presentation/                    # INTERFACE: FastAPI routes
│       │   ├── __init__.py
│       │   ├── app.py                       # FastAPI application factory
│       │   ├── dependencies.py              # Dependency injection
│       │   ├── middleware/
│       │   │   ├── __init__.py
│       │   │   ├── auth.py                  # JWT middleware
│       │   │   └── error_handler.py         # Global error handling
│       │   ├── schemas/                     # Request/Response DTOs
│       │   │   ├── __init__.py
│       │   │   ├── project_schemas.py
│       │   │   ├── memory_schemas.py
│       │   │   ├── code_schemas.py
│       │   │   ├── chat_schemas.py
│       │   │   └── git_schemas.py
│       │   └── routes/                      # API endpoints
│       │       ├── __init__.py
│       │       ├── projects.py
│       │       ├── memory.py
│       │       ├── code.py
│       │       ├── chat.py
│       │       └── git.py
│       │
│       └── config/
│           ├── __init__.py
│           └── settings.py                  # Application configuration
│
├── tests/
│   ├── __init__.py
│   ├── architecture/                        # Architecture tests (CI gate)
│   │   ├── __init__.py
│   │   ├── test_dependency_rules.py
│   │   ├── test_file_sizes.py
│   │   └── test_module_isolation.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   └── application/
│   ├── integration/
│   │   ├── __init__.py
│   │   └── repositories/
│   └── conftest.py
│
├── alembic/                                 # Database migrations
│   ├── env.py
│   └── versions/
│
├── pyproject.toml
├── alembic.ini
└── Dockerfile
```

## VS Code Extension

```
vscode-extension/
├── src/
│   ├── extension.ts                         # Entry point
│   ├── commands/                            # Command implementations
│   │   ├── chat.ts
│   │   ├── explain-file.ts
│   │   ├── explain-repo.ts
│   │   ├── find-similar-bug.ts
│   │   ├── summarize-work.ts
│   │   └── save-decision.ts
│   ├── providers/
│   │   ├── tree-view.ts                     # Sidebar tree view
│   │   └── webview.ts                       # Chat webview
│   ├── services/
│   │   └── forge-api.ts                     # API client
│   └── utils/
│       └── config.ts                        # Extension config
├── media/
│   └── icon.png
├── package.json
└── tsconfig.json
```

## Root Files

```
forge/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── Makefile
└── README.md
```
