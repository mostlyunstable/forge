import typer
from rich.console import Console
from rich.markdown import Markdown
from rich.tree import Tree
from rich.panel import Panel

from forge.presentation.cli.di import cli_container
from forge.application.discovery import (
    ContextRetriever,
    ReasoningEngine,
    IGraphAdapter,
    SearchResult,
    ExplainResult,
    GraphResult,
)

app = typer.Typer(name="discovery", help="Engineering exploration commands.")
console = Console()

def get_context_retriever() -> ContextRetriever:
    return cli_container.resolve(ContextRetriever)

def get_reasoning_engine() -> ReasoningEngine:
    return cli_container.resolve(ReasoningEngine)

def get_graph_adapter() -> IGraphAdapter:
    return cli_container.resolve(IGraphAdapter)

def display_citations(citations):
    if citations:
        console.print("[bold cyan]Citations:[/bold cyan]")
        for citation in citations:
            console.print(f" - {citation}")

@app.command("search")
def search(query: str):
    """Search the codebase."""
    retriever = get_context_retriever()
    result = retriever.search(query)
    
    console.print(Panel(Markdown(result.content), title=f"Search: {query}"))
    display_citations(result.citations)

@app.command("explain")
def explain(file: str):
    """Explain a specific file."""
    engine = get_reasoning_engine()
    result = engine.explain(file)
    
    console.print(Panel(Markdown(result.explanation), title=f"Explanation: {file}"))
    display_citations(result.citations)

def render_graph(result: GraphResult, title: str):
    tree = Tree(f"[bold green]{title}[/bold green]")
    
    from collections import defaultdict
    adj = defaultdict(list)
    for edge in result.edges:
        source = edge.get("source")
        target = edge.get("target")
        if source and target:
            adj[source].append(target)
            
    for node in result.nodes:
        node_id = node.get("id")
        if node_id:
            node_tree = tree.add(node_id)
            for target in adj[node_id]:
                node_tree.add(target)
                
    console.print(tree)
    display_citations(result.citations)

@app.command("graph")
def graph():
    """Display the full dependency graph."""
    adapter = get_graph_adapter()
    result = adapter.get_graph()
    render_graph(result, "Codebase Graph")

@app.command("deps")
def deps(target: str):
    """Display dependencies for a target."""
    adapter = get_graph_adapter()
    result = adapter.get_deps(target)
    render_graph(result, f"Dependencies: {target}")

@app.command("references")
def references(target: str):
    """Display references for a target."""
    adapter = get_graph_adapter()
    result = adapter.get_references(target)
    render_graph(result, f"References: {target}")

def register(main_app: typer.Typer):
    main_app.add_typer(app)
