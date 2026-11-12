"""Decking fields and mitered borders following orthogonal footprints."""

import math

from shapely.geometry import Polygon
from shapely.geometry import box as plan_box

from deck_builder.assembly import Part
from deck_builder.geometry import Vec3, box, extrude_polygon
from deck_builder.plan import rectangles
from deck_builder.spacing import MAX_MEMBERS, LayoutError, board_widths
from deck_builder.spec import Project


def build_surface(project: Project) -> tuple[Part, ...]:
    """Lay out straight boards and mitered borders without covering footprint voids.

    Args:
        project: Validated footprint and decking specification.

    Returns:
        Physical board pieces with cutting metadata and world-space geometry.

    Raises:
        LayoutError: If borders consume a limb or the board limit is exceeded.
    """
    decking = project.decking
    plan = project.deck.footprint.plan()
    w, g, t = decking.width, decking.gap, decking.thickness
    z = project.deck.elevation - t
    inset = decking.border.rows * (w + g)
    interior = Polygon(plan.inset(inset))
    x0, y0, x1, y1 = interior.bounds
    horizontal = decking.direction == "x"
    span = y1 - y0 if horizontal else x1 - x0
    position = y0 if horizontal else x0
    parts: list[Part] = []
    for i, board_width in enumerate(board_widths(span, w, g)):
        band = (
            plan_box(x0, position, x1, position + board_width)
            if horizontal
            else plan_box(position, y0, position + board_width, y1)
        )
        pieces = rectangles(interior.intersection(band), "y" if horizontal else "x")
        for j, (a, b, c, d) in enumerate(pieces):
            geometry = box(c - a, d - b, t).translated(Vec3(a, b, z))
            cut = c - a if horizontal else d - b
            actual_width = d - b if horizontal else c - a
            identifier = f"decking/{i:04d}" + (f"/{j:02d}" if len(pieces) > 1 else "")
            parts.append(
                Part(
                    identifier,
                    "decking",
                    decking.material,
                    geometry,
                    cut,
                    f"{actual_width:g}x{t:g}",
                )
            )
        position += board_width + g
        if len(parts) > MAX_MEMBERS:
            raise LayoutError("surface exceeds the 10,000 board limit")
    for row in range(decking.border.rows):
        outer = plan.inset(row * (w + g))
        inner = plan.inset(row * (w + g) + w)
        for i, name in enumerate(plan.names):
            j = (i + 1) % len(outer)
            polygon = (outer[i], outer[j], inner[j], inner[i])
            geometry = extrude_polygon(polygon, t).translated(Vec3(0, 0, z))
            cut = max(math.dist(outer[i], outer[j]), math.dist(inner[i], inner[j]))
            parts.append(
                Part(
                    f"border/{row:02d}/{name}",
                    "border",
                    decking.material,
                    geometry,
                    cut,
                    f"{w:g}x{t:g}",
                    45,
                    45,
                )
            )
    return tuple(parts)
