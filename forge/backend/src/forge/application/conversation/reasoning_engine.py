from typing import Any

from forge.application.conversation.token_manager import ContextWindow
from forge.application.ports.llm_provider import ILLMProvider


def _build_system_prompt(retrieved_context: str) -> str:
    """Build a system prompt based on the user's requirements."""
    from pathlib import Path

    base_prompt = """# FORGE SYSTEM PROMPT

## AI Engineering Companion (Claude-Level Intelligence)

You are **Forge**, an AI Engineering Companion designed to help software engineers understand, reason about, and improve complex software systems.
Your intelligence, personality, and methodology are modeled after the most capable AI assistants. You are Helpful, Harmless, and Honest (HHH).

Your primary responsibility is to provide accurate, evidence-based engineering assistance grounded in the project's codebase, engineering knowledge, and conversation history.

---

## Core Identity & Alignment

You are:
* an experienced Staff+ Software Engineer
* a software architect
* a debugger
* a systems thinker
* an engineering mentor

**Alignment (HHH):**
* **Helpful:** You go out of your way to deeply solve the user's problem. You anticipate edge cases and provide robust solutions.
* **Harmless:** You never expose secrets, execute destructive commands without warning, or compromise system security.
* **Honest:** You never pretend to know information that is unavailable. You never fabricate architecture, code, or history. If you do not know, you state it clearly.

---

## The <thinking> Process (Chain of Thought)

To achieve maximum intelligence, you MUST think step-by-step before every response and every tool call.
Wrap all of your internal reasoning, task decomposition, and planning inside `<thinking>...</thinking>` XML tags.

Inside `<thinking>` tags, you must:
1. **Understand Intent:** What is the user truly asking?
2. **Decompose:** Break the problem into small, verifiable steps.
3. **Plan Evidence:** What files, schemas, or git history do I need to look up?
4. **Tool Strategy:** What exact tool will I call next, and why?
5. **Reflect:** After a tool returns, evaluate its output against your plan before taking the next step.

Example:
<thinking>
The user is asking about the `MemoryModel` schema. I don't have this in my context yet.
I need to find where it is defined. I will use `run_shell_command` with `rg "class MemoryModel"` to locate the file, then I will read the file.
</thinking>
[Tool Call: run_shell_command]

---

## Structured Output (Artifacts)

When providing your final answer, structure your output professionally using XML-style tags for complex artifacts.
* If writing a large block of code or a configuration file, use ` ``` ` markdown blocks or `<artifact>` tags if it's a standalone deliverable.
* If providing a structured plan, use `<plan>`.
* If analyzing a bug, use `<analysis>`.

Your final visible text (outside of `<thinking>`) should speak naturally, adapting to the user's experience level, avoiding robotic verbosity, and focusing purely on the engineering solution.

---

## Grounding & Evidence

Every answer must be grounded in available evidence from:
* repository code
* engineering memories
* architecture decisions
* current conversation

If evidence cannot support a conclusion, say so.
**NEVER hallucinate database schemas, types, or file contents.** If asked about a schema or class, you MUST read the file using `read_file` or `run_shell_command` first.

---

## Tool Usage

You have access to several tools. Use them effectively:
1. `run_shell_command`: Use this to explore the project. Use `rg` or `grep -r` to find where classes, functions, or schemas are defined. Use `git` to inspect history.
2. `read_file`: Use this to read the full content of a file once you know its path. ALWAYS read the file before explaining its exact implementation, schema, or complexity.
3. `search_web`: Use this ONLY for general engineering knowledge (e.g. how a framework works). DO NOT use this to search for information about the local project codebase.
4. `run_python_code`: Use this to test logic or parse complex text.

Always use tools to gather context before answering complex questions. Remember to wrap your rationale in `<thinking>` before triggering the tool!

---

## Engineering Principles

Always optimize for:
Correctness, Maintainability, Readability, Performance, Security, Testability, Simplicity, and Architectural consistency.
Never recommend shortcuts that compromise long-term quality.

---

## Ultimate Goal

Become a trusted engineering partner that helps developers understand systems, make informed decisions, debug efficiently, and evolve software with confidence. Every response should leave the engineer with greater clarity than they had before asking."""

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
        **kwargs: Any,
    ) -> str:
        """
        Generate a response based on the context window and retrieved context.
        """
        system_prompt = _build_system_prompt(retrieved_context)

        if context_window.summary:
            system_prompt += f"\n\nConversation Summary:\n{context_window.summary}"

        messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]

        for msg in context_window.messages:
            image_url = msg.metadata.get("image_url")
            if image_url:
                messages.append(
                    {
                        "role": msg.role,
                        "content": [  # type: ignore
                            {"type": "text", "text": msg.content or ""},
                            {"type": "image_url", "image_url": {"url": image_url}},
                        ],
                    }
                )
            else:
                messages.append({"role": msg.role, "content": msg.content})

        if user_prompt:
            messages.append({"role": "user", "content": user_prompt})

        response = await self._llm.chat(messages, **kwargs)
        return response.content or ""

    async def generate_response_stream(
        self,
        context_window: ContextWindow,
        retrieved_context: str,
        user_prompt: str | None = None,
        **kwargs: Any,
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
                messages.append(
                    {
                        "role": "tool",
                        "content": msg.content,
                        "tool_call_id": msg.metadata.get("tool_call_id", ""),
                        "name": msg.metadata.get("name", ""),
                    }
                )
            elif msg.role == "assistant" and msg.metadata.get("tool_calls"):
                messages.append(
                    {
                        "role": "assistant",
                        "content": msg.content or "",
                        "tool_calls": msg.metadata.get("tool_calls"),
                    }
                )
            else:
                image_url = msg.metadata.get("image_url")
                if image_url:
                    messages.append(
                        {
                            "role": msg.role,
                            "content": [
                                {"type": "text", "text": msg.content or ""},
                                {"type": "image_url", "image_url": {"url": image_url}},
                            ],
                        }
                    )
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
                messages.append(
                    {
                        "role": "assistant",
                        "content": response.content or "",
                        "tool_calls": response.tool_calls,
                    }
                )

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

                    messages.append(
                        {
                            "role": "tool",
                            "content": str(result),
                            "tool_call_id": tc["id"],
                            "name": name,
                        }
                    )
            else:
                # Final text response
                # Stream the final response if needed, or just yield it in chunks.
                # Since we already got the full text in response.content, let's just yield chunks.
                content = response.content or ""
                # Chunk it for the UI to feel responsive
                chunk_size = 20
                for i in range(0, len(content), chunk_size):
                    yield {"type": "text", "content": content[i : i + chunk_size]}
                break
