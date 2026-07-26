import asyncio
import json
import yaml
import typer
from typing import List, Any
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from forge.presentation.cli.di import cli_container
from forge.domain.memory.repository_contracts.memory_repository import IMemoryRepository
from forge.domain.projects.value_objects.project_id import ProjectId
import uuid

app = typer.Typer(name="memory", help="Knowledge Navigation: Memory commands")
console = Console()

def get_repo() -> IMemoryRepository:
    return cli_container.resolve(IMemoryRepository)

def get_project_id() -> ProjectId:
    # In a real scenario, this would come from context or config
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
    # Collect all unique keys for columns
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
def list_memories(
    json_out: bool = typer.Option(False, "--json", help="Format output as JSON"),
    yaml_out: bool = typer.Option(False, "--yaml", help="Format output as YAML")
):
    """List all memories."""
    async def _run():
        repo = get_repo()
        mems = await repo.get_by_project(get_project_id())
        data = []
        for m in mems:
            data.append({
                "id": str(m.id.value),
                "type": getattr(m, 'memory_type', 'unknown'),
                "title": m.title,
                "created_at": str(m.created_at)
            })
        render_output(data, json_out, yaml_out, "All Memories")
    asyncio.run(_run())

@app.command("adr")
def list_adrs(
    json_out: bool = typer.Option(False, "--json", help="Format output as JSON"),
    yaml_out: bool = typer.Option(False, "--yaml", help="Format output as YAML")
):
    """List architecture decision records (ADRs)."""
    async def _run():
        repo = get_repo()
        mems = await repo.get_by_project(get_project_id())
        data = []
        for m in mems:
            if getattr(m, 'memory_type', '') == 'decision':
                data.append({
                    "id": str(m.id.value),
                    "title": m.title,
                    "status": getattr(m, 'status', 'N/A'),
                    "created_at": str(m.created_at)
                })
        render_output(data, json_out, yaml_out, "Architecture Decisions")
    asyncio.run(_run())

@app.command("feature")
def list_features(
    json_out: bool = typer.Option(False, "--json", help="Format output as JSON"),
    yaml_out: bool = typer.Option(False, "--yaml", help="Format output as YAML")
):
    """List features."""
    async def _run():
        repo = get_repo()
        mems = await repo.get_by_project(get_project_id())
        data = []
        for m in mems:
            if getattr(m, 'memory_type', '') == 'feature':
                data.append({
                    "id": str(m.id.value),
                    "title": m.title,
                    "status": getattr(m, 'status', 'N/A')
                })
        render_output(data, json_out, yaml_out, "Features")
    asyncio.run(_run())

@app.command("bug")
def list_bugs(
    json_out: bool = typer.Option(False, "--json", help="Format output as JSON"),
    yaml_out: bool = typer.Option(False, "--yaml", help="Format output as YAML")
):
    """List bugs."""
    async def _run():
        repo = get_repo()
        mems = await repo.get_by_project(get_project_id())
        data = []
        for m in mems:
            if getattr(m, 'memory_type', '') == 'bug':
                data.append({
                    "id": str(m.id.value),
                    "title": m.title,
                    "severity": getattr(m, 'severity', 'N/A'),
                    "resolved": str(getattr(m, 'resolved', False))
                })
        render_output(data, json_out, yaml_out, "Bugs")
    asyncio.run(_run())

@app.command("note")
def list_notes(
    json_out: bool = typer.Option(False, "--json", help="Format output as JSON"),
    yaml_out: bool = typer.Option(False, "--yaml", help="Format output as YAML")
):
    """List engineering notes."""
    async def _run():
        repo = get_repo()
        mems = await repo.get_by_project(get_project_id())
        data = []
        for m in mems:
            if getattr(m, 'memory_type', '') == 'note':
                data.append({
                    "id": str(m.id.value),
                    "title": m.title,
                    "tags": ", ".join(getattr(m, 'tags', []))
                })
        render_output(data, json_out, yaml_out, "Engineering Notes")
    asyncio.run(_run())

@app.command("event")
def list_events(
    json_out: bool = typer.Option(False, "--json", help="Format output as JSON"),
    yaml_out: bool = typer.Option(False, "--yaml", help="Format output as YAML")
):
    """List engineering events."""
    async def _run():
        repo = get_repo()
        mems = await repo.get_by_project(get_project_id())
        data = []
        for m in mems:
            if getattr(m, 'memory_type', '') == 'event':
                data.append({
                    "id": str(m.id.value),
                    "title": m.title,
                    "event_type": getattr(m, 'event_type', 'N/A')
                })
        render_output(data, json_out, yaml_out, "Engineering Events")
    asyncio.run(_run())

def register(main_app: typer.Typer):
    main_app.add_typer(app)
