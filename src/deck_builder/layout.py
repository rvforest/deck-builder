"""Rectangular deck layout. Spacing limits are project inputs, not span tables."""

from deck_builder.assembly import Boundary, DeckAssembly, Part
from deck_builder.blocking import build_blocking
from deck_builder.blocks import build_supports
from deck_builder.geometry import Vec3, box
from deck_builder.spacing import spaced_positions
from deck_builder.spec import LUMBER_DIMENSIONS, Project
from deck_builder.stairs import build_stair
from deck_builder.surface import build_surface


def build_deck(project: Project) -> DeckAssembly:
    """Resolve a validated specification into a deterministic assembly.

    Args:
        project: Validated rectangular deck specification.

    Returns:
        Framing, supports, and decking with stable part identifiers.

    Raises:
        LayoutError: If the requested layout exceeds supported member limits.
    """
    footprint = project.deck.footprint
    joists = project.framing.joists
    decking = project.decking
    thickness, height = LUMBER_DIMENSIONS[joists.size]
    cross, run = footprint.width, footprint.length
    if joists.direction == "x":
        cross, run = run, cross
    joist_bottom = project.deck.elevation - decking.thickness - height
    joist_positions = spaced_positions(0, cross - thickness, joists.max_spacing)
    parts: list[Part] = []

    def member(
        identifier: str, role: str, x: float, y: float, width: float, length: float, cut: float
    ) -> None:
        # Normalize y-running joists by a proper rotation, preserving face winding.
        geometry = box(width, length, height).translated(Vec3(x, y, joist_bottom))
        if joists.direction == "x":
            geometry = geometry.rotated_z(90).translated(Vec3(run, 0, 0))
        parts.append(
            Part(
                identifier,
                "rim" if role == "rim" else "joist",
                joists.material,
                geometry,
                cut,
                joists.size,
            )
        )

    member("rim/start", "rim", 0, 0, cross, thickness, cross)
    member("rim/end", "rim", 0, run - thickness, cross, thickness, cross)
    for i, position in enumerate(joist_positions):
        member(
            f"joist/{i:04d}",
            "joist",
            position,
            thickness,
            thickness,
            run - 2 * thickness,
            run - 2 * thickness,
        )
    parts.extend(build_blocking(project, tuple(parts)))
    parts.extend(build_supports(project, joist_positions))
    width, length = footprint.width, footprint.length
    boundaries = (
        Boundary("front", Vec3(0, 0, 0), Vec3(width, 0, 0)),
        Boundary("right", Vec3(width, 0, 0), Vec3(width, length, 0)),
        Boundary("back", Vec3(width, length, 0), Vec3(0, length, 0)),
        Boundary("left", Vec3(0, length, 0), Vec3(0, 0, 0)),
    )
    parts.extend(build_surface(project))
    edges = {boundary.name: boundary for boundary in boundaries}
    for stair in project.stairs:
        parts.extend(build_stair(project, stair, edges[stair.edge]))
    return DeckAssembly(tuple(parts), boundaries)
