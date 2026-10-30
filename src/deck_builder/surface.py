"""Decking fields and mitered perimeter borders in world coordinates."""

from deck_builder.assembly import Part
from deck_builder.geometry import Vec3, box, extrude_polygon
from deck_builder.spacing import board_widths
from deck_builder.spec import Project


def build_surface(project: Project) -> tuple[Part, ...]:
    """Lay out interior decking and zero or more mitered border rows.

    Args:
        project: Validated deck specification.

    Returns:
        Decking and border parts with cutting metadata and world-space geometry.
    """
    decking = project.decking
    width, length = project.deck.footprint.width, project.deck.footprint.length
    w, g, t = decking.width, decking.gap, decking.thickness
    z = project.deck.elevation - t
    inset = decking.border.rows * (w + g)
    inner_width, inner_length = width - 2 * inset, length - 2 * inset
    parts: list[Part] = []
    span, cut = (
        (inner_length, inner_width) if decking.direction == "x" else (inner_width, inner_length)
    )
    position = inset
    for i, board_width in enumerate(board_widths(span, w, g)):
        if decking.direction == "x":
            geometry = box(cut, board_width, t).translated(Vec3(inset, position, z))
        else:
            geometry = box(board_width, cut, t).translated(Vec3(position, inset, z))
        parts.append(
            Part(
                f"decking/{i:04d}",
                "decking",
                decking.material,
                geometry,
                cut,
                f"{board_width:g}x{t:g}",
            )
        )
        position += board_width + g
    for row in range(decking.border.rows):
        lo = row * (w + g)
        x, y = width - lo, length - lo
        polygons = {
            "front": ((lo, lo), (x, lo), (x - w, lo + w), (lo + w, lo + w)),
            "right": ((x, lo), (x, y), (x - w, y - w), (x - w, lo + w)),
            "back": ((x, y), (lo, y), (lo + w, y - w), (x - w, y - w)),
            "left": ((lo, y), (lo, lo), (lo + w, lo + w), (lo + w, y - w)),
        }
        for name, polygon in polygons.items():
            geometry = extrude_polygon(polygon, t).translated(Vec3(0, 0, z))
            cut_length = (width if name in ("front", "back") else length) - 2 * lo
            parts.append(
                Part(
                    f"border/{row:02d}/{name}",
                    "border",
                    decking.material,
                    geometry,
                    cut_length,
                    f"{w:g}x{t:g}",
                    45,
                    45,
                )
            )
    return tuple(parts)
