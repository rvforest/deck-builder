"""Pure spacing and board-fitting operations shared by layout planners."""

import math

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
