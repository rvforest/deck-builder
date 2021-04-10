from typing import Iterable

import ezdxf
from ezdxf.layouts import Modelspace

from shapes import Shape, Dim


def draw_face(shapes: Iterable[Shape], face: Dim, msp: Modelspace, layer=None):
    dxfattrib = {}
    if layer:
        dxfattrib['layer'] = layer
    for shape in shapes:
        msp.add_lwpolyline(shape.get_2d_path(face))


if __name__ == '__main__':
    from shapes import Cuboid, Point

    doc = ezdxf.new(dxfversion='AC1024')
    modelspace = doc.modelspace()
    s = [Cuboid(2, 6, 120, Point3D(1, 2, 0)), Cuboid(120, 2, 3, Point3D(0, 0, 0))]
    draw_face(
        s,
        Dim.Z,
        modelspace
    )
    doc.saveas('foo.dxf')
