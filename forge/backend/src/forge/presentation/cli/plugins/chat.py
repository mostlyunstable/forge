import asyncio
import uuid
from pathlib import Path

import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.styles import Style
from rich.console import Console
from rich.live import Live
from rich.markdown import Markdown

from forge.application.conversation.context_manager import ConversationContextManager
from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.application.conversation.token_manager import ContextWindow
from forge.domain.conversation.entities.message import Message
from forge.infrastructure.database.connection import database_manager
from forge.infrastructure.llm.llm_service import LLMService
from forge.infrastructure.repositories.conversation_repository import ConversationRepository
from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.infrastructure.search.sqlite_retriever import SqliteRetriever

console = Console()

# ── DB helpers (short-lived sessions each) ────────────────────────────────────


async def _get_or_create_project():
    async with database_manager.get_session() as db:
        repo = ProjectRepository(db)
        projects = await repo.get_all()
        if projects:
            return projects[0].id
    from forge.domain.projects.value_objects.project_id import ProjectId

    return ProjectId(uuid.uuid4())


async def _create_conversation(project_id):
    from forge.domain.conversation.entities.conversation import Conversation

    async with database_manager.get_session() as db:
        repo = ConversationRepository(db)
        conv = Conversation.create(project_id=project_id, title="CLI Chat Session")
        await repo.save(conv)
        return conv.id


async def _get_conversation(conversation_id):
    async with database_manager.get_session() as db:
        repo = ConversationRepository(db)
        return await repo.get_by_id(conversation_id)


async def _save_conversation(conversation):
    async with database_manager.get_session() as db:
        repo = ConversationRepository(db)
        await repo.save(conversation)


async def _build_context(conversation_id, retrieved):
    async with database_manager.get_session() as db:
        repo = ConversationRepository(db)
        mgr = ConversationContextManager(repo)
        return await mgr.build_context(conversation_id, retrieved)


def _resolve_db_path() -> Path:
    """Find forge.db from this file's location."""
    here = Path(__file__).resolve()
    for parent in here.parents:
        candidate = parent / "forge.db"
        if candidate.exists():
            return candidate
    # Default: relative to backend dir
    return here.parent.parent.parent.parent.parent / "forge.db"


# ── Main chat coroutine ───────────────────────────────────────────────────────


async def run_chat():
    session_prompt = PromptSession(
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory(),
        style=Style.from_dict({"prompt": "ansicyan bold"}),
    )

    console.print("[bold cyan]╔══════════════════════════════════════╗[/bold cyan]")
    console.print("[bold cyan]║        FORGE  —  AI Engineering      ║[/bold cyan]")
    console.print("[bold cyan]╚══════════════════════════════════════╝[/bold cyan]")
    console.print(
        "Type [bold yellow]/help[/bold yellow] for commands • [bold yellow]/exit[/bold yellow] to quit\n"
    )

    current_conversation_id = None
    recent_citations: list[dict] = []

    # Stateless services
    llm_service = LLMService()
    reasoning_engine = ReasoningEngine(llm_service)
    retriever = SqliteRetriever()

    db_path = _resolve_db_path()
    indexed = db_path.exists()
    if not indexed:
        console.print(
            "[bold yellow]⚠  Codebase not indexed yet.[/bold yellow] "
            "Run [bold]python forge_index.py[/bold] from forge/backend/ to enable retrieval.\n"
        )
    else:
        console.print(f"[dim]✓ Codebase index found at {db_path}[/dim]\n")

    project_id = await _get_or_create_project()

    while True:
        image_metadata = None
        try:
            text = await session_prompt.prompt_async("forge> ")
        except (EOFError, KeyboardInterrupt):
            console.print("\n[bold green]Goodbye![/bold green]")
            break

        text = text.strip()
        if not text:
            continue

        # ── Slash commands ────────────────────────────────────────────────────
        if text.startswith("/"):
            cmd = text.split()[0]

            if cmd == "/exit":
                console.print("[bold green]Goodbye![/bold green]")
                break

            elif cmd == "/help":
                help_text = """
        Command /help      : Show this help message
        Command /new       : Start a fresh conversation
        Command /history   : View conversation history
        Command /context   : Show assembled LLM context
        Command /citations : Show last retrieval sources
        Command /summary   : Show conversation summary
        Command /export    : Export conversation to markdown
        Command /index     : Run the Knowledge Ingester to index the codebase
        Command /learn     : Manually add a permanent rule for Forge to remember
        Command /rate      : Rate the current conversation (1-5) for fine-tuning
        Command /clear     : Clear screen
        Command /exit      : Exit the application
        """
                console.print(help_text)
                continue

            elif cmd == "/clear":
                console.clear()
                continue

            elif cmd == "/index":
                console.print("[dim italic]Indexing codebase...[/dim italic]")
                import sys
                from pathlib import Path

                backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
                db_path = str(backend_dir / "forge.db")

                # Add to path if needed and import
                from forge.application.training.knowledge_ingester import KnowledgeIngester

                ingester = KnowledgeIngester(db_path=db_path)
                # Use asyncio event loop since we are in async main
                stats = await ingester.ingest()
                console.print(
                    f"[green]✅ Codebase indexed![/green] Processed {stats['files_processed']} files into {stats['entries_written']} chunks."
                )
                continue

            elif text.startswith("/learn"):
                rule = text[6:].strip()
                if not rule:
                    console.print("[red]Usage: /learn <rule description>[/red]")
                    continue

                from pathlib import Path

                backend_dir = Path(__file__).resolve().parent.parent.parent.parent.parent
                forge_dir = backend_dir.parent
                rules_path = forge_dir / ".forge_rules.md"

                existing = ""
                if rules_path.exists():
                    existing = rules_path.read_text(encoding="utf-8")

                new_content = existing + f"\n- {rule}" if existing else f"- {rule}"
                rules_path.write_text(new_content, encoding="utf-8")

                console.print(f"[green]✅ Learned new rule:[/green] {rule}")
                continue

            elif text.startswith("/rate"):
                try:
                    rating = int(text[5:].strip())
                    if rating < 1 or rating > 5:
                        raise ValueError()
                except ValueError:
                    console.print("[red]Usage: /rate <1-5>[/red]")
                    continue

                if not current_conversation_id:
                    console.print("[dim]No active conversation to rate.[/dim]")
                    continue

                conv = await _get_conversation(current_conversation_id)
                if conv:
                    conv.metadata["rating"] = rating
                    await _save_conversation(conv)
                    console.print(f"[green]✅ Rated conversation {rating}/5 stars![/green]")
                continue

            elif cmd == "/new" or cmd == "/delete":
                current_conversation_id = None
                recent_citations = []
                console.print("[bold green]✓ New conversation started.[/bold green]")
                continue

            elif cmd == "/history":
                if not current_conversation_id:
                    console.print("[dim]No active conversation.[/dim]")
                else:
                    conv = await _get_conversation(current_conversation_id)
                    if conv:
                        for msg in conv.messages:
                            role_color = "cyan" if msg.role == "user" else "green"
                            console.print(
                                f"[bold {role_color}]{msg.role}:[/bold {role_color}] {msg.content}\n"
                            )

            elif cmd == "/context":
                if not current_conversation_id:
                    console.print("[dim]No active conversation.[/dim]")
                else:
                    assembled = await _build_context(current_conversation_id, [])
                    console.print(assembled)

            elif cmd == "/citations":
                if not recent_citations:
                    console.print("[dim]No citations from last response.[/dim]")
                else:
                    for c in recent_citations:
                        console.print(
                            f"[bold cyan]{c['file_path']}[/bold cyan]\n[dim]{c['content'][:200]}[/dim]\n"
                        )

            elif cmd == "/summary":
                if not current_conversation_id:
                    console.print("[dim]No active conversation.[/dim]")
                else:
                    conv = await _get_conversation(current_conversation_id)
                    if conv and conv.summaries:
                        console.print(Markdown(conv.summaries[-1].content))
                    else:
                        console.print("[dim]No summary yet.[/dim]")

            elif cmd == "/export":
                if not current_conversation_id:
                    console.print("[dim]No active conversation.[/dim]")
                else:
                    conv = await _get_conversation(current_conversation_id)
                    if conv:
                        content = "\n\n".join(
                            f"### {m.role.upper()}\n\n{m.content}" for m in conv.messages
                        )
                        fname = f"forge_chat_{current_conversation_id.value}.md"
                        Path(fname).write_text(content)
                        console.print(f"[bold green]✓ Exported to {fname}[/bold green]")

            elif cmd == "/index":
                console.print("[dim]Indexing codebase… this may take a moment.[/dim]")
                import subprocess
                import sys

                result = subprocess.run(
                    [sys.executable, "forge_index.py"], capture_output=True, text=True
                )
                console.print(result.stdout or result.stderr)

            elif text.startswith("/image"):
                import base64
                import mimetypes

                parts = text.split(maxsplit=2)
                if len(parts) < 2:
                    console.print("[red]Usage: /image <path> [prompt][/red]")
                    continue

                image_path = Path(parts[1]).resolve()
                if not image_path.exists():
                    console.print(f"[red]Error: Image not found at {image_path}[/red]")
                    continue

                mime_type, _ = mimetypes.guess_type(image_path)
                if not mime_type or not mime_type.startswith("image/"):
                    mime_type = "image/jpeg"

                try:
                    with open(image_path, "rb") as f:
                        b64_data = base64.b64encode(f.read()).decode("utf-8")
                    image_url = f"data:{mime_type};base64,{b64_data}"
                except Exception as e:
                    console.print(f"[red]Error reading image: {e}[/red]")
                    continue

                prompt = parts[2] if len(parts) > 2 else "Analyze this image."

                # We need to process this message normally, but inject the metadata
                text = prompt
                # Let's set a flag to inject this image_url in the message creation phase below
                console.print(f"[dim]📎 Attached image: {image_path.name}[/dim]")

                # Jump down to message processing directly for this specific case
                image_metadata = {"image_url": image_url}
                # But wait, we need to pass this metadata to the message creation block!
                pass  # We'll just break out of slash command block and handle it below

            else:
                console.print(f"[bold red]Unknown command: {cmd}[/bold red]  — type /help")

            if not text.startswith("/image"):
                continue

        # ── Message processing ────────────────────────────────────────────────

        # Create conversation on first message
        if not current_conversation_id:
            current_conversation_id = await _create_conversation(project_id)

        # Persist user message
        conversation = await _get_conversation(current_conversation_id)
        if not conversation:
            console.print("[bold red]Error: conversation lost.[/bold red]")
            continue

        user_msg = Message.create_user(
            conversation_id=current_conversation_id,
            content=text,
            token_count=max(1, len(text) // 4),
            metadata=image_metadata,
        )
        conversation.add_message(user_msg)
        await _save_conversation(conversation)

        # ── Retrieval ─────────────────────────────────────────────────────────
        retrieved_results = await retriever.retrieve(text)
        recent_citations = retrieved_results
        retrieved_context_str = retriever.format_for_llm(retrieved_results)

        if retrieved_results:
            console.print(f"[dim]📚 Retrieved {len(retrieved_results)} relevant snippets[/dim]")

        # ── Build context window ──────────────────────────────────────────────
        try:
            assembled = await _build_context(current_conversation_id, [])

            messages_for_llm = []
            for m in assembled["messages"]:
                if m["role"] == "user":
                    messages_for_llm.append(
                        Message.create_user(
                            conversation_id=current_conversation_id,
                            content=m["content"],
                            token_count=1,
                            metadata=m.get("metadata", {}),
                        )
                    )
                elif m["role"] == "assistant":
                    messages_for_llm.append(
                        Message.create_assistant(
                            conversation_id=current_conversation_id,
                            content=m["content"],
                            token_count=1,
                            metadata=m.get("metadata", {}),
                        )
                    )
                elif m["role"] == "system":
                    # Reconstruct system/tool messages if present
                    msg = Message.create_system(current_conversation_id, m["content"], 1)
                    msg.metadata = m.get("metadata", {})
                    messages_for_llm.append(msg)
                elif m["role"] == "tool":
                    msg = Message.create_tool(
                        current_conversation_id,
                        m["content"],
                        m.get("metadata", {}).get("tool_call_id", ""),
                        m.get("metadata", {}).get("name", ""),
                        1,
                    )
                    messages_for_llm.append(msg)

            context_window = ContextWindow(
                summary=assembled["summary"],
                summary_tokens=0,
                messages=messages_for_llm,
                message_tokens=0,
                total_tokens=assembled["total_tokens_estimated"],
            )

            # ── Stream LLM response ───────────────────────────────────────────
            with Live(Markdown("▋"), console=console, refresh_per_second=15) as live:
                current_text = ""
                async for chunk in reasoning_engine.generate_response_stream(
                    context_window=context_window,
                    retrieved_context=retrieved_context_str,
                ):
                    if isinstance(chunk, dict):
                        if chunk["type"] == "status":
                            live.stop()
                            console.print(f"[dim italic]⚙️ {chunk['message']}[/dim italic]")
                            live.start()
                        elif chunk["type"] == "text":
                            current_text += chunk["content"]
                            live.update(Markdown(current_text + " ▋"))
                    else:
                        current_text += str(chunk)
                        live.update(Markdown(current_text + " ▋"))
                live.update(Markdown(current_text))

            # Persist assistant reply
            conversation = await _get_conversation(current_conversation_id)
            assistant_msg = Message.create_assistant(
                conversation_id=current_conversation_id,
                content=current_text,
                token_count=max(1, len(current_text) // 4),
            )
            conversation.add_message(assistant_msg)
            await _save_conversation(conversation)

            console.print()

        except Exception as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
            import traceback

            console.print(f"[dim]{traceback.format_exc()}[/dim]")


# ── Typer registration ────────────────────────────────────────────────────────


def register(app: typer.Typer):
    @app.command("chat")
    def chat_cmd():
        """Interactive chat with retrieval-augmented context."""
        asyncio.run(run_chat())
