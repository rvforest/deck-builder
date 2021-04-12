from __future__ import annotations
import math
from typing import Optional, Dict

import solid as s
import solid.utils as su

from lumber import LumberSize, LumberFactory
from point import Point3D
from shapes import Dim, Shape, ShapeCollection, TrapezoidalPrism
from util import ft, write_dxf_doc


# southern pine
joist_spans: Dict[float, float] = {
    LumberSize.SIX.value: ft(6) + 8,
    LumberSize.EIGHT.value: ft(10) + 1,
    LumberSize.TEN.value: ft(14),
    LumberSize.TWELVE.value: ft(16) + 6
}


def n_members(length, lumber_width, max_span):
    width_minus_last = length - lumber_width
    return math.ceil(width_minus_last / max_span) + 1


def oc_spacing(frame_width, lumber_width, n):
    return (frame_width - lumber_width) / (n - 1)


class Deck:

    def __init__(
            self,
            width: float,
            length: float,
            height: float,
            beam_class: LumberFactory,
            joist_class: LumberFactory,
            decking_class: LumberFactory,
            footing_class: FootingFactory,
            max_spacing: float = 16,
            joist_overhang: float = ft(2),
            beam_overhang: float = ft(2),
    ):
        self.width = width
        self.length = length
        self.height = height
        self.beam_class = beam_class
        self.joist_class = joist_class
        self.decking_class = decking_class
        self.footing_class = footing_class
        self.max_spacing = max_spacing
        self.joist_overhang = joist_overhang
        self.beam_overhang = beam_overhang

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
        return n_members(self.width, lumber_width=LumberSize.TWO.value, max_span=self.max_spacing)

    @property
    def n_beams(self):
        return n_members(self.inner_length, self.beam_class.width, max_span=joist_spans[self.joist_class.height])

    @property
    def inner_length(self):
        return self.length - 2 * self.joist_overhang

    @property
    def joist_spacing(self):
        """Amount of space between joists."""
        return oc_spacing(self.width, self.joist_class.width, self.n_joists)

    @property
    def beam_spacing(self):
        """Amount of space between joists."""
        return oc_spacing(self.inner_length, self.beam_class.width, self.n_beams)

    @property
    def frame_height(self):
        return self.height - self.decking_class.height

    @property
    def beam_height(self):
        return self.frame_height - self.joist_class.height

    @property
    def post_height(self):
        return self.beam_height - self.beam_class.height

    def footings(self):
        raise NotImplementedError

    def frame(self):
        joist = self.joist_class

        # Set rim joist
        # Joists face Y direction and rim joists face X direction
        f = ShapeCollection()
        f.append(joist(self.width, orient_towards=Dim.X))

        # Set joists
        row_position = self.row_offset
        for i in range(self.n_joist_spans):
            for j in range(0, self.n_joists):
                f.append(joist(self.joist_len, orient_towards=Dim.Y).translate(
                    j * self.joist_spacing,
                    row_position,
                    0
                ))
            row_position += self.joist_len + self.joist_class.width
            f.append(joist(self.width).translate(0, row_position - self.joist_class.width, 0))

        return f.translate(0, 0, self.beam_height)

    def decking(self):
        return ShapeCollection([
            self.decking_class(ft(20)).translate(0, 0, self.frame_height)
        ])


class FlushBeamDeck(Deck):

    @property
    def n_joist_spans(self):
        return self.n_beams - 1

    @property
    def joist_len(self):
        return self.length / (self.n_beams - 1)

    @property
    def row_offset(self):
        return self.beam_class.width

    def footings(self):
        pass


class DeckJoistsOnBlocks(Deck):

    def footings(self):
        b = ShapeCollection()
        for i in range(self.n_beams):
            for j in range(1, self.n_joists - 1):
                b.append(
                    self.footing_class().translate(
                        j * self.joist_spacing + LumberSize.TWO.value / 2,
                        i * self.beam_spacing + self.beam_overhang,
                        0
                    )
                )
        return b.translate(0, 0, self.beam_height - self.footing_class.height)

    def all(self):
        return self.frame() + self.footings() + self.decking()


class FootingFactory:

    height: float

    def __call__(self, position: Optional[Point3D] = None, layer: Optional[str] = None) -> Shape:
        raise NotImplementedError


class DeckBlockFactory(FootingFactory):

    def __init__(
            self,
            block_height: float = 7.75,
            block_slot_height: float = 6,
            block_base_len: float = 10.75,
            block_top_len: float = 8,
    ):
        self.block_height = block_height
        self.block_slot_height = block_slot_height
        self.block_base_len = block_base_len
        self.block_top_len = block_top_len

        self.height = block_slot_height
        self.block_scale = self.block_top_len / self.block_base_len

    def __call__(self, position: Optional[Point3D] = None, layer: Optional[str] = None) -> TrapezoidalPrism:
        return TrapezoidalPrism(
            bottom_square_len=self.block_base_len,
            top_square_len=self.block_top_len,
            height=self.block_height,
            position=position,
            layer=layer
        )


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
# noinspection PyTypeChecker
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
    TwoBySix = LumberFactory(LumberSize.TWO.value, LumberSize.SIX.value)
    d = DeckJoistsOnBlocks(
        width=ft(16),
        length=ft(16),
        height=8,
        beam_class=TwoBySix,
        joist_class=TwoBySix,
        decking_class=LumberFactory(LumberSize.SIX.value, LumberSize.ONE.value),
        footing_class=DeckBlockFactory()
    )
    s.scad_render_to_file(ground + house + d.all().render_scad(), 'foo.scad')
    write_dxf_doc(d.all(), Dim.Z, 'foo_top.dxf')
    write_dxf_doc(d.all(), Dim.Y, 'foo_front.dxf')
    write_dxf_doc(d.all(), Dim.X, 'foo_side.dxf')
