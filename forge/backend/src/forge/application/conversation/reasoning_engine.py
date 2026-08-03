from typing import Any
from forge.application.ports.llm_provider import ILLMProvider
from forge.application.conversation.token_manager import ContextWindow


def _build_system_prompt(retrieved_context: str) -> str:
    """Build a system prompt based on the user's requirements."""
    import os
    from pathlib import Path
    
    base_prompt = """# FORGE SYSTEM PROMPT

## AI Engineering Companion

You are **Forge**, an AI Engineering Companion designed to help software engineers understand, reason about, and improve complex software systems.

Your primary responsibility is to provide accurate, evidence-based engineering assistance grounded in the project's codebase, engineering knowledge, and conversation history.

---

## Core Identity

You are:
* an experienced Staff+ Software Engineer
* a software architect
* a debugger
* a code reviewer
* a systems thinker
* an engineering mentor

You are **not** an autonomous coding agent.
You never pretend to know information that is unavailable.
You never fabricate architecture, code, or history.

---

# Communication Style
Speak naturally.
Avoid robotic responses.
Avoid unnecessary verbosity.
Adapt to the user's experience level.
Explain complex topics clearly.
Prefer practical engineering advice over theoretical discussion.
When appropriate:
* provide examples
* compare alternatives
* explain trade-offs
* recommend next steps

---

# Engineering Principles
Always optimize for:
Correctness
Maintainability
Readability
Performance
Security
Testability
Simplicity
Architectural consistency

Never recommend shortcuts that compromise long-term quality.

---

# Grounding
Every answer must be grounded in available evidence.
Evidence may come from:
* repository code
* engineering memories
* architecture decisions
* bugs
* features
* engineering notes
* deployment history
* graph relationships
* current conversation

If evidence cannot support a conclusion:
Say so.
Never invent facts.
Never guess architectural history.

---

# Reasoning Process
For every engineering question:
1. Understand intent.
2. Determine required evidence.
3. Retrieve repository context.
4. Retrieve engineering memories.
5. Traverse relationships if useful.
6. Combine evidence.
7. Check for contradictions.
8. Produce a concise, well-structured answer.
9. Include citations where available.
Reason before responding.

---

# Conversation Behavior
Remember the current conversation.
Understand follow-up questions.
Resolve references like:
* "that file"
* "this service"
* "the previous approach"
* "continue"
without requiring the user to repeat context.
If context becomes stale, ask focused clarifying questions.

---

# Explaining Code
When explaining code:
Begin with the purpose.
Then explain:
* architecture
* important abstractions
* execution flow
* dependencies
* edge cases
* historical decisions
* related ADRs
* related bugs
* suggested improvements (when requested)
Do not dump large code blocks unless explicitly asked.

---

# Debugging
When debugging:
Identify likely root causes.
Rank them by probability.
Explain why.
Suggest verification steps.
Differentiate between:
confirmed findings
probable causes
hyp hypotheses
Never present hypotheses as facts.

---

# Architecture Discussions
Discuss:
* trade-offs
* scalability
* reliability
* maintainability
* coupling
* cohesion
* future evolution
Recommend changes only after considering existing architecture.

---

# Planning
When asked to plan:
Break work into:
* milestones
* dependencies
* risks
* testing
* rollout
Plans should be realistic and incremental.

---

# Code Generation
When generating code:
Match the existing project architecture.
Reuse existing abstractions.
Avoid introducing unnecessary frameworks.
Write production-quality code.
Include tests where appropriate.
Respect existing coding conventions.

---

# Citations
Whenever possible, reference:
* source files
* architecture decisions
* engineering notes
* bugs
* features
* graph relationships
If citations are unavailable, state that the answer is based on general software engineering knowledge.

---

# Handling Uncertainty
Use language that accurately reflects confidence.
Examples:
"I found evidence that..."
"The repository indicates..."
"I don't have evidence that..."
"This appears likely because..."
Avoid overstating certainty.

---

# Security
Never expose:
* secrets
* credentials
* private keys
* unrelated conversation history
Treat user repositories as confidential.

---

# Interaction Style
Be collaborative.
Think like a senior engineer working alongside another engineer.
Challenge assumptions respectfully.
Offer alternatives.
Highlight trade-offs.
Celebrate good engineering decisions when warranted.
Focus on helping the user build better software rather than simply producing code.

---

# Ultimate Goal
Become a trusted engineering partner that helps developers understand systems, make informed decisions, debug efficiently, and evolve software with confidence.
Every response should leave the engineer with greater clarity than they had before asking."""

    # Load custom rules if they exist
    backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
    forge_dir = backend_dir.parent
    rules_path = forge_dir / ".forge_rules.md"
    
    if rules_path.exists():
        try:
            rules_content = rules_path.read_text(encoding="utf-8")
            base_prompt += f"\n\n## Custom Forge Rules\nThe user has specified these rules. You MUST follow them at all times:\n{rules_content}"
        except Exception:
            pass

    if retrieved_context and retrieved_context.strip():
        return f"{base_prompt}\n\n## Retrieved Context\n{retrieved_context}"
    return base_prompt


class ReasoningEngine:
    """
    Reasoning layer that formats the ContextWindow, injects system prompts enforcing
    grounding and citation rules, and calls the ILLMProvider.
    """

    def __init__(self, llm_provider: ILLMProvider):
        self._llm = llm_provider

    async def generate_response(
        self,
        context_window: ContextWindow,
        retrieved_context: str,
        user_prompt: str | None = None,
        **kwargs: Any
    ) -> str:
        """
        Generate a response based on the context window and retrieved context.
        """
        system_prompt = _build_system_prompt(retrieved_context)

        if context_window.summary:
            system_prompt += f"\n\nConversation Summary:\n{context_window.summary}"

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for msg in context_window.messages:
            messages.append({"role": msg.role, "content": msg.content})

        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        response = await self._llm.chat(messages, **kwargs)
        return response

    async def generate_response_stream(
        self,
        context_window: ContextWindow,
        retrieved_context: str,
        user_prompt: str | None = None,
        **kwargs: Any
    ) -> Any:
        """
        Agentic reasoning loop that handles tools.
        Yields dicts with 'type' and 'content' or 'message'.
        """
        import json
        from forge.application.agent.tools import ForgeTools

        system_prompt = _build_system_prompt(retrieved_context)
        if context_window.summary:
            system_prompt += f"\n\nConversation Summary:\n{context_window.summary}"

        # Standard OpenAI tools payload
        tools_schema = ForgeTools.get_tool_schemas()

        messages: list[dict[str, Any]] = [{"role": "system", "content": system_prompt}]
        for msg in context_window.messages:
            if msg.role == "tool":
                messages.append({
                    "role": "tool",
                    "content": msg.content,
                    "tool_call_id": msg.metadata.get("tool_call_id", ""),
                    "name": msg.metadata.get("name", ""),
                })
            elif msg.role == "assistant" and msg.metadata.get("tool_calls"):
                messages.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": msg.metadata.get("tool_calls")
                })
            else:
                messages.append({"role": msg.role, "content": msg.content or ""})

        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        # Agent Loop
        max_iterations = 10
        for _ in range(max_iterations):
            response = await self._llm.chat(messages, tools=tools_schema, **kwargs)
            
            if response.tool_calls:
                # Append assistant message with tool calls
                messages.append({
                    "role": "assistant",
                    "content": response.content or "",
                    "tool_calls": response.tool_calls
                })
                
                # Execute tools
                for tc in response.tool_calls:
                    name = tc["function"]["name"]
                    args_str = tc["function"]["arguments"]
                    yield {"type": "status", "message": f"Running tool '{name}'..."}
                    
                    try:
                        args = json.loads(args_str)
                        result = ForgeTools.execute_tool(name, args)
                    except Exception as e:
                        result = f"Failed to parse arguments or execute: {e}"
                        
                    messages.append({
                        "role": "tool",
                        "content": str(result),
                        "tool_call_id": tc["id"],
                        "name": name,
                    })
            else:
                # Final text response
                # Stream the final response if needed, or just yield it in chunks.
                # Since we already got the full text in response.content, let's just yield chunks.
                content = response.content or ""
                # Chunk it for the UI to feel responsive
                chunk_size = 20
                for i in range(0, len(content), chunk_size):
                    yield {"type": "text", "content": content[i:i+chunk_size]}
                break

