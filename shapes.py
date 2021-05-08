from __future__ import annotations
from abc import abstractmethod
from typing import Optional, Protocol, List, Tuple

from ezdxf.layouts import Modelspace
import solid as s
import solid.utils as su
from solid.solidpython import OpenSCADObject

from layers import Layer
from paths import trace_rectangle, trace_square, trace_isosceles_trapezoid
from point import Dim, Point2D, Point3D


class Shape(Protocol):
    position: Optional[Point3D]
    layer: Optional[Layer]
    height: float
    color: Optional[Tuple[float, float, float]]

    @abstractmethod
    def _render_scad(self) -> OpenSCADObject:
        raise NotImplementedError

    def render_scad(self) -> OpenSCADObject:
        shape = self._render_scad()
        if self.color is not None:
            return s.color(self.color)(shape)
        else:
            return shape

    @abstractmethod
    def render_dxf(self, plane: Dim, msp: Modelspace):
        raise NotImplementedError

    @abstractmethod
    def translate(self, x: float, y: float, z: float) -> Shape:
        raise NotImplementedError


class Cuboid(Shape):

    def __init__(
            self,
            x_len: float,
            y_len: float,
            z_len: float,
            position: Optional[Point3D] = None,
            layer: Layer = None,
            color: Optional[Tuple[float, float, float]] = None
    ):
        self.x_len = x_len
        self.y_len = y_len
        self.z_len = z_len
        self.lengths = (x_len, y_len, z_len)
        self.position = position if position is not None else Point3D(0, 0, 0)
        self.layer = layer
        self.color = color

        self.height = self.z_len

    def _render_scad(self):
        return su.translate(tuple(self.position))(s.cube(self.lengths))

    def _get_path(self, plane: Dim):
        args = [self.lengths[d.value] for d in Dim if d != plane]
        position_2d = self.position.get_2d_point(plane)
        if plane == Dim.Y:
            position_2d = position_2d.h_invert()
            h_invert = True
        else:
            h_invert = False

        return trace_rectangle(args[0], args[1], position_2d, h_invert=h_invert)

    def render_dxf(self, plane: Dim, msp: Modelspace):
        path = self._get_path(plane)

        dxfattrib = {}
        if self.layer:
            dxfattrib['layer'] = self.layer.value
        msp.add_lwpolyline(path, dxfattribs=dxfattrib)

    def translate(self, x: float, y: float, z: float) -> Cuboid:
        return Cuboid(
            self.x_len, self.y_len, self.z_len,
            position=self.position + Point3D(x, y, z), layer=self.layer, color=self.color
        )


class TrapezoidalPrism(Shape):

    def __init__(
            self,
            bottom_square_len: float,
            top_square_len: float,
            height: float,
            center: bool = True,
            position: Optional[Point3D] = None,
            layer: Layer = None,
            color: Tuple[float, float, float] = None
    ):
        self.top_square_len = top_square_len
        self.bottom_square_len = bottom_square_len
        self.height = height
        self.center = center
        self.position = position if position is not None else Point3D(0, 0, 0)
        self.layer = layer
        self.color = color

    def render_dxf(self, plane: Dim, msp: Modelspace):

        dxfattrib = {}
        if self.layer:
            dxfattrib['layer'] = self.layer.value

        if plane == Dim.Z:
            # Draw top and bottom faces
            path1 = trace_square(self.bottom_square_len, self.position.get_2d_point(plane), self.center)
            path2 = trace_square(self.top_square_len, self.position.get_2d_point(plane), self.center)
            msp.add_lwpolyline(path1, dxfattribs=dxfattrib)
            msp.add_lwpolyline(path2, dxfattribs=dxfattrib)

            # Connect top and bottom faces with line at each corner
            corners = [(a, b) for a, b in zip(path1, path2)]
            for corner in corners:
                msp.add_lwpolyline(corner, dxfattribs=dxfattrib)
        else:
            # Other two sides are identical
            # Adjust so that height is not centered
            position_2d = self.position.get_2d_point(plane) + Point2D(0, self.height / 2)
            if plane == Dim.Y:
                position_2d = position_2d.h_invert()
                h_invert = True
            else:
                h_invert = False
            path = trace_isosceles_trapezoid(
                self.bottom_square_len,
                self.top_square_len,
                self.height,
                position_2d,
                self.center,
                h_invert
            )
            msp.add_lwpolyline(path, dxfattribs=dxfattrib)

    def _render_scad(self):
        scale = self.top_square_len / self.bottom_square_len
        # noinspection PyTypeChecker
        return su.translate(tuple(self.position))(
            su.linear_extrude(height=self.height, scale=scale)(
                s.square(self.bottom_square_len, center=self.center)
            )
        )

    def translate(self, x: float, y: float, z: float) -> TrapezoidalPrism:
        return TrapezoidalPrism(
            self.bottom_square_len,
            self.top_square_len,
            self.height,
            position=self.position + Point3D(x, y, z),
            layer=self.layer,
            color=self.color
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


class Drawable(Protocol):
    def shape(self) -> ShapeCollection:
        raise NotImplementedError
