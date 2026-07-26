import asyncio
import uuid
import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.live import Live
from prompt_toolkit import PromptSession
from prompt_toolkit.history import InMemoryHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.styles import Style

from forge.infrastructure.database.connection import database_manager
from forge.infrastructure.repositories.conversation_repository import ConversationRepository
from forge.infrastructure.repositories.project_repository import ProjectRepository
from forge.application.conversation.context_manager import ConversationContextManager, RetrievedContext
from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.application.conversation.token_manager import TokenManager, ContextWindow
from forge.infrastructure.llm.llm_service import LLMService
from forge.domain.conversation.entities.message import Message
from forge.domain.conversation.value_objects.conversation_id import ConversationId

console = Console()

async def run_chat():
    session_prompt = PromptSession(
        history=InMemoryHistory(),
        auto_suggest=AutoSuggestFromHistory(),
        style=Style.from_dict({
            'prompt': 'ansicyan bold',
        })
    )

    console.print("[bold green]Forge Chat Mode[/bold green]")
    console.print("Type [bold yellow]/help[/bold yellow] for a list of commands.")
    console.print("Use [bold yellow]Option-Enter[/bold yellow] or [bold yellow]Esc-Enter[/bold yellow] for multiline input. Press [bold yellow]Enter[/bold yellow] to submit.")
    
    current_conversation_id = None
    project_id = None
    recent_citations = []
    
    # Initialize Dependencies
    async with database_manager.get_session() as db_session:
        conv_repo = ConversationRepository(db_session)
        project_repo = ProjectRepository(db_session)
        context_manager = ConversationContextManager(conv_repo)
        llm_service = LLMService()
        reasoning_engine = ReasoningEngine(llm_service)
        
        # We need a project to attach to, fetch first available or use a dummy if not found
        projects = await project_repo.list_all()
        if projects:
            project_id = projects[0].id
        else:
            project_id = str(uuid.uuid4())
            # Would need to insert a project ideally

        while True:
            try:
                # Use multiline if needed, prompt_toolkit supports Esc+Enter for multiline naturally if configured
                text = await session_prompt.prompt_async("forge> ")
            except (EOFError, KeyboardInterrupt):
                break

            text = text.strip()
            if not text:
                continue

            if text.startswith("/"):
                # Handle slash commands
                parts = text.split(" ")
                cmd = parts[0]
                if cmd == "/exit":
                    console.print("[bold green]Goodbye![/bold green]")
                    break
                elif cmd == "/help":
                    console.print(Markdown(
"""
**Slash Commands:**
- `/clear`: Clear terminal screen
- `/new`: Start a new conversation
- `/history`: View conversation history
- `/context`: View current conversation context
- `/citations`: View recent citations
- `/summary`: View current conversation summary
- `/export`: Export conversation to markdown
- `/help`: Show this help message
- `/exit`: Exit chat
"""
                    ))
                    continue
                elif cmd == "/clear":
                    console.clear()
                    continue
                elif cmd == "/new":
                    current_conversation_id = None
                    recent_citations = []
                    console.print("[bold green]Started a new conversation.[/bold green]")
                    continue
                elif cmd == "/history":
                    if not current_conversation_id:
                        console.print("No active conversation.")
                        continue
                    conv = await conv_repo.get_by_id(current_conversation_id)
                    if conv:
                        for msg in conv.messages:
                            console.print(f"**{msg.role}**: {msg.content}")
                    continue
                elif cmd == "/context":
                    if not current_conversation_id:
                        console.print("No active conversation.")
                        continue
                    assembled = await context_manager.build_context(current_conversation_id, [])
                    console.print(assembled)
                    continue
                elif cmd == "/citations":
                    if not recent_citations:
                        console.print("No citations in the recent response.")
                    else:
                        for c in recent_citations:
                            console.print(f"Source: {c['source']}\nScore: {c['score']}\nSnippet: {c['content'][:100]}...\n")
                    continue
                elif cmd == "/summary":
                    if not current_conversation_id:
                        console.print("No active conversation.")
                        continue
                    conv = await conv_repo.get_by_id(current_conversation_id)
                    if conv and conv.summary:
                        console.print(Markdown(conv.summary))
                    else:
                        console.print("No summary available yet.")
                    continue
                elif cmd == "/export":
                    if not current_conversation_id:
                        console.print("No active conversation.")
                        continue
                    conv = await conv_repo.get_by_id(current_conversation_id)
                    export_content = ""
                    if conv:
                        for msg in conv.messages:
                            export_content += f"### {msg.role.upper()}\n\n{msg.content}\n\n"
                        filename = f"conversation_{current_conversation_id.value}.md"
                        with open(filename, "w") as f:
                            f.write(export_content)
                        console.print(f"[bold green]Exported to {filename}[/bold green]")
                    continue
                else:
                    console.print(f"[bold red]Unknown command: {cmd}[/bold red]")
                    continue
            
            # Normal message processing
            if not current_conversation_id:
                # Start new session
                from forge.domain.conversation.entities.conversation import Conversation
                conv = Conversation.create(project_id=project_id, title="CLI Chat Session")
                await conv_repo.save(conv)
                current_conversation_id = conv.id
            
            conversation = await conv_repo.get_by_id(current_conversation_id)
            if not conversation:
                console.print("[bold red]Error: Conversation missing![/bold red]")
                continue
            
            user_msg = Message.create_user(
                conversation_id=str(current_conversation_id.value),
                content=text,
                token_count=max(1, len(text) // 4)
            )
            conversation.add_message(user_msg)
            await conv_repo.save(conversation)
            
            # Simple mock retrieval for CLI demonstration (this would use ContextRetriever in real scenario)
            retrieved_contexts = []
            
            try:
                assembled_context = await context_manager.build_context(current_conversation_id, retrieved_contexts)
                recent_citations = assembled_context.get("retrieved", [])
                
                messages_for_llm = []
                for m in assembled_context["messages"]:
                    if m["role"] == "user":
                        messages_for_llm.append(Message.create_user(conversation_id=str(current_conversation_id.value), content=m["content"], token_count=1))
                    elif m["role"] == "assistant":
                        messages_for_llm.append(Message.create_assistant(conversation_id=str(current_conversation_id.value), content=m["content"], token_count=1))
                
                context_window = ContextWindow(
                    summary=assembled_context["summary"],
                    summary_tokens=0,
                    messages=messages_for_llm,
                    message_tokens=0,
                    total_tokens=assembled_context["total_tokens_estimated"]
                )
                
                retrieved_context_str = "\n\n".join([
                    f"Source: {ctx['source']}\n{ctx['content']}" for ctx in recent_citations
                ])
                
                with Live(Markdown("Thinking..."), console=console, refresh_per_second=15) as live:
                    current_text = ""
                    async for chunk in reasoning_engine.generate_response_stream(
                        context_window=context_window,
                        retrieved_context=retrieved_context_str
                    ):
                        current_text += chunk
                        live.update(Markdown(current_text))
                
                assistant_msg = Message.create_assistant(
                    conversation_id=str(current_conversation_id.value),
                    content=current_text,
                    token_count=max(1, len(current_text) // 4)
                )
                conversation.add_message(assistant_msg)
                await conv_repo.save(conversation)
                
                console.print()
            except Exception as e:
                console.print(f"[bold red]Error generating response: {str(e)}[/bold red]")


def register(app: typer.Typer):
    @app.command("chat")
    def chat_cmd():
        """Interactive chat interface."""
        asyncio.run(run_chat())
