"""Typer commands for validation and CAD generation from TOML project files."""

from collections import Counter
from pathlib import Path
from typing import Annotated

import typer

from deck_builder.assembly import DeckAssembly
from deck_builder.exporters.project import export_project
from deck_builder.layout import build_deck
from deck_builder.spec import Project, load_project

app = typer.Typer(
    help="Generate deck CAD files from TOML.",
    no_args_is_help=True,
    add_completion=False,
    pretty_exceptions_enable=False,
)
ConfigPath = Annotated[Path, typer.Argument(help="Path to a TOML deck configuration.")]


def _load(config: Path) -> tuple[Project, DeckAssembly]:
    try:
        project = load_project(config)
        return project, build_deck(project)
    except (OSError, ValueError) as error:
        typer.echo(f"deck-builder: {error}", err=True)
        raise typer.Exit(2) from error


@app.command(help="Validate configuration and resolve the layout without writing files.")
def validate(config: ConfigPath) -> None:
    """Validate configuration and resolve the layout without writing files.

    Args:
        config: Path to a TOML project file.
    """
    _, assembly = _load(config)
    counts = Counter(part.role for part in assembly.parts)
    summary = ", ".join(f"{count} {role}" for role, count in sorted(counts.items()))
    typer.echo(f"Valid deck: {len(assembly.parts)} parts ({summary})")


@app.command(help="Generate CAD files and an assembly manifest.")
def export(
    config: ConfigPath,
    output: Annotated[Path, typer.Option(help="Directory for generated files.")] = Path("build"),
) -> None:
    """Generate CAD files and an assembly manifest.

    Args:
        config: Path to a TOML project file.
        output: Destination directory for the selected files.
    """
    project, assembly = _load(config)
    try:
        paths = export_project(project, assembly, output)
    except OSError as error:
        typer.echo(f"deck-builder: {error}", err=True)
        raise typer.Exit(2) from error
    for path in paths:
        typer.echo(str(path))


def main() -> None:
    """Run the Typer application through the installed console entry point."""
    app()
