"""RecordEngineeringEventUseCase."""

import hashlib
import json
from dataclasses import dataclass

from forge.application.memory.use_cases.markdown_parser import parse_markdown
from forge.application.ports import IEmbeddingService
from forge.domain.knowledge_graph.entities.relationship import Relationship, RelationshipType
from forge.domain.knowledge_graph.repository_contracts.graph_adapter import IGraphAdapter
from forge.domain.memory.entities.event import EngineeringEvent
from forge.domain.memory.repository_contracts.memory_repository import IMemoryRepository
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class RecordEngineeringEventRequest:
    project_id: str
    content: str
    source: str = "system"
    author: str | None = None
    related_files: list[str] | None = None
    related_commits: list[str] | None = None


class RecordEngineeringEventUseCase:
    def __init__(
        self,
        memory_repo: IMemoryRepository,
        graph_adapter: IGraphAdapter,
        embedding_service: IEmbeddingService | None = None,
    ):
        self._memory_repo = memory_repo
        self._graph_adapter = graph_adapter
        self._embedding_service = embedding_service

    async def execute(self, request: RecordEngineeringEventRequest) -> EngineeringEvent:
        metadata, body = parse_markdown(request.content)
        title = metadata.get("title", "Unknown Event")
        event_type = metadata.get("event_type", "general")

        event_data_raw = metadata.get("event_data", "{}")
        try:
            event_data = json.loads(event_data_raw)
        except json.JSONDecodeError:
            event_data = {"raw": event_data_raw}

        project_id = ProjectId.from_string(request.project_id)
        existing_memories = await self._memory_repo.get_by_project(project_id)

        content_hash = hashlib.md5(request.content.encode()).hexdigest()

        for mem in existing_memories:
            if isinstance(mem, EngineeringEvent) and mem.title == title:
                if mem.metadata.get("content_hash") == content_hash:
                    return mem

        event = EngineeringEvent.create(
            project_id=project_id,
            title=title,
            event_type=event_type,
            summary=body[:200] + "..." if len(body) > 200 else body,
            body=body,
            source=request.source,
            author=request.author,
            event_data=event_data,
        )

        # EngineeringEvent is immutable, but metadata is a dict, so we can modify it
        # Actually, let's bypass immutability or do it before if needed
        # Since it is a dict, modifying it works unless it's frozen deeply
        # A workaround is using object.__setattr__ if we want to modify embedding_reference
        object.__setattr__(event, "metadata", {**event.metadata, "content_hash": content_hash})

        if self._embedding_service:
            try:
                await self._embedding_service.get_embedding(request.content)
                object.__setattr__(event, "embedding_reference", "embedded")
            except Exception:
                pass

        saved_event = await self._memory_repo.save(event)

        relationships = []
        if request.related_files:
            for rf in request.related_files:
                relationships.append(
                    Relationship.create(
                        project_id=project_id,
                        source_id=str(saved_event.id.value),
                        target_id=f"file:{rf}",
                        relationship_type=RelationshipType.RELATED_TO,
                    )
                )
        if request.related_commits:
            for rc in request.related_commits:
                relationships.append(
                    Relationship.create(
                        project_id=project_id,
                        source_id=str(saved_event.id.value),
                        target_id=f"commit:{rc}",
                        relationship_type=RelationshipType.RELATED_TO,
                    )
                )

        if relationships:
            await self._graph_adapter.add_relationships(project_id, relationships)

        return saved_event  # type: ignore
