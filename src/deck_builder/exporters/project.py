"""File output orchestration, separated from layout and individual exporters."""

import json
from dataclasses import asdict
from pathlib import Path

from deck_builder.assembly import DeckAssembly
from deck_builder.exporters.dxf import render_dxf
from deck_builder.exporters.scad import render_scad
from deck_builder.projection import View
from deck_builder.spec import Project


def export_project(project: Project, assembly: DeckAssembly, output: Path) -> tuple[Path, ...]:
    """Write the selected CAD files and an inspectable assembly manifest.

    Args:
        project: Specification containing validated export selections.
        assembly: The corresponding resolved assembly.
        output: Destination directory, created if missing. Matching filenames
            are overwritten; unrelated files are left untouched.

    Returns:
        Paths of all written files, including assembly.json.

    Raises:
        OSError: If output directories or files cannot be written.
    """
    output.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    if "scad" in project.exports.formats:
        path = output / "deck.scad"
        path.write_text(render_scad(assembly), encoding="utf-8")
        paths.append(path)
    if "dxf" in project.exports.formats:
        for selected in project.exports.views:
            path = output / f"{selected}.dxf"
            render_dxf(assembly, View(selected)).saveas(path)
            paths.append(path)
    manifest = output / "assembly.json"
    manifest.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "units": "inches",
                "parts": [asdict(p) for p in assembly.parts],
            },
            indent=2,
            allow_nan=False,
        )
        + "\n",
        encoding="utf-8",
    )
    return (*paths, manifest)
