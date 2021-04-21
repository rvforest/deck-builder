import solid as s
from ezdxf.layouts import Modelspace
from solid import OpenSCADObject, utils as su

from point import Dim, Point3D
from shapes import Shape, Cuboid


class Ground(Shape):

    ground_points = [
        [0, 0, 0],  # Ground at sliding door
        [20 * 12, 0, -3],  # Ground at kitchen door
        [0, 16 * 12, -3],  # Ground 16 ft out from sliding door
        [20 * 12, 16 * 12, -3.5],  # Ground 16 ft out from kitchen door
        [10 * 12, 8 * 12, -3.5]
    ]
    ground_faces = [
        [0, 1, 2],
        [1, 2, 3],
        [0, 1, 4],
        [1, 3, 4],
        [3, 2, 4],
        [2, 0, 4]
    ]

    def __init__(self, color=(0, .4, .1)):
        self.color = color

    def _render_scad(self) -> OpenSCADObject:
        # noinspection PyTypeChecker
        return s.polyhedron(Ground.ground_points, Ground.ground_faces)

    def render_dxf(self, plane: Dim, msp: Modelspace):
        if plane == Dim.Z:
            pass
        elif plane == Dim.X:
            msp.add_line(Ground.ground_points[0][1:], Ground.ground_points[2][1:])
            msp.add_line(Ground.ground_points[1][1:], Ground.ground_points[3][1:])
        elif plane == Dim.Y:
            start = Ground.ground_points[0]
            end = Ground.ground_points[1]
            msp.add_line((start[0], start[-1]), (end[0], end[-1]))

    def translate(self, x: float, y: float, z: float) -> Shape:
        print('Warning: Ground cannot be moved. No change was made.')
        return self


class House(Cuboid):

    BLUE = (0.5, 0.5, 1)
    WALL_START = -120
    WALL_DECK_GAP = 1
    HOUSE_WALL_LEN = 40 * 12
    HOUSE_HEIGHT = 240
    WALL_THICKNESS = 12
    THRESHOLD_HEIGHT = 8
    GROUND_HEIGHT_AT_DOOR = -3.0
    DOOR_WIDTH = 36
    DOOR_START = 19.5 * 12 - DOOR_WIDTH  # Reference from NW corner of deck
    DOOR_HEIGHT = 80

    def __init__(self):
        super().__init__(
            self.HOUSE_WALL_LEN, self.WALL_THICKNESS, self.HOUSE_HEIGHT,
            Point3D(self.WALL_START, -self.WALL_THICKNESS, -3)
        )

    def _render_scad(self) -> OpenSCADObject:
        house = super()._render_scad()
        house = s.color(self.BLUE)(house)
        # Add door
        house = su.difference()(
            house,
            s.translate((
                self.DOOR_START,
                -2 * self.WALL_THICKNESS,
                self.THRESHOLD_HEIGHT + self.GROUND_HEIGHT_AT_DOOR
            ))(s.cube([self.DOOR_WIDTH, 3 * self.WALL_THICKNESS, self.DOOR_HEIGHT]))
        )
        return house

    def render_dxf(self, plane: Dim, msp: Modelspace):
        if plane == Dim.Y:
            pass
        else:
            super().render_dxf(plane, msp)