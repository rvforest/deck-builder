"""Inspectable physical parts, with no renderer behavior or mutable factories."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Literal

from deck_builder.geometry import Mesh, Vec3

Role = Literal["rim", "joist", "decking", "support"]


@dataclass(frozen=True)
class Part:
    """A placed physical part with stable identity and optional cutting metadata."""

    id: str
    role: Role
    material: str
    geometry: Mesh
    cut_length: float | None = None
    stock: str | None = None

    def translated(self, offset: Vec3) -> Part:
        """Return a translated part, preserving its identity and cutting metadata."""
        return replace(self, geometry=self.geometry.translated(offset))


@dataclass(frozen=True)
class DeckAssembly:
    """A deterministic, immutable sequence of placed parts."""

    parts: tuple[Part, ...]

    def translated(self, offset: Vec3) -> DeckAssembly:
        """Return a translated assembly without modifying any source part."""
        return DeckAssembly(tuple(part.translated(offset) for part in self.parts))
