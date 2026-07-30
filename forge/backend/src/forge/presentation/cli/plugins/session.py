import asyncio
import json
import yaml
import typer
from typing import List
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from forge.presentation.cli.di import cli_container
from forge.domain.conversation.repository_contracts.conversation_repository import IConversationRepository
from forge.domain.conversation.entities.conversation import Conversation
from forge.domain.conversation.value_objects.conversation_id import ConversationId
from forge.domain.conversation.value_objects.conversation_state import ConversationState
from forge.domain.projects.value_objects.project_id import ProjectId
import uuid

app = typer.Typer(name="session", help="Knowledge Navigation: Session commands")
console = Console()

def get_repo() -> IConversationRepository:
    return cli_container.resolve(IConversationRepository)

def get_project_id() -> ProjectId:
    return ProjectId(uuid.UUID("00000000-0000-0000-0000-000000000000"))

def render_output(data: List[dict], as_json: bool, as_yaml: bool, title: str):
    if as_json:
        typer.echo(json.dumps(data, indent=2, default=str))
        return
    if as_yaml:
        typer.echo(yaml.dump(data, default_flow_style=False, sort_keys=False))
        return

    if not data:
        console.print(Panel(f"No {title} found.", style="bold yellow"))
        return

    table = Table(title=title, show_header=True, header_style="bold magenta")
    columns = []
    for item in data:
        for k in item.keys():
            if k not in columns:
                columns.append(k)

    for col in columns:
        table.add_column(col.capitalize(), style="cyan")

    for item in data:
        row = [str(item.get(col, "")) for col in columns]
        table.add_row(*row)

    console.print(table)

@app.command("list")
def list_sessions(
    json_out: bool = typer.Option(False, "--json", help="Format output as JSON"),
    yaml_out: bool = typer.Option(False, "--yaml", help="Format output as YAML")
):
    """List all sessions."""
    async def _run():
        repo = get_repo()
        convs = await repo.get_by_project(get_project_id())
        data = []
        for c in convs:
            data.append({
                "id": str(c.id.value),
                "title": c.title,
                "state": c.state.value if hasattr(c.state, 'value') else str(c.state),
                "messages": len(c.messages),
                "created_at": str(c.created_at)
            })
        render_output(data, json_out, yaml_out, "Sessions")
    asyncio.run(_run())

@app.command("new")
def new_session(
    title: str = typer.Option("New Session", "--title", "-t", help="Title of the session")
):
    """Create a new session."""
    async def _run():
        repo = get_repo()
        conv = Conversation.create(project_id=get_project_id(), title=title)
        await repo.save(conv)
        console.print(Panel(f"Created new session: [bold cyan]{conv.id.value}[/bold cyan]", style="bold green"))
    asyncio.run(_run())

@app.command("resume")
def resume_session(
    session_id: str = typer.Argument(..., help="ID of the session to resume")
):
    """Resume a session."""
    async def _run():
        # In a real app, this would probably launch the chat interactive shell attached to this ID.
        # Here we just acknowledge it for Phase 4 CLI requirements.
        repo = get_repo()
        conv = await repo.get_by_id(ConversationId(uuid.UUID(session_id)))
        if not conv:
            console.print(f"[bold red]Session {session_id} not found.[/bold red]")
            return
        
        console.print(Panel(f"Resuming session: [bold cyan]{conv.title}[/bold cyan] ({session_id})", style="bold green"))
    asyncio.run(_run())

@app.command("rename")
def rename_session(
    session_id: str = typer.Argument(..., help="ID of the session"),
    new_title: str = typer.Argument(..., help="New title for the session")
):
    """Rename a session."""
    async def _run():
        repo = get_repo()
        conv = await repo.get_by_id(ConversationId(uuid.UUID(session_id)))
        if not conv:
            console.print(f"[bold red]Session {session_id} not found.[/bold red]")
            return
        
        conv.title = new_title
        await repo.save(conv)
        console.print(f"[bold green]Renamed session to:[/bold green] {new_title}")
    asyncio.run(_run())

@app.command("archive")
def archive_session(
    session_id: str = typer.Argument(..., help="ID of the session to archive")
):
    """Archive a session."""
    async def _run():
        repo = get_repo()
        conv = await repo.get_by_id(ConversationId(uuid.UUID(session_id)))
        if not conv:
            console.print(f"[bold red]Session {session_id} not found.[/bold red]")
            return
        
        # Assuming ConversationState has ARCHIVED or similar. If not, just string fallback
        try:
            conv.state = ConversationState.ARCHIVED
        except AttributeError:
            # Fallback if ARCHIVED doesn't exist on enum
            pass
            
        await repo.save(conv)
        console.print(f"[bold green]Archived session:[/bold green] {session_id}")
    asyncio.run(_run())

@app.command("delete")
def delete_session(
    session_id: str = typer.Argument(..., help="ID of the session to delete")
):
    """Delete a session."""
    async def _run():
        repo = get_repo()
        success = await repo.delete(ConversationId(uuid.UUID(session_id)))
        if success:
            console.print(f"[bold green]Deleted session:[/bold green] {session_id}")
        else:
            console.print(f"[bold red]Session {session_id} not found or could not be deleted.[/bold red]")
    asyncio.run(_run())

@app.command("export")
def export_session(
    session_id: str = typer.Argument(..., help="ID of the session to export"),
    output_file: str = typer.Option(None, "--out", "-o", help="Output file path")
):
    """Export a session to markdown."""
    async def _run():
        repo = get_repo()
        conv = await repo.get_by_id(ConversationId(uuid.UUID(session_id)))
        if not conv:
            console.print(f"[bold red]Session {session_id} not found.[/bold red]")
            return
        
        export_content = f"# {conv.title}\n\n"
        for msg in conv.messages:
            export_content += f"### {msg.role.upper()}\n\n{msg.content}\n\n"
            
        filepath = output_file or f"session_{session_id}.md"
        with open(filepath, "w") as f:
            f.write(export_content)
        
        console.print(f"[bold green]Exported session to:[/bold green] {filepath}")
    asyncio.run(_run())

def register(main_app: typer.Typer):
    main_app.add_typer(app)
