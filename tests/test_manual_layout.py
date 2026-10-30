from pathlib import Path

import pytest
from pydantic import ValidationError

from deck_builder.layout import build_deck
from deck_builder.spacing import LayoutError
from deck_builder.spec import Project, load_project

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "manual-layout.toml"


@pytest.mark.parametrize("direction", ["x", "y"])
def test_manual_supports_use_world_coordinates_and_named_ids(direction: str) -> None:
    data = load_project(EXAMPLE).model_dump()
    if direction == "x":
        data["deck"]["footprint"] = {"width": 96, "length": 33.5}
        data["framing"]["joists"]["direction"] = "x"
        data["decking"]["direction"] = "y"
        data["framing"]["blocking"] = []
        for location in data["framing"]["supports"]["locations"]:
            location["x"], location["y"] = location["y"], location["x"]
    project = Project.model_validate(data)
    assembly = build_deck(project)
    actual = {p.id: p for p in assembly.parts if p.role == "support"}
    assert len(actual) == 6
    assert project.framing.supports.locations
    for location in project.framing.supports.locations:
        mesh = actual[f"support/{location.name}"].geometry
        assert sum(p.x for p in mesh.vertices) / 8 == pytest.approx(location.x)
        assert sum(p.y for p in mesh.vertices) / 8 == pytest.approx(location.y)


def test_extra_blocking_is_flush_and_fits_between_joists() -> None:
    assembly = build_deck(load_project(EXAMPLE))
    block = next(p for p in assembly.parts if p.id == "blocking/extra-backing")
    assert min(v.x for v in block.geometry.vertices) == 1.5
    assert max(v.x for v in block.geometry.vertices) == 16
    assert max(v.z for v in block.geometry.vertices) == pytest.approx(24 - 0.94)
    assert block.cut_length == 14.5
    assert block.stock == "2x8"


@pytest.mark.parametrize(
    ("edit", "message"),
    [
        ("off-joist", "centered"),
        ("missing", "two manual supports"),
        ("setback", "edge_setback"),
        ("spacing", "max_spacing"),
        ("overlap", "overlap"),
        ("outside", "clear joist run"),
    ],
)
def test_invalid_manual_support_geometry(edit: str, message: str) -> None:
    data = load_project(EXAMPLE).model_dump()
    supports = data["framing"]["supports"]
    locations = supports["locations"]
    if edit == "off-joist":
        locations[0]["x"] = 3
    elif edit == "missing":
        supports["locations"] = locations[1:]
    elif edit == "setback":
        locations[0]["y"] = 20
    elif edit == "spacing":
        supports["max_spacing"] = 32
    elif edit == "overlap":
        supports["locations"] = (*locations, {**locations[0], "name": "duplicate-center"})
    else:
        locations[0]["y"] = 0
    with pytest.raises(LayoutError, match=message):
        build_deck(Project.model_validate(data))


@pytest.mark.parametrize("field", ["locations", "blocking"])
def test_duplicate_manual_names_are_invalid(field: str) -> None:
    data = load_project(EXAMPLE).model_dump()
    target = data["framing"]["supports"] if field == "locations" else data["framing"]
    target[field] = (*target[field], target[field][0])
    with pytest.raises(ValidationError, match="unique"):
        Project.model_validate(data)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [("x", 0, "intersects"), ("length", 100, "outside"), ("size", "2x12", "depth")],
)
def test_invalid_blocking_placement(field: str, value: object, message: str) -> None:
    data = load_project(EXAMPLE).model_dump()
    data["framing"]["blocking"][0][field] = value
    with pytest.raises(LayoutError, match=message):
        build_deck(Project.model_validate(data))
