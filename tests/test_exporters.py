import json
import re
from pathlib import Path

import ezdxf
import pytest
from ezdxf import units
from ezdxf.entities import Dimension, LWPolyline

from deck_builder.assembly import DeckAssembly, Part
from deck_builder.exporters.dxf import render_dxf
from deck_builder.exporters.project import export_project
from deck_builder.exporters.scad import render_scad
from deck_builder.geometry import Vec3, box, tapered_block
from deck_builder.layout import build_deck
from deck_builder.projection import View, project_point, silhouette
from deck_builder.spec import load_project

EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "rectangle.toml"


@pytest.mark.parametrize(
    ("view", "expected"),
    [
        (View.TOP, (10, 20)),
        (View.FRONT, (10, 30)),
        (View.BACK, (-10, 30)),
        (View.LEFT, (-20, 30)),
        (View.RIGHT, (20, 30)),
    ],
)
def test_view_conventions(view: View, expected: tuple[float, float]) -> None:
    assert project_point(Vec3(10, 20, 30), view) == expected


def test_rotated_geometry_projects_into_every_view() -> None:
    mesh = box(2, 4, 6).rotated_z(90).translated(Vec3(10, 20, 30))
    front = silhouette(mesh, View.FRONT)
    back = silhouette(mesh, View.BACK)
    assert set(front) == {(6, 30), (10, 30), (10, 36), (6, 36)}
    assert set(back) == {(-x, y) for x, y in front}
    assert set(silhouette(mesh, View.RIGHT)) == {(20, 30), (22, 30), (22, 36), (20, 36)}


def test_tapered_block_has_trapezoidal_elevation() -> None:
    result = silhouette(tapered_block(10, 8, 6), View.FRONT)
    assert set(result) == {(-5, 0), (5, 0), (-4, 6), (4, 6)}


def test_scad_contains_the_same_world_vertices_and_clockwise_faces() -> None:
    mesh = box(2, 4, 6).rotated_z(30).translated(Vec3(10, 20, 30))
    part = Part("joist/0000", "joist", "lumber", mesh)
    assembly = DeckAssembly((part,))
    source = render_scad(assembly)
    match = re.search(r"polyhedron\(points=(.*), faces=(.*)\);", source)
    assert match
    assert json.loads(match[1]) == [[v.x, v.y, v.z] for v in mesh.vertices]
    assert json.loads(match[2]) == [list(reversed(face)) for face in mesh.faces]
    assert source == render_scad(assembly)


def test_dxf_round_trip_retains_units_layers_part_ids_and_geometry(tmp_path: Path) -> None:
    project = load_project(EXAMPLE)
    assembly = build_deck(project)
    path = tmp_path / "top.dxf"
    render_dxf(assembly, View.TOP).saveas(path)
    document = ezdxf.readfile(path)
    assert document.units == units.IN
    assert not document.audit().has_errors
    entities = list(document.modelspace().query("LWPOLYLINE"))
    assert len(entities) == len(assembly.parts)
    for part, entity in zip(assembly.parts, entities, strict=True):
        assert isinstance(entity, LWPolyline)
        assert entity.closed
        assert entity.dxf.layer == part.role
        assert entity.get_xdata("DECK_BUILDER")[0].value == part.id
        assert tuple((p[0], p[1]) for p in entity.get_points()) == silhouette(
            part.geometry, View.TOP
        )


def test_selected_outputs_and_manifest(tmp_path: Path) -> None:
    project = load_project(EXAMPLE)
    assembly = build_deck(project)
    output = tmp_path / "nested" / "output"
    paths = export_project(project, assembly, output)
    assert {p.name for p in paths} == {
        "deck.scad",
        "top.dxf",
        "front.dxf",
        "left.dxf",
        "right.dxf",
        "assembly.json",
    }
    manifest = json.loads((output / "assembly.json").read_text())
    assert manifest["units"] == "inches"
    assert len(manifest["parts"]) == len(assembly.parts)
    assert manifest["parts"][0]["id"] == assembly.parts[0].id


@pytest.mark.parametrize(
    ("view", "expected"),
    [
        (View.TOP, (144, 192)),
        (View.FRONT, (24, 144)),
        (View.BACK, (24, 144)),
        (View.LEFT, (24, 192)),
        (View.RIGHT, (24, 192)),
    ],
)
def test_overall_dimensions_round_trip_in_every_view(
    tmp_path: Path,
    view: View,
    expected: tuple[float, float],
) -> None:
    # Translation must not change measurements, including the datum elevation.
    assembly = build_deck(load_project(EXAMPLE)).translated(Vec3(30, -50, 10))
    document = render_dxf(assembly, view, dimensions=True)
    path = tmp_path / f"{view}.dxf"
    document.saveas(path)
    restored = ezdxf.readfile(path)
    assert not restored.audit().has_errors
    measured = []
    for entity in restored.modelspace().query("DIMENSION"):
        assert isinstance(entity, Dimension)
        measured.append(entity.get_measurement())
        assert entity.dxf.layer == "dimensions"
        assert entity.dxf.geometry in restored.blocks
    assert sorted(measured) == pytest.approx(expected)
