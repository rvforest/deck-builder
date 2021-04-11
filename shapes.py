from __future__ import annotations
from abc import abstractmethod
from typing import Optional, Protocol, List

from ezdxf.layouts import Modelspace
import solid as s
import solid.utils as su
from solid.solidpython import OpenSCADObject

from paths import trace_rectangle, trace_square, trace_isosceles_trapezoid
from point import Dim, Point3D


class Shape(Protocol):
    position: Optional[Point3D]
    layer: Optional[str]

    @abstractmethod
    def render_scad(self) -> OpenSCADObject:
        raise NotImplementedError

    @abstractmethod
    def render_dxf(self, plane: Dim, msp: Modelspace):
        raise NotImplementedError

    @abstractmethod
    def translate(self, x: float, y: float, z: float) -> Shape:
        raise NotImplementedError


class Cuboid(Shape):

    def __init__(self, x_len: float, y_len: float, z_len: float, position: Optional[Point3D] = None, layer: str = None):
        self.x_len = x_len
        self.y_len = y_len
        self.z_len = z_len
        self.lengths = (x_len, y_len, z_len)
        self.position = position if position is not None else Point3D(0, 0, 0)
        self.layer = layer

    def render_scad(self):
        return su.translate(tuple(self.position))(s.cube(self.lengths))

    def render_dxf(self, plane: Dim, msp: Modelspace):
        args = [self.lengths[d.value] for d in Dim if d != plane]
        path = trace_rectangle(args[0], args[1], self.position.get_2d_point(plane))

        dxfattrib = {}
        if self.layer:
            dxfattrib['layer'] = self.layer
        msp.add_lwpolyline(path, dxfattribs=dxfattrib)

    def translate(self, x: float, y: float, z: float) -> Cuboid:
        return Cuboid(self.x_len, self.y_len, self.z_len, position=self.position + Point3D(x, y, z), layer=self.layer)


class TrapezoidalPrism(Shape):

    def __init__(
            self,
            bottom_square_len: float,
            top_square_len: float,
            height: float,
            position: Optional[Point3D] = None,
            layer: str = None
    ):
        self.top_square_len = top_square_len
        self.bottom_square_len = bottom_square_len
        self.height = height
        self.position = position if position is not None else Point3D(0, 0, 0)
        self.layer = layer

    def render_dxf(self, plane: Dim, msp: Modelspace):

        if plane == Dim.Z:
            # Top is always parallel to ground
            path = trace_square(self.bottom_square_len, self.position.get_2d_point(plane))
        else:
            # Other two sides are identical
            path = trace_isosceles_trapezoid(
                self.bottom_square_len,
                self.top_square_len,
                self.height,
                self.position.get_2d_point(plane)
            )
        dxfattrib = {}
        if self.layer:
            dxfattrib['layer'] = self.layer
        msp.add_lwpolyline(path, dxfattribs=dxfattrib)

    def render_scad(self):
        scale = self.top_square_len / self.bottom_square_len
        # noinspection PyTypeChecker
        return su.translate(tuple(self.position))(
            su.linear_extrude(height=self.height, scale=scale)(
                s.square(self.bottom_square_len)
            )
        )

    def translate(self, x: float, y: float, z: float) -> TrapezoidalPrism:
        return TrapezoidalPrism(
            self.bottom_square_len,
            self.top_square_len,
            self.height,
            position=self.position + Point3D(x, y, z), layer=self.layer
        )


class ShapeCollection:

    def __init__(self, shapes: Optional[List[Shape]] = None):
        if shapes is None:
            self._shapes = []
        else:
            self._shapes = shapes

    def __len__(self):
        return len(self._shapes)

    def __getitem__(self, item):
        return self._shapes[item]

    def __contains__(self, item):
        return self._shapes.__contains__(item)

    def __add__(self, other: ShapeCollection) -> ShapeCollection:
        return ShapeCollection(self._shapes + other._shapes)

    def append(self, item: Shape):
        self._shapes.append(item)

    def translate(self, x: float, y: float, z: float) -> ShapeCollection:
        return ShapeCollection([shape.translate(x, y, z) for shape in self])

    def render_dxf(self, plane: Dim, msp: Modelspace):
        for shape in self:
            shape.render_dxf(plane, msp)

    def render_scad(self):
        return sum([shape.render_scad() for shape in self])


if __name__ == '__main__':
    pass
