"""SendMessageUseCase."""
from __future__ import annotations

from dataclasses import dataclass, field

from forge.domain.projects.repository_contracts.project_repository import IProjectRepository
from forge.domain.projects.exceptions import ProjectNotFoundError
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class ChatMessage:
    """A single chat exchange."""

    role: str
    content: str


@dataclass
class SendMessageRequest:
    """Input DTO for sending a chat message."""

    project_id: str
    message: str


@dataclass
class SendMessageResponse:
    """Output DTO after processing a chat message."""

    response: str
    sources: list[dict]
    project_id: str


class SendMessageUseCase:
    """Processes a chat message by retrieving context and generating a response.
    Delegates context retrieval and LLM generation to infrastructure ports.
    """

    def __init__(
        self,
        project_repo: IProjectRepository,
        context_retriever,  # IContextRetriever port
        llm_service,  # ILLMService port
    ) -> None:
        self._project_repo = project_repo
        self._context_retriever = context_retriever
        self._llm_service = llm_service

    async def execute(self, request: SendMessageRequest) -> SendMessageResponse:
        project = await self._project_repo.get_by_id(ProjectId.from_string(request.project_id))
        if not project:
            raise ProjectNotFoundError(request.project_id)

        context = await self._context_retriever.retrieve(
            query=request.message,
            project_id=project.id,
        )

        # Build sources from context
        sources = []
        for r in context.get("relevant_code", [])[:3]:
            sources.append({
                "type": "code",
                "name": r["payload"]["name"],
                "file": r["payload"]["file_path"],
                "score": r["score"],
            })
        for r in context.get("relevant_decisions", [])[:3]:
            sources.append({
                "type": "decision",
                "name": r["payload"]["title"],
                "score": r["score"],
            })

        # If LLM is not configured, return raw context
        if not self._llm_service.is_configured:
            response = self._format_raw_context(context)
            return SendMessageResponse(
                response=response,
                sources=sources,
                project_id=request.project_id,
            )

        system_prompt = (
            "You are Forge, an AI engineering companion embedded in the developer's workflow. "
            "You have access to the project's code, architectural decisions, bug history, "
            "and developer preferences. Answer concisely with specific references when possible. "
            "If you don't know, say so."
        )

        messages = [
            {"role": "system", "content": system_prompt},
        ]

        if context.get("relevant_code"):
            code_ctx = "\n".join(
                f"- {r['payload']['name']} in {r['payload']['file_path']}"
                for r in context["relevant_code"][:5]
            )
            messages.append({
                "role": "system",
                "content": f"Relevant code:\n{code_ctx}",
            })

        if context.get("relevant_decisions"):
            dec_ctx = "\n".join(
                f"- {r['payload']['title']}: {r['payload']['decision']}"
                for r in context["relevant_decisions"][:5]
            )
            messages.append({
                "role": "system",
                "content": f"Related decisions:\n{dec_ctx}",
            })

        if context.get("relevant_bugs"):
            bug_ctx = "\n".join(
                f"- {r['payload']['title']}: {r['payload']['solution']}"
                for r in context["relevant_bugs"][:3]
            )
            messages.append({
                "role": "system",
                "content": f"Similar bugs resolved:\n{bug_ctx}",
            })

        messages.append({"role": "user", "content": request.message})

        llm_response = await self._llm_service.chat(messages)

        return SendMessageResponse(
            response=llm_response.content,
            sources=sources,
            project_id=request.project_id,
        )

    def _format_raw_context(self, context: dict) -> str:
        """Format context as readable text when no LLM is available."""
        parts = []

        if context.get("relevant_code"):
            parts.append("**Relevant code:**")
            for r in context["relevant_code"][:5]:
                name = r["payload"]["name"]
                file_path = r["payload"]["file_path"]
                parts.append(f"- {name} in {file_path}")

        if context.get("relevant_decisions"):
            parts.append("\n**Related decisions:**")
            for r in context["relevant_decisions"][:5]:
                title = r["payload"]["title"]
                decision = r["payload"]["decision"]
                parts.append(f"- {title}: {decision}")

        if context.get("relevant_bugs"):
            parts.append("\n**Similar bugs resolved:**")
            for r in context["relevant_bugs"][:3]:
                title = r["payload"]["title"]
                solution = r["payload"].get("solution", "No solution recorded")
                parts.append(f"- {title}: {solution}")

        if not parts:
            return "No relevant context found for this query. Configure an LLM API key in Settings to enable AI-powered responses."

        return "\n".join(parts)
