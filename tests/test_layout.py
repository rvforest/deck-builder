import math

import pytest

from deck_builder.geometry import Vec3, box
from deck_builder.layout import LayoutError, board_widths, build_deck, spaced_positions
from deck_builder.spec import Project


def project(direction: str = "y") -> Project:
    return Project.model_validate(
        {
            "deck": {"footprint": {"width": 144, "length": 192}},
            "framing": {"joists": {"direction": direction}},
            "decking": {"direction": "x" if direction == "y" else "y"},
        }
    )


def test_spacing_includes_endpoints_and_respects_maximum() -> None:
    positions = spaced_positions(12, 180, 72)
    assert positions == (12, 68, 124, 180)
    assert max(b - a for a, b in zip(positions, positions[1:], strict=False)) <= 72


@pytest.mark.parametrize(
    ("span", "width", "gap", "expected"),
    [
        (11.25, 5.5, 0.25, (5.5, 5.5)),
        (12, 5.5, 0.25, (5.5, 5.5, 0.5)),
        (11.4, 5.5, 0.25, (5.5, 5.5)),
        (3, 5.5, 0.25, (3,)),
        (11, 5.5, 0, (5.5, 5.5)),
        (0.3, 0.1, 0, (0.1, 0.1, 0.1)),
    ],
)
def test_board_fitting(span: float, width: float, gap: float, expected: tuple[float, ...]) -> None:
    result = board_widths(span, width, gap)
    assert result == pytest.approx(expected)
    coverage = sum(result) + gap * (len(result) - 1)
    assert coverage <= span + 1e-8
    assert span - coverage <= gap + 1e-8


@pytest.mark.parametrize("direction", ["x", "y"])
def test_layout_bounds_support_alignment_and_determinism(direction: str) -> None:
    spec = project(direction)
    assembly = build_deck(spec)
    assert assembly == build_deck(spec)
    assert len({part.id for part in assembly.parts}) == len(assembly.parts)
    decking = [p for p in assembly.parts if p.role == "decking"]
    vertices = [v for p in decking for v in p.geometry.vertices]
    assert min(v.x for v in vertices) == pytest.approx(0)
    assert max(v.x for v in vertices) == pytest.approx(144)
    assert min(v.y for v in vertices) == pytest.approx(0)
    assert max(v.y for v in vertices) == pytest.approx(192)
    assert max(v.z for v in vertices) == pytest.approx(24)
    joists = [p for p in assembly.parts if p.role == "joist"]
    supports = [p for p in assembly.parts if p.role == "support"]
    axis = "x" if direction == "y" else "y"
    centers = {
        (
            min(getattr(v, axis) for v in p.geometry.vertices)
            + max(getattr(v, axis) for v in p.geometry.vertices)
        )
        / 2
        for p in joists
    }
    for support in supports:
        center = sum(getattr(v, axis) for v in support.geometry.vertices) / 8
        assert any(math.isclose(center, j, abs_tol=1e-8) for j in centers)
        assert max(v.z for v in support.geometry.vertices) == pytest.approx(24 - 0.94 - 7.25)
        assert min(v.z for v in support.geometry.vertices) >= 0
    assert all(p.cut_length and p.cut_length > 0 for p in assembly.parts if p.role != "support")


def test_translation_preserves_metadata_and_source() -> None:
    assembly = build_deck(project())
    moved = assembly.translated(Vec3(10, -20, 3))
    for before, after in zip(assembly.parts, moved.parts, strict=True):
        assert (before.id, before.role, before.material, before.stock, before.cut_length) == (
            after.id,
            after.role,
            after.material,
            after.stock,
            after.cut_length,
        )
        assert after.geometry.vertices[0] == before.geometry.vertices[0].translated(
            Vec3(10, -20, 3)
        )
    assert assembly == build_deck(project())


def test_rotation_and_translation_order() -> None:
    mesh = box(2, 4, 6).rotated_z(90).translated(Vec3(10, 20, 30))
    point = mesh.vertices[2]
    assert (point.x, point.y, point.z) == pytest.approx((6, 22, 30))


@pytest.mark.parametrize("args", [(0, 0, 1), (1, 0, 1), (0, 1, 0), (0, math.inf, 1)])
def test_invalid_spacing(args: tuple[float, float, float]) -> None:
    with pytest.raises(LayoutError):
        spaced_positions(*args)


def test_layout_limits_are_explicit() -> None:
    with pytest.raises(LayoutError, match="limit"):
        spaced_positions(0, 100_000, 1)
    with pytest.raises(LayoutError, match="limit"):
        board_widths(100_000, 1, 0)
