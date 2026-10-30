from pathlib import Path

import pytest
from pydantic import ValidationError

from deck_builder.spec import Project, load_project

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "rectangle.toml"


def test_example_loads_with_immutable_exports() -> None:
    project = load_project(EXAMPLE)
    assert project.deck.footprint.width == 144
    assert project.exports.formats == ("scad", "dxf")
    with pytest.raises(ValidationError, match="frozen"):
        project.deck.elevation = 100  # ty: ignore[invalid-assignment] -- exercise runtime rejection


@pytest.mark.parametrize(
    ("original", "replacement", "message"),
    [
        ('units = "inches"', 'units = "feet"', "units"),
        ("schema_version = 1", "schema_version = 2", "schema_version"),
        ('type = "rectangle"', 'type = "polygon"', "type"),
        ("width = 144", "width = -1", "width"),
        ("width = 144", 'width = "144"', "width"),
        ("width = 144", "width = true", "width"),
        ("width = 144", "width = nan", "width"),
        ("width = 144", "width = inf", "width"),
        ("width = 144", "width = 2", "perimeter"),
        ("max_spacing = 16", "max_spacing = 0", "max_spacing"),
        ("max_spacing = 16", "max_spacing = 1", "lumber thickness"),
        ("edge_setback = 12", "edge_setback = 100", "half"),
        ("edge_setback = 12", "edge_setback = 0", "rim thickness"),
        ("elevation = 24", "elevation = 8", "below z=0"),
        ('direction = "y"', 'direction = "x"', "perpendicular"),
        ("gap = 0.25", "gap = -0.25", "gap"),
        ('formats = ["scad", "dxf"]', 'formats = ["svg"]', "formats"),
        ('formats = ["scad", "dxf"]', "formats = []", "nonempty"),
        ('formats = ["scad", "dxf"]', 'formats = ["dxf", "dxf"]', "duplicates"),
        ("width = 144", "width = 144\nwidht = 144", "widht"),
        ("schema_version = 1", "schema_version = 1\nstairs = []", "stairs"),
    ],
)
def test_invalid_configs_are_rejected(
    tmp_path: Path,
    original: str,
    replacement: str,
    message: str,
) -> None:
    config = tmp_path / "invalid.toml"
    config.write_text(EXAMPLE.read_text().replace(original, replacement))
    with pytest.raises(ValidationError, match=message):
        load_project(config)


def test_minimal_project_has_defaults() -> None:
    project = Project.model_validate({"deck": {"footprint": {"width": 120, "length": 120}}})
    assert project.framing.joists.size == "2x8"
    assert project.units == "inches"
