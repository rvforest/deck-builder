"""Layered orthographic DXF drawings from shared world-space geometry."""

import ezdxf
from ezdxf import units
from ezdxf.document import Drawing

from deck_builder.assembly import DeckAssembly
from deck_builder.projection import View, silhouette


def render_dxf(assembly: DeckAssembly, view: View) -> Drawing:
    """Build a DXF drawing containing one closed silhouette per part.

    Args:
        assembly: Resolved parts with world-space geometry.
        view: Orthographic view to draw.

    Returns:
        An in-memory DXF document with inch units and layers named by part role.
        Hidden parts remain visible; hidden-line removal is not performed.
    """
    document = ezdxf.new("R2010")
    document.units = units.IN
    document.appids.add("DECK_BUILDER")
    for role in sorted({part.role for part in assembly.parts}):
        document.layers.add(role)
    modelspace = document.modelspace()
    for part in assembly.parts:
        entity = modelspace.add_lwpolyline(
            silhouette(part.geometry, view),
            close=True,
            dxfattribs={"layer": part.role},
        )
        entity.set_xdata("DECK_BUILDER", [(1000, part.id)])
    return document
