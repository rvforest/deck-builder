"""Shared orthographic projection for convex part silhouettes."""

from enum import StrEnum

from deck_builder.geometry import Mesh, Vec3

Point2 = tuple[float, float]


class View(StrEnum):
    """Named views with a fixed screen-horizontal axis and world vertical."""

    TOP = "top"
    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"


def project_point(point: Vec3, view: View) -> Point2:
    """Project a world point into a named view.

    Args:
        point: A point in world coordinates.
        view: Top uses x/y; elevations use z vertically. Opposing views mirror
            the horizontal coordinate about the world origin.

    Returns:
        The horizontal and vertical drawing coordinates in inches.
    """
    match view:
        case View.TOP:
            return point.x, point.y
        case View.FRONT:
            return point.x, point.z
        case View.BACK:
            return -point.x, point.z
        case View.LEFT:
            return -point.y, point.z
        case View.RIGHT:
            return point.y, point.z


def silhouette(mesh: Mesh, view: View) -> tuple[Point2, ...]:
    """Find a convex solid's projected outline after all world transforms.

    Args:
        mesh: A convex part mesh. Concave solids must be decomposed first.
        view: The desired orthographic view.

    Returns:
        Counterclockwise outline points without a repeated closing vertex.
    """
    points = sorted({tuple(round(v, 10) for v in project_point(p, view)) for p in mesh.vertices})

    def cross(o: Point2, a: Point2, b: Point2) -> float:
        return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

    lower: list[Point2] = []
    upper: list[Point2] = []
    for point in points:
        p = (point[0], point[1])
        while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
            lower.pop()
        lower.append(p)
    for point in reversed(points):
        p = (point[0], point[1])
        while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
            upper.pop()
        upper.append(p)
    return tuple(lower[:-1] + upper[:-1])
