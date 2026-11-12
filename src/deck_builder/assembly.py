"""Inspectable physical parts, with no renderer behavior or mutable factories."""

from __future__ import annotations

import math
from dataclasses import dataclass, replace
from typing import Literal

from deck_builder.geometry import Mesh, Vec3

Role = Literal[
    "rim",
    "joist",
    "decking",
    "support",
    "border",
    "stair_frame",
    "stair_tread",
    "blocking",
    "backing",
]


@dataclass(frozen=True)
class Part:
    """A placed physical part with stable identity and optional cutting metadata."""

    id: str
    role: Role
    material: str
    geometry: Mesh
    cut_length: float | None = None
    stock: str | None = None
    start_miter: float | None = None
    end_miter: float | None = None

    def translated(self, offset: Vec3) -> Part:
        """Return a translated part, preserving its identity and cutting metadata."""
        return replace(self, geometry=self.geometry.translated(offset))


@dataclass(frozen=True)
class Boundary:
    """A counterclockwise footprint edge with stable identity and local placement."""

    name: str
    start: Vec3
    end: Vec3

    @property
    def length(self) -> float:
        """Return the plan length in inches."""
        return math.hypot(self.end.x - self.start.x, self.end.y - self.start.y)

    def place(self, geometry: Mesh) -> Mesh:
        """Place local x along the edge and local negative y outside the deck."""
        angle = math.degrees(math.atan2(self.end.y - self.start.y, self.end.x - self.start.x))
        return geometry.rotated_z(angle).translated(self.start)

    def translated(self, offset: Vec3) -> Boundary:
        """Return the edge shifted by an offset, preserving its name."""
        return replace(self, start=self.start.translated(offset), end=self.end.translated(offset))


@dataclass(frozen=True)
class Connection:
    """A shared bay seam backed by two touching rim members."""

    id: str
    start: Vec3
    end: Vec3
    members: tuple[str, str]
    kind: str = "double_rim"

    def translated(self, offset: Vec3) -> Connection:
        """Translate the seam while preserving its connected part identities."""
        return replace(self, start=self.start.translated(offset), end=self.end.translated(offset))


@dataclass(frozen=True)
class DeckAssembly:
    """A deterministic, immutable sequence of placed parts."""

    parts: tuple[Part, ...]
    boundaries: tuple[Boundary, ...] = ()
    connections: tuple[Connection, ...] = ()

    def translated(self, offset: Vec3) -> DeckAssembly:
        """Return a translated assembly without modifying any source part."""
        return DeckAssembly(
            tuple(part.translated(offset) for part in self.parts),
            tuple(edge.translated(offset) for edge in self.boundaries),
            tuple(connection.translated(offset) for connection in self.connections),
        )
