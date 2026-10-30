"""Immutable meshes shared by every exporter, independent of CAD libraries."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace


@dataclass(frozen=True)
class Vec3:
    """An immutable point or offset in world coordinates, measured in inches."""

    x: float
    y: float
    z: float

    def translated(self, offset: Vec3) -> Vec3:
        """Return a point shifted by the given offset."""
        return Vec3(self.x + offset.x, self.y + offset.y, self.z + offset.z)


@dataclass(frozen=True)
class Mesh:
    """A solid's vertices and outward-wound polygon faces."""

    vertices: tuple[Vec3, ...]
    faces: tuple[tuple[int, ...], ...]

    def translated(self, offset: Vec3) -> Mesh:
        """Return a mesh with all vertices shifted by the given offset."""
        return replace(self, vertices=tuple(v.translated(offset) for v in self.vertices))

    def rotated_z(self, degrees: float) -> Mesh:
        """Rotate about the world origin; translation order is explicit."""
        angle = math.radians(degrees)
        c, s = math.cos(angle), math.sin(angle)
        return replace(
            self,
            vertices=tuple(Vec3(c * v.x - s * v.y, s * v.x + c * v.y, v.z) for v in self.vertices),
        )


# Outward winding, including a downward-facing base.
FACES = ((0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7))


def box(width: float, length: float, height: float) -> Mesh:
    """Build an axis-aligned box with its minimum corner at the origin."""
    return Mesh(
        (
            Vec3(0, 0, 0),
            Vec3(width, 0, 0),
            Vec3(width, length, 0),
            Vec3(0, length, 0),
            Vec3(0, 0, height),
            Vec3(width, 0, height),
            Vec3(width, length, height),
            Vec3(0, length, height),
        ),
        FACES,
    )


def tapered_block(base: float, top: float, height: float) -> Mesh:
    """A square block centered on x=y=0 with its base at z=0."""
    b, t = base / 2, top / 2
    return Mesh(
        (
            Vec3(-b, -b, 0),
            Vec3(b, -b, 0),
            Vec3(b, b, 0),
            Vec3(-b, b, 0),
            Vec3(-t, -t, height),
            Vec3(t, -t, height),
            Vec3(t, t, height),
            Vec3(-t, t, height),
        ),
        FACES,
    )
