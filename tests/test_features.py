from pathlib import Path

import pytest
from pydantic import ValidationError

from deck_builder.geometry import Mesh, Vec3, extrude_polygon
from deck_builder.layout import build_deck
from deck_builder.spacing import LayoutError
from deck_builder.spec import Project, load_project

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "border-and-stairs.toml"


def volume(mesh: Mesh) -> float:
    result = 0.0
    for face in mesh.faces:
        a = mesh.vertices[face[0]]
        for i in range(1, len(face) - 1):
            b, c = mesh.vertices[face[i]], mesh.vertices[face[i + 1]]
            result += (
                a.x * (b.y * c.z - b.z * c.y)
                + a.y * (b.z * c.x - b.x * c.z)
                + a.z * (b.x * c.y - b.y * c.x)
            ) / 6
    return result


@pytest.mark.parametrize("rows", [0, 1, 2])
@pytest.mark.parametrize("direction", ["x", "y"])
def test_borders_leave_interior_clear_and_preserve_material_volume(
    rows: int, direction: str
) -> None:
    data = load_project(EXAMPLE).model_dump()
    data["stairs"] = []
    data["decking"]["border"]["rows"] = rows
    data["decking"]["direction"] = direction
    data["framing"]["joists"]["direction"] = "y" if direction == "x" else "x"
    project = Project.model_validate(data)
    assembly = build_deck(project)
    border = [p for p in assembly.parts if p.role == "border"]
    assert len(border) == 4 * rows
    inset = rows * (project.decking.width + project.decking.gap)
    for part in assembly.parts:
        assert volume(part.geometry) > 0
        if part.role == "decking":
            assert all(
                inset - 1e-8 <= p.x <= 144 - inset + 1e-8
                and inset - 1e-8 <= p.y <= 192 - inset + 1e-8
                for p in part.geometry.vertices
            )
    if rows:
        expected_border_area = sum(
            (144 - 2 * i * 5.75) * (192 - 2 * i * 5.75)
            - (144 - 2 * i * 5.75 - 11) * (192 - 2 * i * 5.75 - 11)
            for i in range(rows)
        )
        assert sum(volume(p.geometry) for p in border) == pytest.approx(expected_border_area * 0.94)
        assert all(p.start_miter == 45 and p.end_miter == 45 for p in border)


@pytest.mark.parametrize("edge", ["front", "right", "back", "left"])
def test_box_stairs_equal_rises_and_named_edge_placement(edge: str) -> None:
    data = load_project(EXAMPLE).model_dump()
    data["stairs"][0]["edge"] = edge
    assembly = build_deck(Project.model_validate(data))
    tread_parts = [p for p in assembly.parts if p.role == "stair_tread"]
    assert {round(max(v.z for v in p.geometry.vertices), 8) for p in tread_parts} == {6, 12, 18}
    stair_parts = [p for p in assembly.parts if p.id.startswith("stair/")]
    assert min(v.z for p in stair_parts for v in p.geometry.vertices) == pytest.approx(0)
    assert all(volume(p.geometry) > 0 for p in stair_parts)
    for part in stair_parts:
        for point in part.geometry.vertices:
            if edge == "front":
                assert 24 - 1e-8 <= point.x <= 72 + 1e-8 and point.y <= 1e-8
            elif edge == "right":
                assert 24 - 1e-8 <= point.y <= 72 + 1e-8 and point.x >= 144 - 1e-8
            elif edge == "back":
                assert 72 - 1e-8 <= point.x <= 120 + 1e-8 and point.y >= 192 - 1e-8
            else:
                assert 120 - 1e-8 <= point.y <= 168 + 1e-8 and point.x <= 1e-8
    translated = assembly.translated(Vec3(10, -5, 3))
    assert translated.boundaries[0].start == Vec3(10, -5, 3)
    assert {b.name for b in assembly.boundaries} == {"front", "right", "back", "left"}


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("edge", "missing", "edge"),
        ("width", 200, "edge"),
        ("offset", -1, "offset"),
        ("max_rise", 0.5, "thickness"),
        ("ground_elevation", 24, "below"),
        ("name", "bad/name", "name"),
        ("system", "stringer", "system"),
    ],
)
def test_invalid_stair_configuration(field: str, value: object, message: str) -> None:
    data = load_project(EXAMPLE).model_dump()
    data["stairs"][0][field] = value
    with pytest.raises(ValidationError, match=message):
        Project.model_validate(data)


def test_stair_stock_and_overlaps_are_checked() -> None:
    data = load_project(EXAMPLE).model_dump()
    data["stairs"][0]["frame_size"] = "2x6"
    data["stairs"][0]["max_rise"] = 8
    with pytest.raises(LayoutError, match="stock"):
        build_deck(Project.model_validate(data))
    data = load_project(EXAMPLE).model_dump()
    other = {**data["stairs"][0], "name": "other", "offset": 30}
    data["stairs"] = (*data["stairs"], other)
    with pytest.raises(ValidationError, match="overlap"):
        Project.model_validate(data)


def test_border_cannot_consume_footprint() -> None:
    data = load_project(EXAMPLE).model_dump()
    data["decking"]["border"]["rows"] = 10
    data["deck"]["footprint"]["width"] = 100
    with pytest.raises(ValidationError, match="interior"):
        Project.model_validate(data)


def test_convex_extrusion_volume_and_winding() -> None:
    polygon = ((0.0, 0.0), (10.0, 0.0), (8.0, 2.0), (2.0, 2.0))
    mesh = extrude_polygon(polygon, 3)
    assert volume(mesh) == pytest.approx(48)
    assert volume(mesh.rotated_z(37).translated(Vec3(12, -30, 40))) == pytest.approx(48)
    with pytest.raises(ValueError, match="counterclockwise"):
        extrude_polygon(tuple(reversed(polygon)), 3)
