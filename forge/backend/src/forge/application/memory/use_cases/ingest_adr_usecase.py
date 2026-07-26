"""IngestADRUseCase."""
import hashlib
from dataclasses import dataclass
from typing import Any

from forge.domain.memory.entities.decision import ArchitectureDecision
from forge.domain.memory.repository_contracts.memory_repository import IMemoryRepository
from forge.domain.knowledge_graph.repository_contracts.graph_adapter import IGraphAdapter
from forge.domain.knowledge_graph.entities.relationship import Relationship, RelationshipType
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.application.ports import IEmbeddingService
from forge.application.memory.use_cases.markdown_parser import parse_markdown

@dataclass
class IngestADRRequest:
    project_id: str
    content: str
    source: str = "file"
    author: str | None = None
    related_files: list[str] | None = None
    related_commits: list[str] | None = None

class IngestADRUseCase:
    def __init__(
        self,
        memory_repo: IMemoryRepository,
        graph_adapter: IGraphAdapter,
        embedding_service: IEmbeddingService | None = None
    ):
        self._memory_repo = memory_repo
        self._graph_adapter = graph_adapter
        self._embedding_service = embedding_service

    async def execute(self, request: IngestADRRequest) -> ArchitectureDecision:
        metadata, body = parse_markdown(request.content)
        title = metadata.get("title", "Untitled ADR")
        decision_text = metadata.get("decision", "Unknown decision")
        reason = metadata.get("reason", "No reason provided")
        status = metadata.get("status", "accepted")

        # Deduplication check
        project_id = ProjectId.from_string(request.project_id)
        existing_memories = await self._memory_repo.get_by_project(project_id)
        
        content_hash = hashlib.md5(request.content.encode()).hexdigest()
        
        for mem in existing_memories:
            if isinstance(mem, ArchitectureDecision) and mem.title == title:
                # If content hash matches, skip insertion
                if mem.metadata.get("content_hash") == content_hash:
                    return mem
                
        # Create entity
        adr = ArchitectureDecision.create(
            project_id=project_id,
            title=title,
            decision=decision_text,
            reason=reason,
            summary=body[:200] + "..." if len(body) > 200 else body,
            body=body,
            source=request.source,
            author=request.author,
        )
        adr.status = status
        adr.metadata["content_hash"] = content_hash

        # Generate embeddings
        if self._embedding_service:
            try:
                emb = await self._embedding_service.get_embedding(request.content)
                adr.embedding_reference = "embedded"  # Mock reference
            except Exception:
                pass
        
        saved_adr = await self._memory_repo.save(adr)

        # Graph Links
        relationships = []
        if request.related_files:
            for rf in request.related_files:
                relationships.append(Relationship.create(
                    project_id=project_id,
                    source_id=str(saved_adr.id.value),
                    target_id=f"file:{rf}",
                    relationship_type=RelationshipType.AFFECTS
                ))
        if request.related_commits:
            for rc in request.related_commits:
                relationships.append(Relationship.create(
                    project_id=project_id,
                    source_id=str(saved_adr.id.value),
                    target_id=f"commit:{rc}",
                    relationship_type=RelationshipType.CAUSED_BY
                ))
                
        if relationships:
            await self._graph_adapter.add_relationships(project_id, relationships)

        return saved_adr
