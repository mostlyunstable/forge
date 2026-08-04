import sys

import typer

app = typer.Typer(
    name="forge",
    help="Forge CLI Application",
    add_completion=False,
    no_args_is_help=True,
)


@app.callback()
def main_callback():
    """Forge Phase 4 CLI"""
    pass


def setup_global_exception_handler():
    """Sets up a global exception handler to suppress stack traces for the user."""

    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # Print user friendly message
        typer.secho(
            f"An unexpected error occurred: {str(exc_value)}", fg=typer.colors.RED, err=True
        )
        typer.secho(
            "Please check the system logs for more details.", fg=typer.colors.YELLOW, err=True
        )

    sys.excepthook = handle_exception
