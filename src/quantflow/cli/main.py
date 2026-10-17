"""QuantFlow operator CLI entry point (Typer)."""

from __future__ import annotations

import typer

app = typer.Typer(
    help="QuantFlow operator CLI.",
    no_args_is_help=True,
    add_completion=False,
)
migrate_app = typer.Typer(
    help="Forward-only, checksum-verified schema migrations.",
    no_args_is_help=True,
)


@migrate_app.command()
def apply() -> None:
    """Apply pending migrations to the selected store."""
    typer.echo("migrate apply is not implemented yet", err=True)
    raise typer.Exit(code=2)


@migrate_app.command()
def status() -> None:
    """Report pending count and each store's last successful migration."""
    typer.echo("migrate status is not implemented yet", err=True)
    raise typer.Exit(code=2)


@migrate_app.command()
def verify() -> None:
    """Verify store/manifest/ledger consistency read-only."""
    typer.echo("migrate verify is not implemented yet", err=True)
    raise typer.Exit(code=2)


app.add_typer(migrate_app, name="migrate")


def main() -> None:
    """Console-script entry point."""
    app()
