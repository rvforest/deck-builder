from enum import Enum
from typing import Type, Optional

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
            orient_towards: Dim = Dim.X
    ):
        self.width = width
        self.height = height
        self.length = length

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
        position_2d = self.position.get_2d_point(plane)
        if plane == self.orient_towards:
            msp.add_line(position_2d, position_2d + Point2D(self.width, self.height))
            msp.add_line(position_2d + Point2D(0, self.height), position_2d + Point2D(self.width, 0))


class PredefinedLumber(Lumber):
    width: float
    height: float

    def __init__(
            self,
            length: float,
            position: Optional[Point3D] = None,
            layer: Optional[str] = None,
            orient_towards: Dim = Dim.X
    ):
        raise NotImplementedError


def lumber_factory(name: str, width: float, height: float) -> Type[Lumber]:
    def __init__(self, length: float, position: Optional[Point3D] = None, layer: Optional[str] = None, orient_towards: Dim = Dim.X):
        Lumber.__init__(self, width, height, length, position, layer, orient_towards)
    newclass = type(name, (PredefinedLumber,), {'__init__': __init__})
    return newclass


if __name__ == '__main__':
    import ezdxf
    from util import ft
    doc = ezdxf.new(dxfversion='AC1024')
    modelspace = doc.modelspace()

    TwoBySix = lumber_factory("TwoBySix", LumberSize.TWO.value, LumberSize.SIX.value)
    boards = [
        TwoBySix(ft(10), Point3D(0, 0, 0))
    ]
    for board in boards:
        board.render_dxf(Dim.X, modelspace)
    doc.saveas('foo.dxf')
