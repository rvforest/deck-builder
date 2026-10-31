"""Overall deck dimensions, independent of physical part geometry."""

from ezdxf.document import Drawing

from deck_builder.assembly import DeckAssembly
from deck_builder.geometry import Vec3
from deck_builder.projection import View, project_point


def add_dimensions(document: Drawing, assembly: DeckAssembly, view: View) -> None:
    """Annotate the footprint extents or deck width and finished elevation.

    Args:
        document: DXF document to annotate.
        assembly: Assembly containing named plan boundaries and decking.
        view: The same view used to project the physical parts.

    Raises:
        ValueError: If the assembly lacks footprint boundaries or decking.
    """
    surfaces = [p for p in assembly.parts if p.role in ("decking", "border")]
    if not assembly.boundaries or not surfaces:
        raise ValueError("overall dimensions require footprint boundaries and decking")
    top = max(v.z for part in surfaces for v in part.geometry.vertices)
    points = [
        project_point(Vec3(v.x, v.y, z), view)
        for edge in assembly.boundaries
        for v in (edge.start, edge.end)
        for z in (v.z, top)
    ]
    x0, x1 = min(p[0] for p in points), max(p[0] for p in points)
    y0, y1 = min(p[1] for p in points), max(p[1] for p in points)
    offset = max(12, max(x1 - x0, y1 - y0) * 0.08)
    document.layers.add("dimensions")
    modelspace = document.modelspace()
    for base, a, b, angle in (
        (((x0 + x1) / 2, y0 - offset), (x0, y0), (x1, y0), 0),
        ((x1 + offset, (y0 + y1) / 2), (x1, y0), (x1, y1), 90),
    ):
        dimension = modelspace.add_linear_dim(
            base=base,
            p1=a,
            p2=b,
            angle=angle,
            dxfattribs={"layer": "dimensions"},
            override={
                "dimtxt": 2.5,
                "dimasz": 2.5,
                "dimexo": 1,
                "dimexe": 1,
                "dimdec": 2,
                "dimzin": 8,
                "dimpost": "<> in",
            },
        )
        dimension.render()
