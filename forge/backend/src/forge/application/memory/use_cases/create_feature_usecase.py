"""CreateFeatureUseCase."""

import hashlib
from dataclasses import dataclass

from forge.application.memory.use_cases.markdown_parser import parse_markdown
from forge.application.ports import IEmbeddingService
from forge.domain.knowledge_graph.entities.relationship import Relationship, RelationshipType
from forge.domain.knowledge_graph.repository_contracts.graph_adapter import IGraphAdapter
from forge.domain.memory.entities.feature import Feature
from forge.domain.memory.repository_contracts.memory_repository import IMemoryRepository
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class CreateFeatureRequest:
    project_id: str
    content: str
    source: str = "file"
    author: str | None = None
    related_files: list[str] | None = None
    related_commits: list[str] | None = None


class CreateFeatureUseCase:
    def __init__(
        self,
        memory_repo: IMemoryRepository,
        graph_adapter: IGraphAdapter,
        embedding_service: IEmbeddingService | None = None,
    ):
        self._memory_repo = memory_repo
        self._graph_adapter = graph_adapter
        self._embedding_service = embedding_service

    async def execute(self, request: CreateFeatureRequest) -> Feature:
        metadata, body = parse_markdown(request.content)
        title = metadata.get("title", "Untitled Feature")
        status = metadata.get("status", "planned")
        ac_raw = metadata.get("acceptance_criteria", "")
        acceptance_criteria = [a.strip() for a in ac_raw.split(";") if a.strip()] if ac_raw else []

        project_id = ProjectId.from_string(request.project_id)
        existing_memories = await self._memory_repo.get_by_project(project_id)

        content_hash = hashlib.md5(request.content.encode()).hexdigest()

        for mem in existing_memories:
            if isinstance(mem, Feature) and mem.title == title:
                if mem.metadata.get("content_hash") == content_hash:
                    return mem

        feature = Feature.create(
            project_id=project_id,
            title=title,
            summary=body[:200] + "..." if len(body) > 200 else body,
            body=body,
            source=request.source,
            author=request.author,
            status=status,
            acceptance_criteria=acceptance_criteria,
        )
        feature.metadata["content_hash"] = content_hash

        if self._embedding_service:
            try:
                await self._embedding_service.get_embedding(request.content)
                feature.embedding_reference = "embedded"
            except Exception:
                pass

        saved_feature = await self._memory_repo.save(feature)

        relationships = []
        if request.related_files:
            for rf in request.related_files:
                relationships.append(
                    Relationship.create(
                        project_id=project_id,
                        source_id=str(saved_feature.id.value),
                        target_id=f"file:{rf}",
                        relationship_type=RelationshipType.IMPLEMENTS,
                    )
                )
        if request.related_commits:
            for rc in request.related_commits:
                relationships.append(
                    Relationship.create(
                        project_id=project_id,
                        source_id=str(saved_feature.id.value),
                        target_id=f"commit:{rc}",
                        relationship_type=RelationshipType.RELATED_TO,
                    )
                )

        if relationships:
            await self._graph_adapter.add_relationships(project_id, relationships)

        return saved_feature  # type: ignore
