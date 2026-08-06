from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Container, Vertical, VerticalScroll, Horizontal
from textual.widgets import Footer, Header, Label, Static, Input, Markdown, Tree
import re
import sqlite3
import json
import asyncio
import random

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


class GraphPane(Vertical):
    def compose(self) -> ComposeResult:
        with Container(id="graph-container"):
            yield Static(" [b]Forge Memory Graph[/b]", id="graph-header")
            tree = Tree("Root", id="memory-tree")
            tree.root.expand()
            tree.show_root = False
            yield tree

    def on_mount(self) -> None:
        self.fetch_graph_data()

    @work(exclusive=True)
    async def fetch_graph_data(self) -> None:
        tree = self.app.query_one("#memory-tree", Tree)
        
        # Add root nodes
        conv_node = tree.root.add("[b][cyan]💬 Conversations & Extracted Memories[/cyan][/b]", expand=True)
        kg_node = tree.root.add("[b][magenta]🧠 Semantic Knowledge Graph (Relationships)[/magenta][/b]", expand=True)
        
        def _fetch():
            data = {"conversations": [], "relationships": [], "memories": {}}
            try:
                # Fetch from forge.db
                with sqlite3.connect("forge.db") as conn:
                    # 1. Fetch active conversations
                    c_cursor = conn.execute("SELECT id, title FROM conversations ORDER BY created_at DESC LIMIT 20")
                    for c_id, title in c_cursor.fetchall():
                        data["conversations"].append({"id": c_id, "title": title})
                    
                    # 2. Fetch memories (Notes, Bugs, Features, Decisions)
                    m_cursor = conn.execute("SELECT id, memory_type, title, source FROM memories")
                    for m_id, m_type, title, source in m_cursor.fetchall():
                        data["memories"][m_id] = {"type": m_type, "title": title, "source": source}
                        
                # Fetch from forge_knowledge_graph.db
                try:
                    with sqlite3.connect("forge_knowledge_graph.db") as conn:
                        r_cursor = conn.execute("SELECT source_id, target_id, relationship_type FROM relationships LIMIT 100")
                        for src, tgt, rtype in r_cursor.fetchall():
                            data["relationships"].append({"src": src, "tgt": tgt, "type": rtype})
                except sqlite3.OperationalError:
                    pass # knowledge graph db might not exist yet
            except Exception as e:
                data["error"] = str(e)
            return data

        data = await asyncio.to_thread(_fetch)
        
        if "error" in data:
            tree.root.add(f"[red]Error fetching graph data:[/red] {data['error']}")
            return

        # Render Conversations
        for conv in data["conversations"]:
            node = conv_node.add(f"[white]💬 {conv['title']}[/white]")
            conv_memories = [m for m in data["memories"].values() if conv['id'] in m['source']]
            if conv_memories:
                for m in conv_memories:
                    icon = "🐛" if m['type'] == 'bug' else "📝" if m['type'] == 'note' else ("⚖️" if m['type'] == 'decision' else "⚡")
                    color = "red" if m['type'] == 'bug' else "green" if m['type'] == 'note' else "yellow"
                    node.add(f"[{color}]{icon} [{m['type'].upper()}][/{color}] [dim]{m['title']}[/dim]")
            else:
                node.add("[dim]No memories extracted yet.[/dim]")
                    
        # Render Knowledge Graph Relationships
        if not data["relationships"]:
            kg_node.add("[dim]No semantic relationships found.[/dim]")
        for rel in data["relationships"]:
            src = data["memories"].get(rel["src"], {"title": f"Unknown ({rel['src'][:8]})", "type": "node"})
            tgt = data["memories"].get(rel["tgt"], {"title": f"Unknown ({rel['tgt'][:8]})", "type": "node"})
            
            src_icon = "🐛" if src['type'] == 'bug' else "📝" if src['type'] == 'note' else ("⚖️" if src['type'] == 'decision' else "⚡")
            tgt_icon = "🐛" if tgt['type'] == 'bug' else "📝" if tgt['type'] == 'note' else ("⚖️" if tgt['type'] == 'decision' else "⚡")
            
            kg_node.add(f"{src_icon} [dim]{src['title']}[/dim]  [b][blue]──({rel['type']})──>[/blue][/b]  {tgt_icon} [dim]{tgt['title']}[/dim]")


class FloatingRobot(Static):
    FRAMES = [
        r"""
   [b][blue]▄███▄[/blue][/b]
  [b][white]═[/white][/b][b][blue]▐[/blue][/b][b][cyan]◉[/cyan][/b][b][dim]▄[/dim][/b][b][cyan]◉[/cyan][/b][b][blue]▌[/blue][/b][b][white]═[/white][/b]
   [b][blue]█████[/blue][/b]
    [b][white]▟[/white][/b] [b][white]▙[/white][/b]
""",
        r"""
   [b][blue]▄███▄[/blue][/b]
  [b][white]═[/white][/b][b][blue]▐[/blue][/b][b][cyan]◉[/cyan][/b][b][dim]▄[/dim][/b][b][cyan]◉[/cyan][/b][b][blue]▌[/blue][/b][b][white]═[/white][/b]
   [b][blue]█████[/blue][/b]
    [b][white]▚[/white][/b] [b][white]▞[/white][/b]
""",
        r"""
   [b][blue]▄███▄[/blue][/b]
  [b][white]─[/white][/b][b][blue]▐[/blue][/b][b][cyan]◉[/cyan][/b][b][dim]▄[/dim][/b][b][cyan]◉[/cyan][/b][b][blue]▌[/blue][/b][b][white]─[/white][/b]
   [b][blue]█████[/blue][/b]
    [b][white]▟[/white][/b] [b][white]▙[/white][/b]
"""
    ]
    
    def on_mount(self) -> None:
        self.frame_idx = 0
        self.pos_x = 35.0
        self.pos_y = 10.0
        self.vx = 5.0  # cells per second X
        self.vy = 2.0  # cells per second Y
        
        self.styles.offset = (int(self.pos_x), int(self.pos_y))
        self.update(self.FRAMES[self.frame_idx])
        
        self.set_interval(0.2, self.tick)
        
    def tick(self):
        self.pos_x += self.vx * 0.2
        self.pos_y += self.vy * 0.2
        
        max_x = max(0, self.screen.size.width - 10)
        max_y = max(0, self.screen.size.height - 7)
        
        if self.pos_x <= 0:
            self.pos_x = 0
            self.vx *= -1
        elif self.pos_x >= max_x:
            self.pos_x = max_x
            self.vx *= -1
            
        if self.pos_y <= 2:
            self.pos_y = 2
            self.vy *= -1
        elif self.pos_y >= max_y:
            self.pos_y = max_y
            self.vy *= -1
            
        self.styles.offset = (int(self.pos_x), int(self.pos_y))
        
        self.frame_idx = (self.frame_idx + 1) % len(self.FRAMES)
        self.update(self.FRAMES[self.frame_idx])


class Dashboard(App):
    """Interactive Textual Dashboard for Forge."""

    CSS = """
    Screen {
        layout: vertical;
        layers: base overlay;
    }
    #main-container {
        height: 1fr;
        layout: horizontal;
        layer: base;
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
    
    /* Graph Container */
    #graph-container {
        width: 100%;
        height: 1fr;
        layout: vertical;
        padding: 2;
    }
    
    #graph-header {
        background: $surface-lighten-2;
        color: $text;
        width: 100%;
        padding: 1;
        margin-bottom: 1;
    }
    
    #memory-tree {
        height: 1fr;
        border: round $primary-muted;
        background: $surface;
        padding: 1;
    }
    
    #floating-robot {
        layer: overlay;
        position: absolute;
        width: 10;
        height: 5;
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
        self.graph_pane = GraphPane(id="graph-pane")
        
        logo = r"""[b][cyan]
███████╗ ██████╗ ██████╗  ██████╗ ███████╗
██╔════╝██╔═══██╗██╔══██╗██╔════╝ ██╔════╝
█████╗  ██║   ██║██████╔╝██║  ███╗█████╗  
██╔══╝  ██║   ██║██╔══██╗██║   ██║██╔══╝  
██║     ╚██████╔╝██║  ██║╚██████╔╝███████╗
╚═╝      ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚══════╝
[/cyan][/b][b][white]
      A U T O N O M O U S   E N G I N E E R I N G
[/white][/b]

[dim]Press [b]'c'[/b] to Chat   |   Press [b]'s'[/b] to Search   |   Press [b]'g'[/b] to Graph[/dim]
"""
        self.welcome = Static(logo, id="main-text", classes="welcome-text")

    def compose(self) -> ComposeResult:
        yield FloatingRobot(id="floating-robot")
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
        content.mount(self.graph_pane)
