from pathlib import Path

import pytest
from pydantic import ValidationError
from shapely import union_all
from shapely.geometry import Polygon, box

from deck_builder.geometry import Vec3
from deck_builder.layout import build_deck
from deck_builder.plan import Plan, rectangles
from deck_builder.spacing import LayoutError
from deck_builder.spec import Project, load_project

EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


@pytest.mark.parametrize("example", ["l-shaped.toml", "u-shaped.toml"])
@pytest.mark.parametrize("direction", ["x", "y"])
@pytest.mark.parametrize("rows", [0, 1, 2])
def test_concave_layout_has_contained_parts_connected_bays_and_complete_backing(
    example: str,
    direction: str,
    rows: int,
) -> None:
    data = load_project(EXAMPLES / example).model_dump()
    data["framing"]["joists"]["direction"] = direction
    data["decking"]["direction"] = "x" if direction == "y" else "y"
    data["decking"]["border"]["rows"] = rows
    project = Project.model_validate(data)
    assembly = build_deck(project)
    assert assembly == build_deck(project)
    assert len({p.id for p in assembly.parts}) == len(assembly.parts)
    footprint = project.deck.footprint.plan().polygon
    physical = []
    frames = []
    borders = []
    for part in assembly.parts:
        outline = Polygon([(p.x, p.y) for p in part.geometry.vertices]).convex_hull
        if part.role in ("decking", "border", "rim", "joist", "backing", "blocking"):
            assert outline.difference(footprint).area < 1e-6, part.id
        if part.role in ("decking", "border"):
            physical.append(outline)
        if part.role in ("rim", "joist", "backing", "blocking"):
            frames.append(outline)
        if part.role == "border":
            borders.append(outline)
    assert sum(p.area for p in physical) - union_all(physical).area < 1e-6
    assert sum(p.area for p in frames) - union_all(frames).area < 1e-6
    if rows:
        assert union_all(borders).difference(union_all(frames)).area < 1e-6
        assert any(p.role == "backing" for p in assembly.parts)
    assert len(assembly.connections) == (1 if example == "l-shaped.toml" else 2)
    by_id = {p.id: p for p in assembly.parts}
    for connection in assembly.connections:
        assert all(by_id[name].role == "rim" for name in connection.members)
        a, b = [
            Polygon([(v.x, v.y) for v in by_id[name].geometry.vertices]).convex_hull
            for name in connection.members
        ]
        assert a.intersection(b).length > 0
        assert a.intersection(b).area < 1e-8
    moved = assembly.translated(Vec3(10, -20, 5))
    assert moved.connections[0].start == assembly.connections[0].start.translated(Vec3(10, -20, 5))


@pytest.mark.parametrize("edit", ["clockwise", "crossing", "diagonal", "collinear", "names"])
def test_invalid_polygon_is_rejected(edit: str) -> None:
    data = load_project(EXAMPLES / "l-shaped.toml").model_dump()
    ring = data["deck"]["footprint"]["vertices"]
    if edit == "clockwise":
        data["deck"]["footprint"]["vertices"] = tuple(reversed(ring))
    elif edit == "crossing":
        ring[2]["x"] = 0
    elif edit == "diagonal":
        ring[2]["x"] = 230
    elif edit == "collinear":
        ring[3]["y"] = 96
        ring[4]["y"] = 96
    else:
        ring[0]["name"] = ring[1]["name"]
    with pytest.raises(ValidationError):
        Project.model_validate(data)


def test_polygon_inset_rejects_limb_collapse() -> None:
    plan = Plan(
        ("a", "b", "c", "d", "e", "f"), ((0, 0), (100, 0), (100, 10), (20, 10), (20, 100), (0, 100))
    )
    with pytest.raises(LayoutError, match="limb"):
        plan.inset(6)


def test_partition_handles_holes_in_backing_regions() -> None:
    ring = box(0, 0, 100, 80).difference(box(10, 10, 90, 70))
    for axis in ("x", "y"):
        pieces = [box(*bounds) for bounds in rectangles(ring, axis)]
        assert union_all(pieces).symmetric_difference(ring).area < 1e-8
        assert sum(p.area for p in pieces) == pytest.approx(ring.area)


def test_backing_can_be_disabled_explicitly() -> None:
    data = load_project(EXAMPLES / "l-shaped.toml").model_dump()
    data["decking"]["border"]["backing"] = False
    assembly = build_deck(Project.model_validate(data))
    assert not any(p.role == "backing" for p in assembly.parts)


def test_bay_too_short_for_support_setbacks_is_rejected() -> None:
    data = load_project(EXAMPLES / "l-shaped.toml").model_dump()
    data["deck"]["footprint"]["vertices"][2]["y"] = 20
    data["deck"]["footprint"]["vertices"][3]["y"] = 20
    with pytest.raises(LayoutError, match="bay"):
        build_deck(Project.model_validate(data))


def test_manual_supports_and_blocking_work_in_concave_footprints() -> None:
    project = load_project(EXAMPLES / "l-shaped.toml")
    automatic = build_deck(project)
    data = project.model_dump()
    data["framing"]["supports"]["locations"] = [
        {
            "name": p.id.replace("/", "-"),
            "x": sum(v.x for v in p.geometry.vertices) / 8,
            "y": sum(v.y for v in p.geometry.vertices) / 8,
        }
        for p in automatic.parts
        if p.role == "support"
    ]
    data["framing"]["blocking"] = [{"name": "extra", "x": 2, "y": 40, "length": 10}]
    manual = build_deck(Project.model_validate(data))
    assert sum(p.role == "support" for p in manual.parts) == len(
        data["framing"]["supports"]["locations"]
    )
    assert any(p.id == "blocking/extra" for p in manual.parts)
    data["framing"]["blocking"][0].update(x=200, y=140)
    with pytest.raises(LayoutError, match="outside"):
        build_deck(Project.model_validate(data))


def test_stairs_cannot_enter_another_limb_or_staircase() -> None:
    data = load_project(EXAMPLES / "u-shaped.toml").model_dump()
    data["stairs"] = [
        {"name": "entry", "edge": "right-notch", "offset": 24, "width": 48, "tread_depth": 40}
    ]
    with pytest.raises(LayoutError, match="footprint"):
        build_deck(Project.model_validate(data))
    data["stairs"] = [
        {"name": "a", "edge": "left-notch", "offset": 24, "width": 48, "tread_depth": 20},
        {"name": "b", "edge": "right-notch", "offset": 72, "width": 48, "tread_depth": 20},
    ]
    with pytest.raises(LayoutError, match="intersects"):
        build_deck(Project.model_validate(data))
