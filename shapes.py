from abc import abstractmethod
from typing import Protocol

from ezdxf.layouts import Modelspace
import solid as s
import solid.utils as su
from solid.solidpython import OpenSCADObject

from paths import trace_rectangle, trace_square, trace_isosceles_trapezoid
from point import Dim, Point3D


class Shape(Protocol):
    position: Point3D

    @abstractmethod
    def render_scad(self) -> OpenSCADObject:
        raise NotImplementedError

    @abstractmethod
    def render_dxf(self, plane: Dim, msp: Modelspace, layer: str = None):
        raise NotImplementedError


class Cuboid(Shape):

    def __init__(self, x_len: float, y_len: float, z_len: float, position: Point3D):
        self.x_len = x_len
        self.y_len = y_len
        self.z_len = z_len
        self.lengths = (x_len, y_len, z_len)
        self.position = position

    def render_scad(self):
        return su.translate(tuple(self.position))(s.cube(self.lengths))

    def render_dxf(self, plane: Dim, msp: Modelspace, layer: str = None):
        args = [self.lengths[d.value] for d in Dim if d != plane]
        path = trace_rectangle(args[0], args[1], self.position.get_2d_point(plane))

        dxfattrib = {}
        if layer:
            dxfattrib['layer'] = layer
        msp.add_lwpolyline(path)


class TrapezoidalPrism(Shape):

    def __init__(self, bottom_square_len: float, top_square_len: float, height: float, position: Point3D):
        self.top_square_len = top_square_len
        self.bottom_square_len = bottom_square_len
        self.height = height
        self.position = position

    def render_dxf(self, plane: Dim, msp: Modelspace, layer: str = None):

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
        if layer:
            dxfattrib['layer'] = layer
        msp.add_lwpolyline(path)

    def render_scad(self):
        scale = self.top_square_len / self.bottom_square_len
        # noinspection PyTypeChecker
        su.translate(tuple(self.position))(
            su.linear_extrude(height=self.height, scale=scale)(
                s.square(self.bottom_square_len)
            )
        )


if __name__ == '__main__':
    pass
