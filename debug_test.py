import typer
from typer.testing import CliRunner
test_app = typer.Typer()
@test_app.callback()
def callback():
    pass
@test_app.command()
def dummy_command():
    typer.echo("Hello")
runner = CliRunner()
result = runner.invoke(test_app, ["dummy-command"])
print(result.exit_code, result.stdout)
