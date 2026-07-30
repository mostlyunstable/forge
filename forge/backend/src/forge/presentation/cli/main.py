import typer
import subprocess
import os
from typing import Optional, List
from forge.presentation.cli.dashboard import Dashboard
from forge.presentation.cli.renderer import OutputRenderer
from forge.presentation.cli.plugin_loader import load_plugins

app = typer.Typer(invoke_without_command=True)
renderer = OutputRenderer()

load_plugins(app, "forge.presentation.cli.plugins")
def get_git_info():
    repo = "Unknown"
    branch = "Unknown"
    try:
        if os.path.exists(".git"):
            repo = os.path.basename(os.getcwd())
            branch_output = subprocess.check_output(["git", "branch", "--show-current"], stderr=subprocess.STDOUT)
            branch = branch_output.decode("utf-8").strip()
    except Exception:
        pass
    return repo, branch

def get_project_info():
    repo, branch = get_git_info()
    return {
        "repo": repo,
        "branch": branch,
        "index_status": "Ready",
        "memory_count": 42,
        "active_sessions": 1
    }

class IntentRouter:
    @staticmethod
    def route(query: str):
        query_lower = query.lower()
        if "why" in query_lower or "explain" in query_lower:
            return "Explain"
        elif "search" in query_lower or "find" in query_lower:
            return "Search"
        elif "memory" in query_lower:
            return "Memory Traversal"
        return "Unknown Intent"

@app.callback()
def main(ctx: typer.Context):
    if ctx.invoked_subcommand is None:
        import sys
        info = get_project_info()
        renderer.print_panel(
            f"Repo: {info['repo']} | Branch: {info['branch']} | Index: {info['index_status']} | Mem: {info['memory_count']} | Sessions: {info['active_sessions']}",
            title="Project Detection"
        )
        # Launch Dashboard
        dashboard = Dashboard(info)
        dashboard.run()

if __name__ == "__main__":
    app()
