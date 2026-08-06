from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll, Horizontal
from textual.widgets import Footer, Header, Label, Static, Input, Markdown
import re

from forge.application.conversation.reasoning_engine import ReasoningEngine
from forge.infrastructure.llm.llm_service import LLMService

class ChatPane(Vertical):
    def compose(self) -> ComposeResult:
        with Container(id="chat-container"):
            yield VerticalScroll(id="chat-feed")
            with Horizontal(id="input-container"):
                yield Input(placeholder="Ask Forge (Hit Enter to send)...", id="chat-input")

    async def on_input_submitted(self, message: Input.Submitted) -> None:
        if not message.value.strip():
            return
            
        user_text = message.value
        self.query_one("#chat-input", Input).value = ""
        feed = self.query_one("#chat-feed", VerticalScroll)
        
        user_msg = Static(f"[b][white]You[/white][/b]\n{user_text}", classes="user-msg")
        feed.mount(user_msg)
        feed.scroll_end(animate=False)
        
        # Trigger background task for LLM response
        self.fetch_response(user_text)

    def _format_thinking(self, text: str) -> str:
        """Format XML thinking tags as dimmed markdown blockquotes."""
        text = re.sub(r'<thinking>(.*?)</thinking>', r'> *Thought Process:*\n> \1', text, flags=re.DOTALL)
        if '<thinking>' in text and '</thinking>' not in text:
            parts = text.split('<thinking>')
            return parts[0] + "\n> *Thinking...*\n> " + parts[1]
        return text

    @work(exclusive=True)
    async def fetch_response(self, text: str) -> None:
        feed = self.app.query_one("#chat-feed", VerticalScroll)
        
        ai_msg = Markdown("*Thinking...*", classes="forge-msg")
        feed.mount(ai_msg)
        feed.scroll_end(animate=False)
        
        try:
            llm = LLMService()
            engine = ReasoningEngine(llm)
            from forge.application.conversation.token_manager import ContextWindow, DEFAULT_MAX_TOKENS
            cw = ContextWindow(
                summary="",
                summary_tokens=0,
                messages=[],
                message_tokens=0,
                total_tokens=DEFAULT_MAX_TOKENS
            )
            
            full_text = ""
            async for chunk in engine.generate_response_stream(
                context_window=cw,
                retrieved_context="CLI interactive dashboard mode.",
                user_prompt=text
            ):
                if chunk["type"] == "text":
                    full_text += chunk.get("content", "")
                    display_text = self._format_thinking(full_text)
                    # Update markdown
                    ai_msg.update(display_text)
                    feed.scroll_end(animate=False)
                elif chunk["type"] == "status":
                    # Status messages from tool calls
                    status = chunk.get("message", "")
                    full_text += f"\n> _{status}_\n"
                    ai_msg.update(self._format_thinking(full_text))
                    feed.scroll_end(animate=False)
            
        except Exception as e:
            err_msg = Static(f"[bold red]Error communicating with AI Engine:[/bold red]\n{str(e)}", classes="error-msg")
            feed.mount(err_msg)
            feed.scroll_end(animate=False)


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
        align: center middle;
    }
    
    /* Claude-like Centered Chat Container */
    #chat-container {
        width: 100%;
        max-width: 100;
        height: 1fr;
        layout: vertical;
        padding-top: 1;
        padding-bottom: 1;
    }
    
    #chat-feed {
        height: 1fr;
        padding: 1;
    }
    
    /* Message Bubbles */
    .user-msg {
        background: $surface-lighten-3;
        color: $text;
        padding: 1;
        margin-bottom: 1;
        border-left: thick $accent;
    }
    
    .forge-msg {
        padding: 1;
        margin-bottom: 2;
    }
    
    .error-msg {
        background: $error-muted;
        color: $error;
        padding: 1;
    }

    /* Input Container */
    #input-container {
        height: auto;
        dock: bottom;
        padding: 1;
    }
    
    #chat-input {
        width: 1fr;
        border: round $primary-muted;
        background: $surface;
    }
    #chat-input:focus {
        border: round $primary;
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
        
        logo = r"""[b][blue]
    ______                           
   / ____/___  _________ ____  
  / /_  / __ \/ ___/ __ `/ _ \ 
 / __/ / /_/ / /  / /_/ /  __/ 
/_/    \____/_/   \__, /\___/  
                 /____/        
[/blue][/b]
Welcome to the Forge Interactive Dashboard.
[dim]Use 'c' to Chat, 's' to Search, 'g' to view Graph.[/dim]
"""
        self.welcome = Static(logo, id="main-text")

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
