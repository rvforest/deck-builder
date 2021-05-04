from __future__ import annotations
from typing import Dict

from footings import FootingFactory
from frame import Frame
from lumber import LumberSize, LumberFactory
from shapes import ShapeCollection, Drawable
from util import ft, n_members, oc_spacing

# southern pine
joist_spans: Dict[float, float] = {
    LumberSize.SIX.value: ft(6) + 8,
    LumberSize.EIGHT.value: ft(10) + 1,
    LumberSize.TEN.value: ft(14),
    LumberSize.TWELVE.value: ft(16) + 6
}


class Deck:

    def __init__(
            self,
            width: float,
            length: float,
            height: float,
            beam_class: LumberFactory,
            joist_class: LumberFactory,
            decking_board_class: LumberFactory,
            footing_class: FootingFactory,
            joist_overhang: float = 16,
            beam_overhang: float = 16,
    ):
        self.width = width
        self.length = length
        self.height = height
        self.beam_class = beam_class
        self.joist_class = joist_class
        self.decking_board_class = decking_board_class
        self.footing_class = footing_class
        self.joist_overhang = joist_overhang
        self.beam_overhang = beam_overhang

    @property
    def n_beams(self):
        return n_members(self.inner_length, self.beam_class.width, max_span=joist_spans[self._frame.thickness])

    @property
    def inner_length(self):
        return self.length - 2 * self.joist_overhang

    @property
    def beam_spacing(self):
        """Amount of space between joists."""
        return oc_spacing(self.inner_length, self.beam_class.width, self.n_beams)

    @property
    def frame_height(self):
        return self.height - self.decking_board_class.height

    @property
    def beam_height(self):
        return self.frame_height - self._frame.thickness

    @property
    def post_height(self):
        return self.beam_height - self.beam_class.height

    def footings(self) -> ShapeCollection:
        raise NotImplementedError

    @property
    def _frame(self) -> Frame:
        raise NotImplementedError

    def frame(self) -> ShapeCollection:
        return self._frame.shape().translate(0, 0, self.beam_height)

    @property
    def _decking(self) -> Drawable:
        raise NotImplementedError

    def decking(self) -> ShapeCollection:
        return self._decking.shape().translate(0, 0, self.frame_height)

    def all(self):
        raise NotImplementedError
