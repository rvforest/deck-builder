from abc import abstractmethod
from typing import List, Protocol

from paths import trace_rectangle, trace_square, trace_isosceles_trapezoid
from point import Dim, Point3D, Point2D


class Shape(Protocol):
    position: Point3D

    @abstractmethod
    def get_2d_path(self, face: Dim) -> List[Point2D]:
        raise NotImplementedError



class Cuboid(Shape):

    def __init__(self, x_len: float, y_len: float, z_len: float, position: Point3D):
        self.x_len = x_len
        self.y_len = y_len
        self.z_len = z_len
        self.lengths = (x_len, y_len, z_len)
        self.position = position

    def get_2d_path(self, plane: Dim) -> List[Point2D]:
        args = [self.lengths[d.value] for d in Dim if d != plane]
        return trace_rectangle(args[0], args[1], self.position.get_2d_point(plane))


class TrapezoidalPrism(Shape):

    def __init__(self, bottom_square_len: float, top_square_len: float, height: float, position: Point3D):
        self.top_square_len = top_square_len
        self.bottom_square_len = bottom_square_len
        self.height = height
        self.position = position

    def get_2d_path(self, plane: Dim) -> List[Point2D]:
        if plane == Dim.Z:
            # Top is always parallel to ground
            return trace_square(self.bottom_square_len, self.position.get_2d_point(plane))
        else:
            # Other two sides are identical
            return trace_isosceles_trapezoid(
                self.bottom_square_len,
                self.top_square_len,
                self.height,
                self.position.get_2d_point(plane)
            )


if __name__ == '__main__':
    pass
