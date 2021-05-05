from __future__ import annotations
from typing import Tuple, TYPE_CHECKING, Literal

from point import Dim, Point3D
from shapes import ShapeCollection
from lumber import LumberSize
from util import n_members, oc_spacing, even_spacing

if TYPE_CHECKING:
    from deck import Deck

ZeroToTwo = Literal[0, 1, 2]


class Frame:

    def __init__(
            self,
            width: float,
            length: float,
            max_joist_spacing: float,
            deck: Deck,
            loc: Point3D = Point3D(0, 0, 0),
            include_end_joist: Tuple[bool, bool] = (True, True),
            include_rim_joist: Tuple[bool, bool] = (True, True),
            n_rim_joist: Tuple[ZeroToTwo, ZeroToTwo] = (1, 1)
    ):
        self.width = width
        self.length = length
        self.max_joist_spacing = max_joist_spacing
        self.deck = deck
        self.joist_class = deck.joist_class
        self.loc = loc
        self.include_end_joist = include_end_joist
        self.include_rim_joist = include_rim_joist
        self.n_rim_joist = n_rim_joist

        self.thickness = self.joist_class.height

    @property
    def joist_len(self) -> float:
        return self.length - sum(self.n_rim_joist) * self.joist_class.width

    @property
    def joist_y_start(self) -> float:
        return self.n_rim_joist[0] * self.joist_class.width

    @property
    def n_joists(self) -> int:
        return n_members(self.width, lumber_width=LumberSize.TWO.value, max_span=self.max_joist_spacing)

    @property
    def joist_spacing(self) -> float:
        """Amount of space between joists."""
        return oc_spacing(self.width, self.joist_class.width, self.n_joists)

    @property
    def n_joist_spans(self) -> int:
        raise NotImplementedError

    @property
    def joist_row_offset(self) -> float:
        raise NotImplementedError

    def shape(self) -> ShapeCollection:
        joist = self.joist_class
        f = ShapeCollection()

        # Set rim joist
        if self.include_rim_joist[0]:
            f.append(joist(self.width, orient_towards=Dim.X))

        # Set joists
        row_position = self.joist_y_start
        if self.include_end_joist[0]:
            f.append(joist(self.joist_len, orient_towards=Dim.Y).translate(
                0,
                row_position,
                0
            ))

        n_joists = self.n_joists - 1
        if not self.include_end_joist[1]:
            n_joists -= 1

        for i in range(self.n_joist_spans):
            f += even_spacing(
                lambda: joist(self.joist_len, orient_towards=Dim.Y),
                initial_pos=Point3D(self.joist_spacing, row_position, 0),
                offset=Point3D(self.joist_spacing, 0, 0),
                n=n_joists
            )
            row_position += self.joist_len + self.joist_row_offset

        if self.include_rim_joist[1]:
            f.append(joist(self.width).translate(0, row_position - self.joist_class.width, 0))

        return f.translate(*self.loc)


class SingleSpanFrame(Frame):

    @property
    def n_joist_spans(self) -> int:
        return 1

    @property
    def joist_row_offset(self) -> float:
        return 0


class MultiSpanFrame(Frame):

    def __init__(
            self,
            *args,
            n_spans: int,
            span_gap: float,
            **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.n_spans = n_spans
        self.span_gap = span_gap

    @property
    def n_joist_spans(self) -> int:
        return self.n_spans

    @property
    def joist_row_offset(self) -> float:
        return self.span_gap
