# Memory Model

All persistent knowledge inside Forge inherits from the base `Memory` entity.

## Base Entity: `Memory`
**Fields:**
`id`, `memory_type`, `title`, `summary`, `body`, `source`, `author`, `created_at`, `updated_at`, `metadata`, `embedding_reference`, `version_number`, `previous_version_id`, `superseded_by_id`, `archived_at`

## Subclasses
- **ArchitectureDecision:** Tracks architectural decisions, consequences, and alternatives.
- **Bug:** Tracks bug reports, root causes, regression tests, and resolutions.
- **Feature:** Tracks feature development, APIs, database changes, and rollout notes.
- **EngineeringNote:** Tracks general engineering documentation and meeting notes.
- **DecisionLog:** Tracks high-level technical direction.
- **EngineeringEvent:** Tracks immutable historical facts (e.g., "Deployment", "Bug Fixed").

## Versioning
Mutable memories support versioning. Updating a memory creates a new instance, increments the `version_number`, sets `previous_version_id`, and updates the old instance's `superseded_by_id`. History is never overwritten.

## Persistence
Stored via SQLAlchemy Joined Table Inheritance in `memory_model.py`.
