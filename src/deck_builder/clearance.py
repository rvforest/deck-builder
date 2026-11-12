"""Geometric checks for stair placement against concave decks and other stairs."""

from shapely.geometry import Polygon

from deck_builder.assembly import Part
from deck_builder.spacing import TOLERANCE, LayoutError


def check_stairs(footprint: Polygon, stairs: tuple[Part, ...], previous: tuple[Part, ...]) -> None:
    """Reject stairs that enter the deck plan or intersect another staircase.

    Args:
        footprint: Main deck's plan, including concave recesses.
        stairs: Parts of the new staircase.
        previous: Previously placed stair parts.

    Raises:
        LayoutError: If a positive-area overlap also has positive vertical depth.
    """
    old = [
        (part, Polygon([(v.x, v.y) for v in part.geometry.vertices]).convex_hull)
        for part in previous
    ]
    for part in stairs:
        outline = Polygon([(v.x, v.y) for v in part.geometry.vertices]).convex_hull
        if outline.intersection(footprint).area > TOLERANCE:
            raise LayoutError(f"stair {part.id!r} extends into the deck footprint")
        for other, shape in old:
            low = max(
                min(v.z for v in part.geometry.vertices), min(v.z for v in other.geometry.vertices)
            )
            high = min(
                max(v.z for v in part.geometry.vertices), max(v.z for v in other.geometry.vertices)
            )
            if high - low > TOLERANCE and outline.intersection(shape).area > TOLERANCE:
                raise LayoutError(f"stair {part.id!r} intersects {other.id!r}")
