from __future__ import annotations
from abc import abstractmethod
from typing import Optional, Protocol

from ezdxf.layouts import Modelspace
import solid as s
import solid.utils as su
from solid.solidpython import OpenSCADObject

from paths import trace_rectangle, trace_square, trace_isosceles_trapezoid
from point import Dim, Point3D


class Shape(Protocol):
    position: Point3D
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

    def __init__(self, x_len: float, y_len: float, z_len: float, position: Point3D, layer: str = None):
        self.x_len = x_len
        self.y_len = y_len
        self.z_len = z_len
        self.lengths = (x_len, y_len, z_len)
        self.position = position
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
            position: Point3D,
            layer: str = None
    ):
        self.top_square_len = top_square_len
        self.bottom_square_len = bottom_square_len
        self.height = height
        self.position = position
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


if __name__ == '__main__':
    pass
