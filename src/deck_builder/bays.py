"""Concave footprints framed as connected rectangular bays."""

from dataclasses import replace

from deck_builder.assembly import Connection, Part
from deck_builder.framing import build_frame
from deck_builder.geometry import Vec3
from deck_builder.plan import Rectangle, rectangles
from deck_builder.spacing import MAX_MEMBERS, TOLERANCE, LayoutError
from deck_builder.spec import Project


def build_bays(project: Project) -> tuple[tuple[Part, ...], tuple[Connection, ...]]:
    """Partition a polygon perpendicular to joists and connect its bay rims.

    Args:
        project: Validated orthogonal footprint and layout options.

    Returns:
        Framing and supports, plus named seams identifying touching double rims.

    Raises:
        LayoutError: If a bay cannot accommodate framing or configured supports.
    """
    axis = project.framing.joists.direction
    bounds = rectangles(project.deck.footprint.plan().polygon, axis)
    parts: list[Part] = []
    for i, (x0, y0, x1, y1) in enumerate(bounds):
        data = project.model_dump()
        data["deck"]["footprint"] = {"width": x1 - x0, "length": y1 - y0}
        data["decking"]["border"]["rows"] = 0
        data["framing"]["blocking"] = ()
        data["stairs"] = ()
        manual = project.framing.supports.locations
        if manual is not None:
            data["framing"]["supports"]["locations"] = tuple(
                {"name": p.name, "x": p.x - x0, "y": p.y - y0}
                for p in manual
                if x0 <= p.x <= x1 and y0 <= p.y <= y1
            )
        try:
            local = build_frame(Project.model_validate(data))
        except ValueError as error:
            raise LayoutError(f"bay {i} cannot be framed: {error}") from error
        parts.extend(
            replace(part.translated(Vec3(x0, y0, 0)), id=f"bay/{i:03d}/{part.id}") for part in local
        )
        if len(parts) > MAX_MEMBERS:
            raise LayoutError("polygon framing exceeds the 10,000 part limit")
    if project.framing.supports.locations is not None and sum(
        p.role == "support" for p in parts
    ) != len(project.framing.supports.locations):
        raise LayoutError("manual support locations must each belong to exactly one framing bay")
    _check_blocks(parts, project.framing.supports.base_width)
    connections: list[Connection] = []
    for i, a in enumerate(bounds):
        for j in range(i + 1, len(bounds)):
            seam = _seam(a, bounds[j], axis)
            if seam is None:
                continue
            start, end = seam
            members = []
            for index in (i, j):
                candidates = [
                    p for p in parts if p.role == "rim" and p.id.startswith(f"bay/{index:03d}/")
                ]
                coordinate = start.y if axis == "y" else start.x
                member = min(
                    candidates,
                    key=lambda p: min(
                        abs((v.y if axis == "y" else v.x) - coordinate) for v in p.geometry.vertices
                    ),
                )
                members.append(member.id)
            connections.append(
                Connection(f"connection/{i:03d}-{j:03d}", start, end, (members[0], members[1]))
            )
    return tuple(parts), tuple(connections)


def _seam(a: Rectangle, b: Rectangle, axis: str) -> tuple[Vec3, Vec3] | None:
    if axis == "y" and abs(a[3] - b[1]) <= TOLERANCE:
        lo, hi = max(a[0], b[0]), min(a[2], b[2])
        if hi > lo + TOLERANCE:
            return Vec3(lo, a[3], 0), Vec3(hi, a[3], 0)
    if axis == "x" and abs(a[2] - b[0]) <= TOLERANCE:
        lo, hi = max(a[1], b[1]), min(a[3], b[3])
        if hi > lo + TOLERANCE:
            return Vec3(a[2], lo, 0), Vec3(a[2], hi, 0)
    return None


def _check_blocks(parts: list[Part], width: float) -> None:
    cells: dict[tuple[int, int], list[tuple[float, float]]] = {}
    for part in parts:
        if part.role != "support":
            continue
        x = sum(v.x for v in part.geometry.vertices) / len(part.geometry.vertices)
        y = sum(v.y for v in part.geometry.vertices) / len(part.geometry.vertices)
        cell = int(x // width), int(y // width)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for a, b in cells.get((cell[0] + dx, cell[1] + dy), ()):
                    if abs(x - a) < width - TOLERANCE and abs(y - b) < width - TOLERANCE:
                        raise LayoutError(
                            "support blocks overlap across bays; increase edge_setback"
                        )
        cells.setdefault(cell, []).append((x, y))
