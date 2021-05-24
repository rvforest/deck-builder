from __future__ import annotations
from enum import Enum
from typing import Optional

from ezdxf.layouts import Modelspace
import solid as s
import solid.utils as su
from solid import OpenSCADObject

from layers import Layer
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
            layer: Layer = None,
            orient_towards: Dim = Dim.X,
            draw_x: bool = True,
            color=None,
            rotate=None
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

        if layer is None:
            layer = Layer.FRAME

        super().__init__(x, y, z, position, layer, color=color, rotate=rotate)

    def render_dxf(self, plane: Dim, msp: Modelspace, layer: str = None, invert: bool = False):
        # First draw Cuboid outline
        super().render_dxf(plane, msp, invert)

        # Next draw X if lumber goes into page
        dxfattribs = {'layer': self.layer.value}
        if plane == self.orient_towards:
            position_2d = self.position.get_2d_point(plane)
            if invert:
                position_2d = position_2d.h_invert()
                if self.draw_x:
                    msp.add_line(
                        position_2d,
                        position_2d + Point2D(self.width, self.height).h_invert(),
                        dxfattribs=dxfattribs
                    )
                    msp.add_line(
                        position_2d + Point2D(0, self.height).h_invert(),
                        position_2d + Point2D(self.width, 0).h_invert(),
                        dxfattribs=dxfattribs
                    )
            else:
                if self.draw_x:
                    msp.add_line(
                        position_2d,
                        position_2d + Point2D(self.width, self.height),
                        dxfattribs=dxfattribs
                    )
                    msp.add_line(
                        position_2d + Point2D(0, self.height),
                        position_2d + Point2D(self.width, 0),
                        dxfattribs=dxfattribs
                    )

    def translate(self, x: float, y: float, z: float) -> Lumber:
        return Lumber(
            self.width,
            self.height,
            self.length,
            position=self.position + Point3D(x, y, z),
            orient_towards=self.orient_towards,
            layer=self.layer,
            color=self.color,
            rotate=self.rotate
        )


class MiteredBoard(Lumber):

    valid_miter_vals = ['up', 'down', None]

    def __init__(
            self,
            width: float,
            height: float,
            length: float,
            position: Point3D,
            layer: Layer = None,
            orient_towards: Dim = Dim.X,
            draw_x: bool = False,
            color=None,
            start_miter=None,
            end_miter=None,
            rotate=None
    ):
        self.start_miter = start_miter
        self.end_miter = end_miter
        if layer is None:
            layer = Layer.DECKING
        super(MiteredBoard, self).__init__(
            width, height, length, position, layer, orient_towards, draw_x, color, rotate
        )

    def _get_path(self, plane: Dim, invert: bool = False):
        path = super()._get_path(plane, invert)

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

    def _render_scad(self) -> OpenSCADObject:
        return su.translate(tuple(self.position))(
            s.linear_extrude(self.height)(
                s.polygon([p - self.position.get_2d_point(Dim.Z) for p in self._get_path(Dim.Z)])
            )
        )

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
            end_miter=self.end_miter,
            rotate=self.rotate
        )


class DeckingBoard(Lumber):

    def __init__(
            self,
            w2w_gap: float,
            e2e_gap: float,
            width: float,
            height: float,
            length: float,
            position: Point3D,
            layer: str = None,
            orient_towards: Dim = Dim.X,
            draw_x: bool = True,
            color=None,
            rotate=None
    ):
        self.w2w_gap = w2w_gap
        self.e2e_gap = e2e_gap

        if layer is None:
            layer = Layer.DECKING

        super().__init__(width, height, length, position, layer, orient_towards, draw_x, color, rotate)

    def _get_path(self, plane: Dim, invert: bool = False):
        """Don't draw decking gaps in DXF file"""
        path = super()._get_path(plane, invert)

        # Hide gaps in top down view
        if plane == Dim.Z:
            # Assume decking is always oriented in X direction
            far_edge_idxs = (2, 3)
            for idx in far_edge_idxs:
                path[idx] += Point2D(0, self.w2w_gap)

        return path

    def translate(self, x: float, y: float, z: float) -> DeckingBoard:
        return DeckingBoard(
            self.w2w_gap,
            self.e2e_gap,
            self.width,
            self.height,
            self.length,
            position=self.position + Point3D(x, y, z),
            orient_towards=self.orient_towards,
            layer=self.layer,
            color=self.color,
            draw_x=self.draw_x,
            rotate=self.rotate
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
            layer: Optional[Layer] = None,
            orient_towards: Dim = Dim.X,
            rotate: Optional[float] = None
    ) -> Lumber:
        return Lumber(
            self.width, self.height, length, position, layer, orient_towards,
            draw_x=self.draw_x, color=self.color, rotate=rotate
        )

    def copy(self):
        return type(self)(self.width, self.height, self.draw_x, self.color)


class DeckingFactory(LumberFactory):

    def __init__(self, width: float, height: float, draw_x: bool = False, color=None):
        self._w2w_gap = None
        self._e2e_gap = None
        super().__init__(width, height, draw_x, color)

    @property
    def w2w_gap(self):
        if self._w2w_gap is not None:
            return self._w2w_gap
        else:
            raise AttributeError("DeckingFactory.w2w_gap must be set by user before accessing.")

    @w2w_gap.setter
    def w2w_gap(self, val):
        self._w2w_gap = val

    @property
    def e2e_gap(self):
        if self._e2e_gap is not None:
            return self._e2e_gap
        else:
            raise AttributeError("DeckingFactory.e2e_gap must be set by user before accessing.")

    @e2e_gap.setter
    def e2e_gap(self, val):
        self._e2e_gap = val

    def __call__(
            self,
            length: float,
            position: Optional[Point3D] = None,
            layer: Optional[Layer] = None,
            orient_towards: Dim = Dim.X,
            rotate: Optional[float] = None
    ) -> DeckingBoard:
        return DeckingBoard(
            self.w2w_gap, self.e2e_gap, self.width, self.height,
            length, position, layer, orient_towards, draw_x=self.draw_x, color=self.color, rotate=rotate
        )


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
