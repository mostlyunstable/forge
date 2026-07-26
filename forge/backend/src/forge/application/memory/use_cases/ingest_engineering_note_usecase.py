"""IngestEngineeringNoteUseCase."""
import hashlib
from dataclasses import dataclass

from forge.domain.memory.entities.note import EngineeringNote
from forge.domain.memory.repository_contracts.memory_repository import IMemoryRepository
from forge.domain.knowledge_graph.repository_contracts.graph_adapter import IGraphAdapter
from forge.domain.knowledge_graph.entities.relationship import Relationship, RelationshipType
from forge.domain.projects.value_objects.project_id import ProjectId
from forge.application.ports import IEmbeddingService
from forge.application.memory.use_cases.markdown_parser import parse_markdown

@dataclass
class IngestEngineeringNoteRequest:
    project_id: str
    content: str
    source: str = "file"
    author: str | None = None
    related_files: list[str] | None = None
    related_commits: list[str] | None = None

class IngestEngineeringNoteUseCase:
    def __init__(
        self,
        memory_repo: IMemoryRepository,
        graph_adapter: IGraphAdapter,
        embedding_service: IEmbeddingService | None = None
    ):
        self._memory_repo = memory_repo
        self._graph_adapter = graph_adapter
        self._embedding_service = embedding_service

    async def execute(self, request: IngestEngineeringNoteRequest) -> EngineeringNote:
        metadata, body = parse_markdown(request.content)
        title = metadata.get("title", "Untitled Note")
        tags_raw = metadata.get("tags", "")
        tags = [t.strip() for t in tags_raw.split(",") if t.strip()] if tags_raw else []

        project_id = ProjectId.from_string(request.project_id)
        existing_memories = await self._memory_repo.get_by_project(project_id)
        
        content_hash = hashlib.md5(request.content.encode()).hexdigest()
        
        for mem in existing_memories:
            if isinstance(mem, EngineeringNote) and mem.title == title:
                if mem.metadata.get("content_hash") == content_hash:
                    return mem

        note = EngineeringNote.create(
            project_id=project_id,
            title=title,
            summary=body[:200] + "..." if len(body) > 200 else body,
            body=body,
            source=request.source,
            author=request.author,
            tags=tags
        )
        note.metadata["content_hash"] = content_hash

        if self._embedding_service:
            try:
                emb = await self._embedding_service.get_embedding(request.content)
                note.embedding_reference = "embedded"
            except Exception:
                pass
        
        saved_note = await self._memory_repo.save(note)

        relationships = []
        if request.related_files:
            for rf in request.related_files:
                relationships.append(Relationship.create(
                    project_id=project_id,
                    source_id=str(saved_note.id.value),
                    target_id=f"file:{rf}",
                    relationship_type=RelationshipType.DOCUMENTS
                ))
        if request.related_commits:
            for rc in request.related_commits:
                relationships.append(Relationship.create(
                    project_id=project_id,
                    source_id=str(saved_note.id.value),
                    target_id=f"commit:{rc}",
                    relationship_type=RelationshipType.RELATED_TO
                ))
                
        if relationships:
            await self._graph_adapter.add_relationships(project_id, relationships)

        return saved_note
