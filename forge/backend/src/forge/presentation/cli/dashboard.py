from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical
from textual.widgets import Footer, Header, Label, Static, Input, RichLog
from textual.message import Message as TextualMessage

from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.application.conversation.token_manager import ContextWindow, Message
from forge.config.settings import Settings
from forge.infrastructure.llm.llm_service import LLMService


class ChatPane(Vertical):
    def compose(self) -> ComposeResult:
        yield RichLog(id="chat-log", markup=True, auto_scroll=True)
        yield Input(placeholder="Ask Forge (Hit Enter to send)...", id="chat-input")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if not message.value.strip():
            return
            
        user_text = message.value
        self.query_one("#chat-input", Input).value = ""
        log = self.query_one("#chat-log", RichLog)
        
        log.write(f"\n[b][green]You:[/green][/b]\n{user_text}")
        
        # Trigger background task for LLM response
        self.fetch_response(user_text)

    @work(exclusive=True)
    async def fetch_response(self, text: str) -> None:
        log = self.app.query_one("#chat-log", RichLog)
        log.write("\n[b][blue]Forge is thinking...[/blue][/b]")
        
        try:
            llm = LLMService()
            engine = ReasoningEngine(llm)
            
            cw = ContextWindow(
                summary="",
                summary_tokens=0,
                messages=[],
                message_tokens=0,
                total_tokens=4000
            )
            
            # Let's use non-streaming for the UI to avoid RichLog chunking issues for now
            response_text = await engine.generate_response(
                context_window=cw,
                retrieved_context="CLI interactive dashboard mode.",
                user_prompt=text
            )
            log.write(f"\n[b][blue]Forge:[/blue][/b]\n{response_text}")
            
        except Exception as e:
            log.write(f"\n[bold red]Error communicating with AI Engine:[/bold red]\n{str(e)}")


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
    ChatPane {
        height: 1fr;
        width: 1fr;
        padding: 1;
    }
    #chat-log {
        height: 1fr;
        border: solid blue;
        background: $surface;
    }
    #chat-input {
        dock: bottom;
        margin-top: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit", show=True),
        Binding("c", "chat", "Chat", show=True),
        Binding("s", "search", "Search", show=True),
        Binding("g", "graph", "Graph", show=True),
    ]

    def __init__(self, project_info: dict, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.project_info = project_info
        self.chat_pane = ChatPane(id="chat-pane")
        self.welcome = Static("Welcome to Forge Interactive Dashboard.\nUse 'c' to Chat, 's' to Search, 'g' to view Graph.", id="main-text")

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
                yield self.welcome
        yield Footer()

    def action_chat(self) -> None:
        content = self.query_one("#content")
        # Remove anything in content
        for child in content.children:
            child.remove()
        content.mount(self.chat_pane)
        self.chat_pane.query_one(Input).focus()

    def action_search(self) -> None:
        content = self.query_one("#content")
        for child in content.children:
            child.remove()
        content.mount(Static("Opened Search view.", id="search-text"))

    def action_graph(self) -> None:
        content = self.query_one("#content")
        for child in content.children:
            child.remove()
        content.mount(Static("Opened Graph view.", id="graph-text"))
