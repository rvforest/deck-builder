from __future__ import annotations
import math
from typing import Dict

from footings import FootingFactory
from lumber import LumberSize, LumberFactory
from shapes import Dim, ShapeCollection
from util import ft


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
            joist_overhang: float = 16,
            beam_overhang: float = 16,
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

    def footings(self) -> ShapeCollection:
        raise NotImplementedError

    def frame(self) -> ShapeCollection:
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

    def decking(self) -> ShapeCollection:
        return ShapeCollection([
            self.decking_class(ft(20)).translate(0, 0, self.frame_height)
        ])

    def all(self):
        raise NotImplementedError
