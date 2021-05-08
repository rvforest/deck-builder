from __future__ import annotations
from enum import Enum
from typing import Optional

from ezdxf.layouts import Modelspace
import solid as s
import solid.utils as su
from solid import OpenSCADObject

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
            draw_x: bool = True,
            color=None
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
        super().__init__(x, y, z, position, layer, color=color)

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
            layer=self.layer,
            color=self.color
        )


class MiteredBoard(Lumber):

    valid_miter_vals = ['up', 'down', None]

    def __init__(
            self,
            width: float,
            height: float,
            length: float,
            position: Point3D,
            layer: str = None,
            orient_towards: Dim = Dim.X,
            draw_x: bool = True,
            color=None,
            start_miter=None,
            end_miter=None
    ):
        self.start_miter = start_miter
        self.end_miter = end_miter
        super(MiteredBoard, self).__init__(width, height, length, position, layer, orient_towards, draw_x, color)

    def _get_path(self, plane: Dim):
        path = super()._get_path(plane)

        indices = {}
        if self.orient_towards == Dim.X:
            indices['start_up'] = 3
            indices['start_down'] = 0
            indices['end_up'] = 2
            indices['end_down'] = 1
            adj = Point2D(self.width, 0)
        elif self.orient_towards == Dim.Y:
            indices['start_up'] = 0
            indices['start_down'] = 1
            indices['end_up'] = 3
            indices['end_down'] = 2
            adj = Point2D(0, self.width)
        else:
            raise NotImplementedError("Orient towards Z not yet supported.")

        if plane == Dim.Z:
            if self.start_miter is not None:
                idx = indices['start_' + self.start_miter]
                path[idx] += adj
                if idx == 0:
                    path[4] += adj
            if self.end_miter is not None:
                idx = indices['end_' + self.end_miter]
                path[idx] -= adj
                if idx == 0:
                    path[4] -= adj

        return path

    def translate(self, x: float, y: float, z: float) -> Lumber:
        return MiteredBoard(
            self.width,
            self.height,
            self.length,
            position=self.position + Point3D(x, y, z),
            orient_towards=self.orient_towards,
            layer=self.layer,
            color=self.color,
            start_miter=self.start_miter,
            end_miter=self.end_miter
        )


class LumberFactory:
    def __init__(self, width: float, height: float, draw_x: bool = True, color=None):
        self.width = width
        self.height = height
        self.draw_x = draw_x
        self.color = color

    def __call__(
            self,
            length: float,
            position: Optional[Point3D] = None,
            layer: Optional[str] = None,
            orient_towards: Dim = Dim.X
    ) -> Lumber:
        return Lumber(
            self.width, self.height, length, position, layer, orient_towards, draw_x=self.draw_x, color=self.color
        )

    def copy(self):
        return LumberFactory(self.width, self.height, self.draw_x, self.color)


if __name__ == '__main__':
    import ezdxf
    from util import ft
    doc = ezdxf.new(dxfversion='AC1024')
    modelspace = doc.modelspace()

    TwoBySix = LumberFactory(LumberSize.TWO.value, LumberSize.SIX.value)
    boards = [
        # TwoBySix(ft(10), Point3D(0, 0, 0))
        MiteredBoard(3.5, 1.5, ft(3), Point3D(0, 0, 0), orient_towards=Dim.Y, end_miter='down')
    ]
    for b in boards:
        b.render_dxf(Dim.Z, modelspace)
    doc.saveas('foo.dxf')
