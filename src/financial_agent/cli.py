import typer

app = typer.Typer(help="Daily weekly breakout agent")


@app.callback()
def main() -> None:
    """Daily after-close weekly breakout research CLI."""
