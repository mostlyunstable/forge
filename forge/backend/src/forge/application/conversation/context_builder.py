"""ContextBuilder — assembles context for LLM from multiple sources."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.projects.value_objects.project_id import ProjectId


@dataclass
class LLMContext:
    """Assembled context ready to be sent to LLM."""

    system_prompt: str
    history_messages: list[dict[str, str]]
    user_message: str
    sources: list[dict[str, Any]]
    total_tokens_estimate: int


class ContextBuilder:
    """Builds the full LLM context from conversation history + memory retrieval.

    Assembles:
    1. System prompt with role definition
    2. Conversation summary (if exists)
    3. Recent messages from conversation history
    4. Memory-retrieved context (code, decisions, bugs)
    5. Current user message
    """

    SYSTEM_PROMPT = (
        "You are Forge, an AI engineering companion embedded in the developer's workflow. "
        "You have access to the project's code, architectural decisions, bug history, "
        "and developer preferences. You maintain conversation context across turns. "
        "Answer concisely with specific references when possible. "
        "If you don't know, say so. "
        "When discussing code, reference specific files and functions."
    )

    def build(
        self,
        conversation: Conversation,
        user_message: str,
        memory_context: dict[str, Any] | None = None,
        max_history_tokens: int = 6000,
    ) -> LLMContext:
        """Build complete LLM context."""
        messages: list[dict[str, str]] = []

        # Add summary as system context
        if conversation.summaries:
            messages.append({
                "role": "system",
                "content": f"Previous discussion summary:\n{conversation.summaries[-1].content}",
            })

        # Add recent messages (respect token budget)
        token_budget = max_history_tokens
        recent = conversation.messages[-20:]
        for msg in reversed(recent):
            msg_tokens = msg.token_count or len(msg.content) // 4
            if msg_tokens > token_budget:
                break
            messages.insert(0, {"role": msg.role, "content": msg.content})
            token_budget -= msg_tokens

        # Add memory-retrieved context
        sources = []
        if memory_context:
            messages.extend(self._build_memory_messages(memory_context, sources))

        total_est = sum(len(m["content"]) // 4 for m in messages) + len(user_message) // 4

        return LLMContext(
            system_prompt=self.SYSTEM_PROMPT,
            history_messages=messages,
            user_message=user_message,
            sources=sources,
            total_tokens_estimate=total_est,
        )

    def _build_memory_messages(
        self, context: dict[str, Any], sources: list[dict[str, Any]]
    ) -> list[dict[str, str]]:
        """Convert memory context to LLM messages."""
        msgs = []

        if context.get("relevant_code"):
            code_ctx = "\n".join(
                f"- {r['payload']['name']} in {r['payload']['file_path']}"
                for r in context["relevant_code"][:5]
            )
            msgs.append({"role": "system", "content": f"Relevant code:\n{code_ctx}"})
            for r in context["relevant_code"][:3]:
                sources.append({
                    "type": "code",
                    "name": r["payload"]["name"],
                    "file": r["payload"]["file_path"],
                    "score": r["score"],
                })

        if context.get("relevant_decisions"):
            dec_ctx = "\n".join(
                f"- {r['payload']['title']}: {r['payload']['decision']}"
                for r in context["relevant_decisions"][:5]
            )
            msgs.append({"role": "system", "content": f"Related decisions:\n{dec_ctx}"})
            for r in context["relevant_decisions"][:3]:
                sources.append({
                    "type": "decision",
                    "name": r["payload"]["title"],
                    "score": r["score"],
                })

        if context.get("relevant_bugs"):
            bug_ctx = "\n".join(
                f"- {r['payload']['title']}: {r['payload']['solution']}"
                for r in context["relevant_bugs"][:3]
            )
            msgs.append({"role": "system", "content": f"Similar bugs resolved:\n{bug_ctx}"})
            for r in context["relevant_bugs"][:2]:
                sources.append({
                    "type": "bug",
                    "name": r["payload"]["title"],
                    "score": r["score"],
                })

        return msgs
