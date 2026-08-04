from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Label, Static


class Dashboard(App):
    """Interactive Textual Dashboard for Forge."""

    CSS = """
    Screen {
        layout: vertical;
    }
    #main-container {
        height: 1fr;
        layout: horizontal;
    }
    #sidebar {
        width: 30;
        dock: left;
        height: 1fr;
        border-right: solid green;
    }
    #content {
        height: 1fr;
        width: 1fr;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("f1", "chat", "F1 Chat", show=True),
        Binding("f2", "search", "F2 Search", show=True),
        Binding("f3", "graph", "F3 Graph", show=True),
    ]

    def __init__(self, project_info: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_info = project_info

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="main-container"):
            with Vertical(id="sidebar"):
                yield Label("[b]Project Status[/b]\n")
                yield Label(f"Repo: {self.project_info.get('repo', 'Unknown')}")
                yield Label(f"Branch: {self.project_info.get('branch', 'Unknown')}")
                yield Label(f"Index: {self.project_info.get('index_status', 'Unknown')}")
                yield Label(f"Memory: {self.project_info.get('memory_count', 0)}")
                yield Label(f"Sessions: {self.project_info.get('active_sessions', 0)}")
            with Container(id="content"):
                yield Static(
                    "Welcome to Forge Interactive Dashboard.\nUse Command Palette F1-F7 for actions.",
                    id="main-text",
                )
        yield Footer()

    def action_chat(self) -> None:
        self.query_one("#main-text").update("Opened Chat view.")

    def action_search(self) -> None:
        self.query_one("#main-text").update("Opened Search view.")

    def action_graph(self) -> None:
        self.query_one("#main-text").update("Opened Graph view.")
