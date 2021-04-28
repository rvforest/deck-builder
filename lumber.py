from __future__ import annotations
from enum import Enum
from typing import Optional

from ezdxf.layouts import Modelspace

from shapes import Cuboid, Dim
from point import Point2D, Point3D


class LumberSize(Enum):
    ONE = 0.75
    TWO = 1.5
    FOUR = 3.5
    SIX = 5.5
    EIGHT = 7.25
    TEN = 9.25
    TWELVE = 11.25


class Lumber(Cuboid):

    def __init__(
            self,
            width: float,
            height: float,
            length: float,
            position: Point3D,
            layer: str = None,
            orient_towards: Dim = Dim.X,
            draw_x: bool = True
    ):
        self.width = width
        self.height = height
        self.length = length
        self.draw_x = draw_x

        self.orient_towards = orient_towards
        x, y, z = length, width, height
        if orient_towards == Dim.Y:
            x, y = y, x
        elif orient_towards == Dim.Z:
            x, z = z, x
        super().__init__(x, y, z, position, layer)

    def render_dxf(self, plane: Dim, msp: Modelspace, layer: str = None):
        # First draw Cuboid outline
        super().render_dxf(plane, msp)

        # Next draw X if lumber goes into page
        if plane == self.orient_towards:
            position_2d = self.position.get_2d_point(plane)
            if plane == Dim.Y:
                position_2d = position_2d.h_invert()
                if self.draw_x:
                    msp.add_line(position_2d, position_2d + Point2D(self.width, self.height).h_invert())
                    msp.add_line(position_2d + Point2D(0, self.height).h_invert(),
                                 position_2d + Point2D(self.width, 0).h_invert())
            else:
                if self.draw_x:
                    msp.add_line(position_2d, position_2d + Point2D(self.width, self.height))
                    msp.add_line(position_2d + Point2D(0, self.height), position_2d + Point2D(self.width, 0))

    def translate(self, x: float, y: float, z: float) -> Lumber:
        return Lumber(
            self.width,
            self.height,
            self.length,
            position=self.position + Point3D(x, y, z),
            orient_towards=self.orient_towards,
            layer=self.layer
        )


class LumberFactory:
    def __init__(self, width: float, height: float, draw_x: bool = True):
        self.width = width
        self.height = height
        self.draw_x = draw_x

    def __call__(
            self,
            length: float,
            position: Optional[Point3D] = None,
            layer: Optional[str] = None,
            orient_towards: Dim = Dim.X
    ) -> Lumber:
        return Lumber(self.width, self.height, length, position, layer, orient_towards, draw_x=self.draw_x)


if __name__ == '__main__':
    import ezdxf
    from util import ft
    doc = ezdxf.new(dxfversion='AC1024')
    modelspace = doc.modelspace()

    TwoBySix = LumberFactory(LumberSize.TWO.value, LumberSize.SIX.value)
    boards = [
        TwoBySix(ft(10), Point3D(0, 0, 0))
    ]
    for board in boards:
        board.render_dxf(Dim.X, modelspace)
    doc.saveas('foo.dxf')
