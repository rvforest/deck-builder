"""Orchestrate footprint framing, surfaces, stairs, and connection metadata."""

from deck_builder.assembly import DeckAssembly
from deck_builder.backing import build_backing
from deck_builder.bays import build_bays
from deck_builder.blocking import build_blocking
from deck_builder.clearance import check_stairs
from deck_builder.framing import build_frame
from deck_builder.spec import PolygonFootprint, Project
from deck_builder.stairs import build_stair
from deck_builder.surface import build_surface


def build_deck(project: Project) -> DeckAssembly:
    """Resolve a validated project into physical parts and framing connections.

    Args:
        project: Validated rectangular or orthogonal polygon specification.

    Returns:
        A deterministic assembly in world coordinates.

    Raises:
        LayoutError: If framing, support, or geometry rules cannot be satisfied.
    """
    if isinstance(project.deck.footprint, PolygonFootprint):
        frame, connections = build_bays(project)
        frame += build_blocking(project, frame)
    else:
        frame, connections = build_frame(project), ()
    parts = list(frame)
    parts.extend(build_backing(project, frame))
    parts.extend(build_surface(project))
    boundaries = project.deck.footprint.plan().boundaries
    edges = {boundary.name: boundary for boundary in boundaries}
    placed = []
    for stair in project.stairs:
        new = build_stair(project, stair, edges[stair.edge])
        check_stairs(project.deck.footprint.plan().polygon, new, tuple(placed))
        placed.extend(new)
        parts.extend(new)
    return DeckAssembly(tuple(parts), boundaries, connections)
