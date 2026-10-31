"""Explicit additional framing members with geometric placement checks."""

from shapely.geometry import box as plan_box

from deck_builder.assembly import Part
from deck_builder.geometry import Vec3, box
from deck_builder.spacing import TOLERANCE, LayoutError
from deck_builder.spec import LUMBER_DIMENSIONS, Project


def build_blocking(project: Project, existing: tuple[Part, ...]) -> tuple[Part, ...]:
    """Place configured blocking flush with the top of the main framing.

    Args:
        project: Specification with explicitly named extra framing members.
        existing: Main framing to check for solid intersections.

    Returns:
        Additional members with stable IDs and their selected stock dimensions.

    Raises:
        LayoutError: If a member exceeds the footprint or framing depth, or
            intersects another framing member. Touching faces are allowed.
    """
    footprint = project.deck.footprint
    frame_height = LUMBER_DIMENSIONS[project.framing.joists.size][1]
    parts: list[Part] = []
    for block in project.framing.blocking:
        size = block.size or project.framing.joists.size
        thickness, height = LUMBER_DIMENSIONS[size]
        width, length = (
            (block.length, thickness) if block.direction == "x" else (thickness, block.length)
        )
        if not footprint.plan().polygon.covers(
            plan_box(block.x, block.y, block.x + width, block.y + length)
        ):
            raise LayoutError(f"blocking {block.name!r} extends outside the footprint")
        if height > frame_height:
            raise LayoutError(f"blocking {block.name!r} exceeds the main framing depth")
        bottom = project.deck.elevation - project.decking.thickness - height
        geometry = box(width, length, height).translated(Vec3(block.x, block.y, bottom))
        for other in (*existing, *parts):
            vertices = other.geometry.vertices
            if (
                min(block.x + width, max(v.x for v in vertices))
                - max(block.x, min(v.x for v in vertices))
                > TOLERANCE
                and min(block.y + length, max(v.y for v in vertices))
                - max(block.y, min(v.y for v in vertices))
                > TOLERANCE
            ):
                raise LayoutError(f"blocking {block.name!r} intersects {other.id!r}")
        parts.append(
            Part(
                f"blocking/{block.name}",
                "blocking",
                project.framing.joists.material,
                geometry,
                block.length,
                size,
            )
        )
    return tuple(parts)
