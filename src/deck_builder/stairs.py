"""Stacked box stair assemblies attached to named rectangular boundaries."""

import math

from deck_builder.assembly import Boundary, Part
from deck_builder.geometry import Vec3, box
from deck_builder.spacing import MAX_MEMBERS, LayoutError, board_widths, spaced_positions
from deck_builder.spec import LUMBER_DIMENSIONS, Project, Stair


def build_stair(project: Project, stair: Stair, boundary: Boundary) -> tuple[Part, ...]:
    """Build stacked, fully decked box tiers with equal rises to ground.

    Args:
        project: Specification supplying finished elevation and decking stock.
        stair: Named stair configuration, including attachment offset and width.
        boundary: Counterclockwise edge that the stair attaches to.

    Returns:
        Frame and tread parts placed outside the footprint. Lower platforms are
        fully decked so each upper frame bears on the preceding platform.

    Raises:
        LayoutError: If tier count, frame stock, or part limits cannot be satisfied.
    """
    total_rise = project.deck.elevation - stair.ground_elevation
    ratio = total_rise / stair.max_rise
    if not math.isfinite(ratio) or ratio > 100:
        raise LayoutError(f"stair {stair.name!r} exceeds the 100 riser limit")
    risers = math.ceil(ratio)
    if risers < 2:
        raise LayoutError("stairs need at least one tread; reduce max_rise")
    rise = total_rise / risers
    thickness, stock_height = LUMBER_DIMENSIONS[stair.frame_size]
    tread = project.decking
    frame_height = rise - tread.thickness
    if frame_height <= 0 or frame_height > stock_height:
        raise LayoutError(f"stair {stair.name!r} rise cannot fit its frame stock and decking")
    positions = spaced_positions(0, stair.width - thickness, stair.max_spacing)
    parts: list[Part] = []
    for tier in range(1, risers):
        depth = stair.tread_depth * (risers - tier)
        base = stair.ground_elevation + (tier - 1) * rise
        prefix = f"stair/{stair.name}/tier/{tier:03d}"

        frame_inputs = [
            ("inner-rim", 0.0, -thickness, stair.width, thickness, stair.width),
            ("outer-rim", 0.0, -depth, stair.width, thickness, stair.width),
            *(
                (
                    f"joist/{j:04d}",
                    x,
                    -depth + thickness,
                    thickness,
                    depth - 2 * thickness,
                    depth - 2 * thickness,
                )
                for j, x in enumerate(positions)
            ),
        ]
        for identifier, x, y, w, d, cut in frame_inputs:
            geometry = box(w, d, frame_height).translated(Vec3(stair.offset + x, y, base))
            parts.append(
                Part(
                    f"{prefix}/frame/{identifier}",
                    "stair_frame",
                    project.framing.joists.material,
                    boundary.place(geometry),
                    cut,
                    f"{thickness:g}x{frame_height:g}",
                )
            )

        position = -depth
        for j, width in enumerate(board_widths(depth, tread.width, tread.gap)):
            geometry = box(stair.width, width, tread.thickness).translated(
                Vec3(stair.offset, position, base + frame_height),
            )
            parts.append(
                Part(
                    f"{prefix}/tread/{j:04d}",
                    "stair_tread",
                    tread.material,
                    boundary.place(geometry),
                    stair.width,
                    f"{width:g}x{tread.thickness:g}",
                )
            )
            position += width + tread.gap
        if len(parts) > MAX_MEMBERS:
            raise LayoutError(f"stair {stair.name!r} exceeds the 10,000 part limit")
    return tuple(parts)
