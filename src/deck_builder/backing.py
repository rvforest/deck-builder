"""Continuous border and seam backing assembled from ripped framing stock."""

from shapely import union_all
from shapely.geometry import Polygon

from deck_builder.assembly import Part
from deck_builder.geometry import Vec3, box
from deck_builder.plan import rectangles
from deck_builder.spacing import MAX_MEMBERS, TOLERANCE, LayoutError, board_widths
from deck_builder.spec import LUMBER_DIMENSIONS, Project


def build_backing(project: Project, frame: tuple[Part, ...]) -> tuple[Part, ...]:
    """Fill the border's bearing region without intersecting existing framing.

    Args:
        project: Deck specification, including the optional backing switch.
        frame: Existing framing, including explicit blocking and supports.

    Returns:
        Rectangular stock pieces providing continuous bearing below border rows
        and half a framing thickness beyond their interior decking seam.

    Raises:
        LayoutError: If the backing would exceed the part limit.
    """
    decking = project.decking
    if not decking.border.rows or not decking.border.backing:
        return ()
    thickness, height = LUMBER_DIMENSIONS[project.framing.joists.size]
    footprint = project.deck.footprint.plan().polygon
    inset = decking.border.rows * (decking.width + decking.gap) + thickness / 2
    bearing = footprint.difference(footprint.buffer(-inset, join_style="mitre"))
    occupied = union_all(
        [
            Polygon([(v.x, v.y) for v in p.geometry.vertices]).convex_hull
            for p in frame
            if p.role != "support"
        ]
    )
    missing = bearing.difference(occupied)
    bottom = project.deck.elevation - decking.thickness - height
    parts: list[Part] = []
    for a, b, c, d in rectangles(missing, project.framing.joists.direction):
        horizontal = c - a >= d - b
        span = d - b if horizontal else c - a
        position = b if horizontal else a
        for width in board_widths(span, thickness, 0):
            if width <= TOLERANCE:
                continue
            w, length = (c - a, width) if horizontal else (width, d - b)
            x, y = (a, position) if horizontal else (position, b)
            cut = c - a if horizontal else d - b
            parts.append(
                Part(
                    f"backing/{len(parts):04d}",
                    "backing",
                    project.framing.joists.material,
                    box(w, length, height).translated(Vec3(x, y, bottom)),
                    cut,
                    f"{width:g}x{height:g}",
                )
            )
            position += width
            if len(parts) > MAX_MEMBERS:
                raise LayoutError("border backing exceeds the 10,000 part limit")
    return tuple(parts)
