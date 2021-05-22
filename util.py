import math
from abc import abstractmethod
from typing import Protocol, Callable

import ezdxf
from ezdxf.layouts import Modelspace
import ezdxf.zoom
import solid as s

from layers import Layer
from point import Point3D
from shapes import Dim, Shape, ShapeCollection


def ft(f):
    return 12 * f


class DXFWritable(Protocol):

    @abstractmethod
    def render_dxf(self, plane: Dim, msp: Modelspace):
        raise NotImplementedError


def write_dxf_doc(obj: DXFWritable, plane: Dim, filename: str):
    doc = ezdxf.new()
    doc.header['$INSUNITS'] = 1  # Doc in inches
    for layer in Layer:
        doc.layers.new(name=layer.value)
    modelspace = doc.modelspace()
    obj.render_dxf(plane, modelspace)
    doc.saveas(filename)


def n_members(length, lumber_width, max_span):
    width_minus_last = length - lumber_width
    return math.ceil(width_minus_last / max_span) + 1


def oc_spacing(frame_width, lumber_width, n):
    return (frame_width - lumber_width) / (n - 1)


def even_spacing(
        shape: Callable[[], Shape],
        initial_pos: Point3D,
        offset: Point3D,
        n: int,
) -> ShapeCollection:
    f = ShapeCollection()
    for i in range(0, n):
        new_position = initial_pos + i * offset
        f.append(shape().translate(*new_position))
    return f


def render_all(obj, name):
    s.scad_render_to_file(obj.render_scad(), f'{name}.scad')
    write_dxf_doc(obj, Dim.Z, f'{name}_top.dxf')
    write_dxf_doc(obj, Dim.Y, f'{name}_front.dxf')
    write_dxf_doc(obj, Dim.X, f'{name}_side.dxf')
