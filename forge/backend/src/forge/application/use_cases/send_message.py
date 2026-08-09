from typing import Any, AsyncGenerator

from forge.application.conversation.context_manager import (
    ConversationContextManager,
    RetrievedContext,
)
from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.application.conversation.token_manager import ContextWindow
from forge.application.ports.llm_provider import ILLMProvider
from forge.application.ports import IContextRetriever
from forge.domain.conversation.entities.message import Message
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository

class SendMessageUseCase:
    def __init__(
        self,
        conversation_repo: IConversationRepository,
        retriever: IContextRetriever,
        llm_provider: ILLMProvider,
    ):
        self._conversation_repo = conversation_repo
        self._retriever = retriever
        self._llm_provider = llm_provider
        self._reasoning_engine = ReasoningEngine(llm_provider)

    async def execute(self, conversation_id: str, message: str) -> AsyncGenerator[dict[str, Any], None]:
        conv_id = ConversationId.from_string(conversation_id)

        # 1. Fetch conversation
        conversation = await self._conversation_repo.get_by_id(conv_id)
        if not conversation:
            raise ValueError("Conversation not found")

        # Save user message first
        user_msg = Message.create_user(
            conversation_id=conv_id,
            content=message,
            token_count=max(1, len(message) // 4),
        )
        conversation.add_message(user_msg)
        await self._conversation_repo.save(conversation)

        # 3. Retrieve memory/context
        retrieval_result = await self._retriever.retrieve(
            query=message, project_id=conversation.project_id, context_window=None
        )

        retrieved_contexts = []
        for t in ["relevant_code", "relevant_decisions", "relevant_bugs"]:
            for res in retrieval_result.get(t, []):
                content = res.get("payload", {}).get("content", "")
                source = (
                    res.get("payload", {}).get("file_path", "")
                    or res.get("payload", {}).get("title", "")
                    or "unknown"
                )
                retrieved_contexts.append(
                    RetrievedContext(source=source, content=content, score=res.get("score", 1.0))
                )

        # 2/4. Build context window
        context_manager = ConversationContextManager(self._conversation_repo)
        assembled_context = await context_manager.build_context(conv_id, retrieved_contexts)

        messages_for_llm = []
        for m in assembled_context["messages"]:
            if m["role"] == "user":
                messages_for_llm.append(
                    Message.create_user(
                        conversation_id=conv_id, content=m["content"], token_count=1
                    )
                )
            elif m["role"] == "assistant":
                messages_for_llm.append(
                    Message.create_assistant(
                        conversation_id=conv_id, content=m["content"], token_count=1
                    )
                )

        context_window = ContextWindow(
            summary=assembled_context["summary"],
            summary_tokens=0,
            messages=messages_for_llm,
            message_tokens=0,
            total_tokens=assembled_context["total_tokens_estimated"],
        )

        retrieved_context_str = "\n\n".join(
            [f"Source: {ctx['source']}\n{ctx['content']}" for ctx in assembled_context["retrieved"]]
        )

        # 4/5. Stream reasoning engine chunks
        full_response = ""
        citations = [
            {"source": ctx["source"], "content": ctx["content"], "score": ctx["score"]}
            for ctx in assembled_context["retrieved"]
        ]
        
        # We'll emit a chunk with citations first if needed, but UI typically gets it from standard chunks.
        # Wait, the frontend might expect specific format. Let's look at `generate_response_stream` output.
        # It yields dicts like {"type": "text", "content": ...}
        
        generator = self._reasoning_engine.generate_response_stream(
            context_window=context_window, retrieved_context=retrieved_context_str
        )
        
        async for chunk in generator:
            if chunk.get("type") == "text":
                full_response += chunk.get("content", "")
            yield chunk

        # 5/6. Save messages to DB
        assistant_msg = Message.create_assistant(
            conversation_id=conv_id,
            content=full_response,
            token_count=max(1, len(full_response) // 4),
        )
        conversation.add_message(assistant_msg)
        await self._conversation_repo.save(conversation)
