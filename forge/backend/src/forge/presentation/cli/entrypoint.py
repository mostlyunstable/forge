import typer
from .app import app, setup_global_exception_handler
from .plugin_loader import load_plugins

def main():
    setup_global_exception_handler()
    
    # Load plugins dynamically from the plugins package
    load_plugins(app, "forge.presentation.cli.plugins")
    
    app()

if __name__ == "__main__":
    main()
