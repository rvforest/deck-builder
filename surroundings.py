import math

import solid as s
from ezdxf.layouts import Modelspace
from solid import OpenSCADObject, utils as su

from colors import BLUE, GREEN
from layers import Layer
from paths import trace_rectangle
from point import Dim, Point3D, Point2D
from shapes import Shape, Cuboid
from util import ft


class Ground(Shape):

    ground_points = [
        [0, 0, 0],  # Ground at sliding door
        [ft(19.25), 0, -2],  # Ground at kitchen door
        [0, ft(16), -2],  # Ground 16 ft out from sliding door
        [ft(19.25), ft(16), -2.5],  # Ground 16 ft out from kitchen door
        [ft(10), ft(8), -2.5]
    ]
    ground_faces = [
        [0, 1, 2],
        [1, 2, 3],
        [0, 1, 4],
        [1, 3, 4],
        [3, 2, 4],
        [2, 0, 4]
    ]

    def __init__(self, color=GREEN):
        self.color = color
        self.rotate = None

    def _render_scad(self) -> OpenSCADObject:
        # noinspection PyTypeChecker
        return s.polyhedron(Ground.ground_points, Ground.ground_faces)

    def render_dxf(self, plane: Dim, msp: Modelspace, invert=False):
        if plane == Dim.Z:
            return

        if plane == Dim.X:
            start1 = Ground.ground_points[0][1:]
            end1 = Ground.ground_points[2][1:]
            start2 = Ground.ground_points[1][1:]
            end2 = Ground.ground_points[3][1:]
        elif plane == Dim.Y:
            start = Ground.ground_points[0]
            end = Ground.ground_points[1]
            start1 = (start[0], start[-1])
            end1 = (end[0], end[-1])
            start = Ground.ground_points[2]
            end = Ground.ground_points[3]
            start2 = (start[0], start[-1])
            end2 = (end[0], end[-1])
        else:
            raise ValueError("Invalid value for `plane`")

        if invert:
            end1 = (-end1[0], end1[1])
            end2 = (-end2[0], end2[1])

        msp.add_line(
            start1, end1, dxfattribs={'layer': Layer.GROUND1.value}
        )
        msp.add_line(
            start2, end2, dxfattribs={'layer': Layer.GROUND2.value}
        )

    def translate(self, x: float, y: float, z: float) -> Shape:
        print('Warning: Ground cannot be moved. No change was made.')
        return self


class House(Cuboid):

    WALL_X_START = -ft(3.5)
    WALL_DECK_GAP = 1
    HOUSE_WALL_LEN = ft(25)
    HOUSE_HEIGHT = 240
    WALL_THICKNESS = 6
    WALL_Y_START = -WALL_DECK_GAP - WALL_THICKNESS

    THRESHOLD_HEIGHT = 8
    GROUND_HEIGHT_AT_DOOR = -3.0
    DOOR_WIDTH = 36
    DOOR_START = 19.5 * 12 - DOOR_WIDTH  # Reference from NW corner of deck
    DOOR_HEIGHT = 80

    WINDOW_WIDTH = 61.5
    WINDOW_HEIGHT = 32.5
    WINDOW_DIST_FROM_GROUND = 47.5
    WINDOW_DIST_FROM_DOOR = 26.5
    WINDOW_X_START = DOOR_START - WINDOW_DIST_FROM_DOOR - WINDOW_WIDTH
    WINDOW_Z_START = WINDOW_DIST_FROM_GROUND + GROUND_HEIGHT_AT_DOOR + THRESHOLD_HEIGHT

    def __init__(self):
        super().__init__(
            self.HOUSE_WALL_LEN, self.WALL_THICKNESS, self.HOUSE_HEIGHT,
            Point3D(self.WALL_X_START, self.WALL_Y_START, -3), layer=Layer.HOUSE
        )

    def _render_scad(self) -> OpenSCADObject:
        house = super()._render_scad()
        house = s.color(BLUE)(house)
        # Add door
        house = su.difference()(
            house,
            s.translate((
                self.DOOR_START,
                -2 * self.WALL_THICKNESS,
                self.THRESHOLD_HEIGHT + self.GROUND_HEIGHT_AT_DOOR
            ))(s.cube([self.DOOR_WIDTH, 3 * self.WALL_THICKNESS, self.DOOR_HEIGHT]))
        )

        # Add window
        house = su.difference()(
            house,
            s.translate((
                House.WINDOW_X_START,
                -2.0 * House.WALL_THICKNESS,
                House.WINDOW_Z_START
            ))(s.cube([House.WINDOW_WIDTH, 3 * House.WALL_THICKNESS, House.WINDOW_HEIGHT]))
        )
        return house

    def render_dxf(self, plane: Dim, msp: Modelspace, invert: bool = False):
        dxfattrib = {}
        if self.layer:
            dxfattrib['layer'] = self.layer.value
        else:
            dxfattrib['layer'] = Layer.HOUSE.value

        inv = -1 if invert else 1
        if plane == Dim.Y:
            window = trace_rectangle(
                House.WINDOW_WIDTH,
                House.WINDOW_HEIGHT,
                Point2D(inv * House.WINDOW_X_START, House.WINDOW_Z_START),
                h_invert=True
            )
            msp.add_lwpolyline(window, dxfattribs=dxfattrib)

            door = trace_rectangle(
                House.DOOR_WIDTH,
                House.DOOR_HEIGHT,
                Point2D(inv * House.DOOR_START, House.THRESHOLD_HEIGHT + House.GROUND_HEIGHT_AT_DOOR),
                h_invert=True
            )
            msp.add_lwpolyline(door, dxfattribs=dxfattrib)
        elif plane == Dim.Z:
            for i in range(2):
                msp.add_line(
                    (self.WALL_X_START, self.WALL_Y_START + i * self.WALL_THICKNESS),
                    (inv * self.WINDOW_X_START, self.WALL_Y_START + i * self.WALL_THICKNESS)
                )
                msp.add_line(
                    (self.WINDOW_X_START + self.WINDOW_WIDTH, self.WALL_Y_START + i * self.WALL_THICKNESS),
                    (inv * self.DOOR_START, self.WALL_Y_START + i * self.WALL_THICKNESS)
                )
                msp.add_line(
                    (self.DOOR_START + self.DOOR_WIDTH, self.WALL_Y_START + i * self.WALL_THICKNESS),
                    (inv * (self.WALL_X_START + self.HOUSE_WALL_LEN), self.WALL_Y_START + i * self.WALL_THICKNESS)
                )
            # Add Door
            door_end = House.DOOR_START + House.DOOR_WIDTH
            door_lines = [
                (
                    Point2D(House.DOOR_START, House.WALL_Y_START),
                    Point2D(House.DOOR_START, House.WALL_Y_START + House.WALL_THICKNESS)
                ),
                (
                    Point2D(inv * door_end, House.WALL_Y_START),
                    Point2D(inv * door_end, House.WALL_Y_START + House.WALL_THICKNESS)
                ),
                # Door line
                (
                    Point2D(inv * door_end, House.WALL_Y_START),
                    Point2D(
                        inv * (door_end - self.DOOR_WIDTH * math.cos(math.radians(20))),
                        House.WALL_Y_START - self.DOOR_WIDTH * math.sin(math.radians(20))
                    )
                ),
            ]
            for line in door_lines:
                msp.add_lwpolyline(line, dxfattribs=dxfattrib)

            # Add window
            window_end = House.WINDOW_X_START + House.WINDOW_WIDTH
            window_half_y = House.WALL_Y_START + House.WALL_THICKNESS / 2
            window_lines = [
                (
                    Point2D(House.WINDOW_X_START, House.WALL_Y_START),
                    Point2D(House.WINDOW_X_START, House.WALL_Y_START + House.WALL_THICKNESS)
                ),
                (
                    Point2D(inv * window_end, House.WALL_Y_START),
                    Point2D(inv * window_end, House.WALL_Y_START + House.WALL_THICKNESS)
                ),
                # Mid point line
                (
                    Point2D(House.WINDOW_X_START, window_half_y),
                    Point2D(inv * window_end, window_half_y)
                ),
            ]
            for line in window_lines:
                msp.add_lwpolyline(line, dxfattribs=dxfattrib)
