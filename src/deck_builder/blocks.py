"""Automatic support grids and validated manual support placements."""

import math
from bisect import bisect_left
from collections import defaultdict

from deck_builder.assembly import Part
from deck_builder.geometry import Vec3, tapered_block
from deck_builder.spacing import MAX_MEMBERS, TOLERANCE, LayoutError, spaced_positions
from deck_builder.spec import LUMBER_DIMENSIONS, Project


def build_supports(project: Project, joists: tuple[float, ...]) -> tuple[Part, ...]:
    """Resolve support locations, preserving joist alignment and spacing limits.

    Args:
        project: Validated deck and support configuration.
        joists: Joist minimum cross-axis coordinates in the local y-running layout.

    Returns:
        Tapered support blocks with deterministic automatic or user-named IDs.

    Raises:
        LayoutError: If manual locations miss joists, overlap, or fail coverage,
            setback, spacing, or resource limits.
    """
    supports = project.framing.supports
    thickness, height = LUMBER_DIMENSIONS[project.framing.joists.size]
    direction = project.framing.joists.direction
    footprint = project.deck.footprint
    run = footprint.length if direction == "y" else footprint.width
    centers = tuple(p + thickness / 2 for p in joists)
    locations: list[tuple[str, float, float]] = []
    if supports.locations is None:
        along = spaced_positions(
            supports.edge_setback, run - supports.edge_setback, supports.max_spacing
        )
        if len(centers) * len(along) > MAX_MEMBERS:
            raise LayoutError("layout exceeds the 10,000 support limit")
        for i, center in enumerate(centers):
            for j, position in enumerate(along):
                x, y = (center, position) if direction == "y" else (run - position, center)
                locations.append((f"support/{i:04d}/{j:04d}", x, y))
    else:
        grouped: dict[int, list[float]] = defaultdict(list)
        for location in supports.locations:
            cross = location.x if direction == "y" else location.y
            position = location.y if direction == "y" else run - location.x
            insertion = bisect_left(centers, cross)
            candidates = range(max(0, insertion - 1), min(len(centers), insertion + 1))
            index = min(candidates, key=lambda i: abs(centers[i] - cross))
            if abs(centers[index] - cross) > TOLERANCE:
                raise LayoutError(f"support {location.name!r} is not centered under a joist")
            if not thickness <= position <= run - thickness:
                raise LayoutError(f"support {location.name!r} is outside the clear joist run")
            grouped[index].append(position)
            locations.append((f"support/{location.name}", location.x, location.y))
        for index in range(len(centers)):
            positions = sorted(grouped[index])
            if len(positions) < 2:
                raise LayoutError(f"joist {index} requires at least two manual supports")
            if (
                positions[0] > supports.edge_setback + TOLERANCE
                or run - positions[-1] > supports.edge_setback + TOLERANCE
            ):
                raise LayoutError(f"joist {index} manual supports exceed edge_setback")
            if any(
                b - a > supports.max_spacing + TOLERANCE
                for a, b in zip(positions, positions[1:], strict=False)
            ):
                raise LayoutError(f"joist {index} manual supports exceed max_spacing")
    # Spatial hashing checks neighboring bases without a quadratic all-pairs scan.
    cells: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    width = supports.base_width
    for name, x, y in locations:
        cell = math.floor(x / width), math.floor(y / width)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for a, b in cells.get((cell[0] + dx, cell[1] + dy), ()):
                    if abs(x - a) < width - TOLERANCE and abs(y - b) < width - TOLERANCE:
                        raise LayoutError(f"support blocks overlap near {name!r}")
        cells[cell].append((x, y))
    base = project.deck.elevation - project.decking.thickness - height - supports.block_height
    geometry = tapered_block(width, supports.top_width, supports.block_height)
    return tuple(
        Part(name, "support", "concrete", geometry.translated(Vec3(x, y, base)))
        for name, x, y in locations
    )
