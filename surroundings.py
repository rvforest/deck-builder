import solid as s
from ezdxf.layouts import Modelspace
from solid import OpenSCADObject, utils as su

from layers import Layer
from paths import trace_rectangle
from point import Dim, Point3D, Point2D
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
        dxfattribs = {'layer': Layer.GROUND}
        if plane == Dim.Z:
            pass
        elif plane == Dim.X:
            msp.add_line(Ground.ground_points[0][1:], Ground.ground_points[2][1:], dxfattribs=dxfattribs)
            msp.add_line(Ground.ground_points[1][1:], Ground.ground_points[3][1:], dxfattribs=dxfattribs)
        elif plane == Dim.Y:
            start = Ground.ground_points[0]
            end = Ground.ground_points[1]
            msp.add_line((start[0], start[-1]), (end[0], end[-1]), dxfattribs=dxfattribs)

    def translate(self, x: float, y: float, z: float) -> Shape:
        print('Warning: Ground cannot be moved. No change was made.')
        return self


class House(Cuboid):

    BLUE = (0.5, 0.5, 1)
    WALL_X_START = -120
    WALL_DECK_GAP = 1
    HOUSE_WALL_LEN = 40 * 12
    HOUSE_HEIGHT = 240
    WALL_THICKNESS = 8
    WALL_Y_START = -WALL_DECK_GAP - WALL_THICKNESS

    THRESHOLD_HEIGHT = 8
    GROUND_HEIGHT_AT_DOOR = -3.0
    DOOR_WIDTH = 36
    DOOR_START = 19.5 * 12 - DOOR_WIDTH  # Reference from NW corner of deck
    DOOR_HEIGHT = 80

    WINDOW_WIDTH = 61.5
    WINDOW_HEIGHT = 32.5
    WINDOW_DIST_FROM_GROUND = 47.5 - GROUND_HEIGHT_AT_DOOR
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

    def render_dxf(self, plane: Dim, msp: Modelspace):
        dxfattrib = {}
        if self.layer:
            dxfattrib['layer'] = self.layer.value
        else:
            dxfattrib['layer'] = Layer.HOUSE.value
        if plane == Dim.Y:
            window = trace_rectangle(
                House.WINDOW_WIDTH,
                House.WINDOW_HEIGHT,
                Point2D(-House.WINDOW_X_START, House.WINDOW_Z_START),
                h_invert=True
            )
            msp.add_lwpolyline(window, dxfattribs=dxfattrib)

            door = trace_rectangle(
                House.DOOR_WIDTH,
                House.DOOR_HEIGHT,
                Point2D(-House.DOOR_START, House.THRESHOLD_HEIGHT),
                h_invert=True
            )
            msp.add_lwpolyline(door, dxfattribs=dxfattrib)
        elif plane == Dim.Z:
            super().render_dxf(plane, msp)
            # Add Door
            door_end = House.DOOR_START + House.DOOR_WIDTH
            door_lines = [
                (
                    Point2D(House.DOOR_START, House.WALL_Y_START),
                    Point2D(House.DOOR_START, House.WALL_Y_START + House.WALL_THICKNESS)
                ),
                (
                    Point2D(door_end, House.WALL_Y_START),
                    Point2D(door_end, House.WALL_Y_START + House.WALL_THICKNESS)
                ),
                # Door line
                (
                    Point2D(door_end, House.WALL_Y_START),
                    Point2D(door_end - 25.5, House.WALL_Y_START - 25.5)
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
                    Point2D(window_end, House.WALL_Y_START),
                    Point2D(window_end, House.WALL_Y_START + House.WALL_THICKNESS)
                ),
                # Mid point line
                (
                    Point2D(House.WINDOW_X_START, window_half_y),
                    Point2D(window_end, window_half_y)
                ),
            ]
            for line in window_lines:
                msp.add_lwpolyline(line, dxfattribs=dxfattrib)
