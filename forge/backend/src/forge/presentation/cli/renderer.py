import json
from typing import Any

import yaml
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table
from rich.tree import Tree


class OutputRenderer:
    """Centralized output renderer using Rich."""

    def __init__(self, console: Console | None = None):
        self.console = console or Console()

    def print(self, *args, **kwargs):
        self.console.print(*args, **kwargs)

    def print_panel(self, renderable, title: str = "", **kwargs):
        self.console.print(Panel(renderable, title=title, **kwargs))

    def print_table(self, title: str, columns: list[str], rows: list[list[Any]], **kwargs):
        table = Table(title=title, **kwargs)
        for col in columns:
            table.add_column(col)
        for row in rows:
            table.add_row(*[str(r) for r in row])
        self.console.print(table)

    def print_tree(self, label: str, items: list[Any], **kwargs):
        tree = Tree(label, **kwargs)
        for item in items:
            tree.add(str(item))
        self.console.print(tree)

    def print_markdown(self, markdown_text: str, **kwargs):
        self.console.print(Markdown(markdown_text, **kwargs))

    def print_json(self, data: Any, **kwargs):
        self.console.print(
            Syntax(json.dumps(data, indent=2), "json", theme="monokai", word_wrap=True)
        )

    def print_yaml(self, data: Any, **kwargs):
        self.console.print(
            Syntax(
                yaml.dump(data, default_flow_style=False), "yaml", theme="monokai", word_wrap=True
            )
        )
