import math

import solid as s
import solid.utils as su

from util import ft

ONE = 0.75
TWO = 1.5
FOUR = 3.5
SIX = 5.5
EIGHT = 7.25
TEN = 9.25
TWELVE = 11.25


# southern pine
joist_spans = {
    SIX: ft(6) + 8,
    EIGHT: ft(10) + 1,
    TEN: ft(14),
    TWELVE: ft(16) + 6
}


def lumber(h, w, orient_towards='x'):
    """
    Lumber factory function
    :param orient_towards:
    :param h:
    :param w:

    """
    if orient_towards not in ('x', 'y', 'z'):
        raise ValueError("Invalid argument `orient_towards`. Value must be one of 'x', 'y', or 'z'")

    def inner(length):
        x, y, z = length, h, w
        if orient_towards == 'y':
            x, y = y, x
        elif orient_towards == 'z':
            x, z = z, x
        return s.cube([x, y, z])

    return inner


def n_members(length, lumber_width, max_span):
    width_minus_last = length - lumber_width
    return math.ceil(width_minus_last / max_span) + 1


def oc_spacing(frame_width, lumber_width, n):
    return (frame_width - lumber_width) / (n - 1)


class Deck:

    def __init__(
            self,
            width,
            length,
            height,
            joist_thickness=SIX,
            joist_width=TWO,
            max_spacing=16,
            joist_overhang=ft(2),
            beam_thickness=EIGHT,
            beam_width=FOUR,
            beam_overhang=ft(2),
            decking_thickness=ONE
    ):
        self.width = width
        self.length = length
        self.height = height
        self.joist_thickness = joist_thickness
        self.joist_width = joist_width
        self.max_spacing = max_spacing
        self.joist_overhang = joist_overhang
        self.beam_thickness = beam_thickness
        self.beam_width = beam_width
        self.beam_overhang = beam_overhang
        self.decking_thickness = decking_thickness

    @property
    def n_joist_spans(self):
        return 1

    @property
    def joist_len(self):
        return self.length

    @property
    def row_offset(self):
        return 0

    @property
    def n_joists(self):
        return n_members(self.width, lumber_width=TWO, max_span=self.max_spacing)

    @property
    def n_beams(self):
        return n_members(self.inner_length, self.beam_width, max_span=joist_spans[self.joist_thickness])

    @property
    def inner_length(self):
        return self.length - 2 * self.joist_overhang

    @property
    def joist_spacing(self):
        """Amount of space between joists."""
        return oc_spacing(self.width, self.joist_width, self.n_joists)

    @property
    def beam_spacing(self):
        """Amount of space between joists."""
        return oc_spacing(self.inner_length, self.beam_width, self.n_beams)

    @property
    def frame_height(self):
        return self.height - self.decking_thickness

    @property
    def beam_height(self):
        return self.frame_height - self.joist_thickness

    @property
    def post_height(self):
        return self.beam_height - self.beam_thickness

    def footings(self):
        raise NotImplementedError

    def frame(self):
        rim_joist = lumber(self.joist_width, self.joist_thickness)
        joist = lumber(self.joist_width, self.joist_thickness, orient_towards='y')
        f = rim_joist(self.width)
        row_position = self.row_offset
        for i in range(self.n_joist_spans):
            for j in range(0, self.n_joists):
                f += su.forward(row_position)(su.right(j * self.joist_spacing)(joist(self.joist_len)))
            row_position += self.joist_len + self.joist_width
            f += su.forward(row_position - self.joist_width)(rim_joist(self.width))

        return su.up(self.beam_height)(f)

    def planking(self):
        plank = s.cube([20 * 12, 5.5, .75])
        return su.up(self.frame_height)(plank)


class FlushBeamDeck(Deck):

    @property
    def n_joist_spans(self):
        return self.n_beams - 1

    @property
    def joist_len(self):
        return self.length / (self.n_beams - 1)

    @property
    def row_offset(self):
        return self.beam_width


class DeckJoistsOnBlocks(Deck):

    def footings(self):
        b = []
        for i in range(self.n_beams):
            for j in range(1, self.n_joists - 1):
                b.append(
                    su.forward(i * self.beam_spacing + self.beam_overhang)(
                        su.right(j * self.joist_spacing + TWO / 2)(deck_block)
                    )
                )
        return su.up(self.beam_height - BLOCK_SLOT_HEIGHT)(sum(b))

    def all(self):
        return self.frame() + self.footings() + self.planking()


BLOCK_HEIGHT = 7.75
BLOCK_SLOT_HEIGHT = 6
BLOCK_BASE_LEN = 10.75
BLOCK_TOP_LEN = 8
deck_block = su.linear_extrude(height=BLOCK_HEIGHT, scale=BLOCK_TOP_LEN/BLOCK_BASE_LEN)(s.square(10.75, center=True)) \
             - su.up(BLOCK_SLOT_HEIGHT + FOUR / 2)(s.cube([12, TWO, FOUR], center=True)) \
             - su.up(BLOCK_SLOT_HEIGHT + FOUR / 2)(s.cube([TWO, 12, FOUR], center=True)) \
             - su.up(BLOCK_SLOT_HEIGHT + 1)(s.cube([FOUR, FOUR, 2], center=True))


ground_points = [
    [0, 0, 0],
    [20 * 12, 0, -3],
    [0, 16 * 12, -3],
    [20 * 12, 16 * 12, -3.5],
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
ground = s.polyhedron(ground_points, ground_faces)

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
house = s.translate((WALL_START, -WALL_DECK_GAP - WALL_THICKNESS, -3))(
        s.color(BLUE)(s.cube([HOUSE_WALL_LEN, WALL_THICKNESS, HOUSE_HEIGHT])),
)
# Add door
house = su.difference()(
    house,
    s.translate((DOOR_START, -2 * WALL_THICKNESS, THRESHOLD_HEIGHT + GROUND_HEIGHT_AT_DOOR))(
        s.cube([DOOR_WIDTH, 3 * WALL_THICKNESS, DOOR_HEIGHT])
    )
)


if __name__ == '__main__':
    d = DeckJoistsOnBlocks(ft(16), ft(16), 8)
    s.scad_render_to_file(ground + house + d.all(), 'foo.scad')
