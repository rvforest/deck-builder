"""Validated orthogonal footprint geometry and deterministic rectangular partitions."""

from dataclasses import dataclass

from shapely.geometry import GeometryCollection, MultiPolygon, Polygon, box
from shapely.geometry.base import BaseGeometry

from deck_builder.assembly import Boundary
from deck_builder.geometry import Vec3
from deck_builder.spacing import TOLERANCE, LayoutError

Point = tuple[float, float]
Rectangle = tuple[float, float, float, float]


def validate_polygon(points: tuple[Point, ...]) -> None:
    """Require a simple counterclockwise orthogonal ring starting at the datum."""
    polygon = Polygon(points)
    if not polygon.is_valid or polygon.area <= 0 or not polygon.exterior.is_ccw:
        raise ValueError("polygon must be simple, counterclockwise, and have positive area")
    if min(p[0] for p in points) != 0 or min(p[1] for p in points) != 0:
        raise ValueError("polygon minimum x and y must both be zero")
    for i, a in enumerate(points):
        b, c = points[(i + 1) % len(points)], points[(i + 2) % len(points)]
        if (a[0] == b[0]) == (a[1] == b[1]):
            raise ValueError("polygon edges must be nonzero and axis aligned")
        if (b[0] - a[0]) * (c[1] - b[1]) == (b[1] - a[1]) * (c[0] - b[0]):
            raise ValueError("polygon must not contain redundant collinear vertices")


@dataclass(frozen=True)
class Plan:
    """A named outer ring shared by framing, surfaces, stairs, and drawings."""

    names: tuple[str, ...]
    points: tuple[Point, ...]

    @property
    def polygon(self) -> Polygon:
        """Return the plan as a planar polygon."""
        return Polygon(self.points)

    @property
    def boundaries(self) -> tuple[Boundary, ...]:
        """Return counterclockwise named edges at z=0."""
        return tuple(
            Boundary(name, Vec3(*p, 0), Vec3(*self.points[(i + 1) % len(self.points)], 0))
            for i, (name, p) in enumerate(zip(self.names, self.points, strict=True))
        )

    def inset(self, distance: float) -> tuple[Point, ...]:
        """Offset every edge inward, rejecting collapsed or split footprints.

        Args:
            distance: Nonnegative inward offset in inches.

        Returns:
            Vertices corresponding to the original named edges.

        Raises:
            LayoutError: If the offset changes topology or consumes a narrow limb.
        """
        result: list[Point] = []
        n = len(self.points)
        for i, (x, y) in enumerate(self.points):
            a, b = self.points[(i - 1) % n], self.points[(i + 1) % n]
            before = (x - a[0], y - a[1])
            after = (b[0] - x, b[1] - y)
            la, lb = abs(before[0]) + abs(before[1]), abs(after[0]) + abs(after[1])
            result.append(
                (
                    x - distance * (before[1] / la + after[1] / lb),
                    y + distance * (before[0] / la + after[0] / lb),
                )
            )
        shape = Polygon(result)
        expected = self.polygon.buffer(-distance, join_style="mitre")
        if (
            not shape.is_valid
            or not isinstance(expected, Polygon)
            or expected.is_empty
            or shape.symmetric_difference(expected).area > 1e-6
        ):
            raise LayoutError("footprint inset consumes or splits a narrow limb")
        return tuple(result)


def polygons(shape: BaseGeometry) -> tuple[Polygon, ...]:
    """Extract positive-area polygon components, ignoring zero-area contacts."""
    if isinstance(shape, Polygon):
        return (shape,) if shape.area > TOLERANCE else ()
    if isinstance(shape, MultiPolygon | GeometryCollection):
        return tuple(p for child in shape.geoms for p in polygons(child))
    return ()


def rectangles(shape: BaseGeometry, axis: str) -> tuple[Rectangle, ...]:
    """Partition an orthogonal shape into rectangles, merging unchanged spans.

    Args:
        shape: Orthogonal polygon geometry without holes.
        axis: Direction along which slab boundaries are introduced: x or y.

    Returns:
        Disjoint rectangular bounds in a deterministic order.

    Raises:
        LayoutError: If the geometry contains unsupported nonrectangular slabs.
    """
    components = polygons(shape)
    index = 0 if axis == "x" else 1
    levels = sorted(
        {
            float(p[index])
            for poly in components
            for ring in (poly.exterior, *poly.interiors)
            for p in ring.coords
        }
    )
    result: list[Rectangle] = []
    if not components:
        return ()
    x0, y0, x1, y1 = shape.bounds
    active: dict[tuple[float, float], int] = {}
    for lo, hi in zip(levels, levels[1:], strict=False):
        slab = box(lo, y0, hi, y1) if axis == "x" else box(x0, lo, x1, hi)
        current: dict[tuple[float, float], int] = {}
        for poly in sorted(polygons(shape.intersection(slab)), key=lambda p: p.bounds):
            a, b, c, d = poly.bounds
            if abs(poly.area - (c - a) * (d - b)) > 1e-6:
                raise LayoutError("footprint requires axis-aligned rectangular bays")
            key = (b, d) if axis == "x" else (a, c)
            if key in active:
                position = active[key]
                old = result[position]
                result[position] = (old[0], b, c, d) if axis == "x" else (a, old[1], c, d)
            else:
                position = len(result)
                result.append((a, b, c, d))
            current[key] = position
        active = current
    return tuple(result)
