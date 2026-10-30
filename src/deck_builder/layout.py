"""Rectangular deck layout. Spacing limits are project inputs, not span tables."""

import math

from deck_builder.assembly import DeckAssembly, Part
from deck_builder.geometry import Vec3, box, tapered_block
from deck_builder.spec import LUMBER_DIMENSIONS, Project

TOLERANCE = 1e-8
MAX_MEMBERS = 10_000


class LayoutError(ValueError):
    """The requested layout cannot be constructed within the supported rules."""


def spaced_positions(start: float, end: float, maximum: float) -> tuple[float, ...]:
    """Divide an interval into positions no farther apart than a maximum.

    Args:
        start: First member's coordinate.
        end: Last member's coordinate, greater than start.
        maximum: Positive maximum center-to-center spacing.

    Returns:
        Equally spaced coordinates including both endpoints.

    Raises:
        LayoutError: If inputs are invalid or the member limit is exceeded.
    """
    if not all(math.isfinite(v) for v in (start, end, maximum)):
        raise LayoutError("spacing inputs must be finite")
    if end <= start or maximum <= 0:
        raise LayoutError("spacing requires end > start and maximum > 0")
    ratio = (end - start) / maximum
    if not math.isfinite(ratio) or ratio >= MAX_MEMBERS - 1:
        raise LayoutError("layout exceeds the 10,000 member limit")
    intervals = math.ceil(ratio)
    return tuple(start + i * (end - start) / intervals for i in range(intervals + 1))


def board_widths(span: float, width: float, gap: float) -> tuple[float, ...]:
    """Fill a span at a fixed gap, ripping the final board when necessary.

    A remainder no larger than the configured gap is left as an edge clearance.
    This avoids producing a zero-width board or enlarging the requested gap.

    Args:
        span: Positive distance to cover perpendicular to board length.
        width: Positive full board width.
        gap: Nonnegative gap between adjacent boards.

    Returns:
        Widths of full boards followed by a ripped board if needed.

    Raises:
        LayoutError: If inputs are invalid or the member limit is exceeded.
    """
    if not all(math.isfinite(v) for v in (span, width, gap)):
        raise LayoutError("board fitting inputs must be finite")
    if span <= 0 or width <= 0 or gap < 0:
        raise LayoutError("board fitting requires positive dimensions and a nonnegative gap")
    pitch = width + gap
    ratio = (span + gap + TOLERANCE) / pitch
    if not math.isfinite(pitch) or not math.isfinite(ratio) or ratio >= MAX_MEMBERS:
        raise LayoutError("layout exceeds the 10,000 member limit")
    count = math.floor(ratio)
    remainder = span - count * pitch
    widths = (width,) * count
    if remainder > TOLERANCE:
        widths += (min(width, remainder),)
    return widths


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
    supports = project.framing.supports
    decking = project.decking
    thickness, height = LUMBER_DIMENSIONS[joists.size]
    cross, run = footprint.width, footprint.length
    if joists.direction == "x":
        cross, run = run, cross
    joist_bottom = project.deck.elevation - decking.thickness - height
    joist_positions = spaced_positions(0, cross - thickness, joists.max_spacing)
    support_positions = spaced_positions(
        supports.edge_setback,
        run - supports.edge_setback,
        supports.max_spacing,
    )
    if (
        joist_positions[1] - joist_positions[0] < supports.base_width - TOLERANCE
        or support_positions[1] - support_positions[0] < supports.base_width - TOLERANCE
    ):
        raise LayoutError("support blocks overlap; increase spacing or reduce block base_width")
    if len(joist_positions) * len(support_positions) > MAX_MEMBERS:
        raise LayoutError("layout exceeds the 10,000 support limit")
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
        for j, along in enumerate(support_positions):
            geometry = tapered_block(
                supports.base_width, supports.top_width, supports.block_height
            ).translated(
                Vec3(
                    position + thickness / 2,
                    along,
                    joist_bottom - supports.block_height,
                )
            )
            if joists.direction == "x":
                geometry = geometry.rotated_z(90).translated(Vec3(run, 0, 0))
            parts.append(Part(f"support/{i:04d}/{j:04d}", "support", "concrete", geometry))

    position = 0.0
    for i, board_width in enumerate(board_widths(run, decking.width, decking.gap)):
        geometry = box(cross, board_width, decking.thickness).translated(
            Vec3(0, position, project.deck.elevation - decking.thickness),
        )
        if joists.direction == "x":
            geometry = geometry.rotated_z(90).translated(Vec3(run, 0, 0))
        parts.append(
            Part(
                f"decking/{i:04d}",
                "decking",
                decking.material,
                geometry,
                cross,
                f"{board_width:g}x{decking.thickness:g}",
            )
        )
        position += board_width + decking.gap
    return DeckAssembly(tuple(parts))
