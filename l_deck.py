from __future__ import annotations
import math

from deck import Deck
from deck_joists_on_blocks import DeckJoistsOnBlocks, DeckBlockFrame
from decking import Decking
from point import Point3D, Dim
from shapes import ShapeCollection


class LDeckFrame:
    def __init__(self, section1: DeckJoistsOnBlocks, section2: DeckJoistsOnBlocks, cutout_x: float, cutout_y: float):
        self.section1 = DeckBlockFrame(
            section1.width,
            section1.length,
            max_joist_spacing=16,
            deck=section1,
            include_rim_joist=(True, False),
            block_overhang1=section1.block_overhang1,
            block_overhang2=section1.block_overhang2,
        )
        self.section2 = DeckBlockFrame(
            section2.width,
            section2.length,
            max_joist_spacing=16,
            deck=section2,
            include_rim_joist=(True, False),
            include_end_joist=(False, True),
            loc=Point3D(section1.width, cutout_y, 0),
            block_overhang1=section2.block_overhang1,
            block_overhang2=section2.block_overhang2
        )
        self.thickness = self.section1.thickness
        self.cutout_x = cutout_x
        self.cutout_y = cutout_y

    def shape(self) -> ShapeCollection:
        return (
            self.section1.shape()
            + self.section2.shape()
            + ShapeCollection([
                self.section1.joist_class(
                    self.section1.true_width + self.section2.true_width,
                    position=Point3D(0, self.section1.length - self.section1.joist_class.width, 0)
                )
            ])
        )


class LDecking:

    decking_start = 0.5

    def __init__(self, ldeck: LDeckOnBlocks):
        self.ldeck = ldeck

        self.section1 = ldeck.section1
        self.section2 = ldeck.section2
        self.cutout_x = ldeck.cutout_x
        self.cutout_y = ldeck.cutout_y

    @property
    def w2w_gap(self):
        board = self.ldeck.decking_board_class
        len_to_deck = self.cutout_y - LDecking.decking_start
        n_boards = math.floor(len_to_deck / board.width)
        gap = (len_to_deck - board.width * n_boards) / (n_boards - 1)

        if gap < Decking.w2w_gap_min:
            n_boards -= 1
            gap = (len_to_deck - board.width * n_boards) / (n_boards - 1)

        if gap > Decking.w2w_gap_max:
            raise ValueError("Could not find gap to match deck dimensions.")

        return gap

    def _n_boards(self, length: float) -> int:
        result = length / (self.section1.decking_board_class.width + self.w2w_gap)
        assert result % 1 == 0
        return int(result)

    @property
    def n_boards1(self) -> int:
        return self._n_boards(self.cutout_y)

    @property
    def n_boards2(self) -> int:
        return self._n_boards(self.section2.length)

    def shape(self) -> ShapeCollection:
        board = self.ldeck.decking_board_class
        boards = ShapeCollection([
            # Section 1 - shorter decking span
            board(self.ldeck.width - self.ldeck.cutout_x, orient_towards=Dim.X, position=Point3D(
                x=0,
                y=i * (board.width + self.w2w_gap) + LDecking.decking_start,
                z=0
            ))
            for i in range(self.n_boards1)
        ])

        # Section 2 - longer decking span
        boards += ShapeCollection([
            board(self.ldeck.width, orient_towards=Dim.X, position=Point3D(
                x=0,
                y=i * (board.width + self.w2w_gap) + self.ldeck.cutout_y + LDecking.decking_start,
                z=0
            ))
            for i in range(self.n_boards1)
        ])
        return boards


class LDeckOnBlocks(Deck):
    """An L-shaped deck defined as a rectangle with a cutout in the SW corner."""

    def __init__(self, *args, block_overhang1, block_overhang2, block_overhang3, cutout_x, cutout_y, **kwargs):
        """
        :param cutout_x: float Length of cutout in x direction.
        :param cutout_y: float Length of cutout in y direction.
        :param args:
        :param kwargs:
        """
        self.block_overhang1 = block_overhang1
        self.block_overhang2 = block_overhang2
        self.block_overhang3 = block_overhang3
        self.cutout_x = cutout_x
        self.cutout_y = cutout_y
        super().__init__(*args, **kwargs)

        self.section1 = DeckJoistsOnBlocks(
            width=self.width - self.cutout_x,
            length=self.length,
            height=self.height,
            beam_class=self.beam_class,
            joist_class=self.joist_class,
            decking_board_class=self.decking_board_class,
            footing_class=self.footing_class,
            joist_overhang=self.joist_overhang,
            beam_overhang=self.beam_overhang,
            block_overhang1=block_overhang1,
            block_overhang2=block_overhang2
        )
        self.section2 = DeckJoistsOnBlocks(
            width=self.cutout_x,
            length=self.length - self.cutout_y,
            height=self.height,
            beam_class=self.beam_class,
            joist_class=self.joist_class,
            decking_board_class=self.decking_board_class,
            footing_class=self.footing_class,
            joist_overhang=self.joist_overhang,
            beam_overhang=self.cutout_x,
            block_overhang1=0,
            block_overhang2=block_overhang3
        )

    @property
    def _decking(self) -> LDecking:
        return LDecking(self)

    @property
    def _frame(self) -> LDeckFrame:
        return LDeckFrame(self.section1, self.section2, self.cutout_x, self.cutout_y)

    def footings(self) -> ShapeCollection:
        n_joists2 = self._frame.section2.n_joists
        section2 = self.section2.footings()
        section2 = ShapeCollection([
            footing.translate(
                self.section1.width - self.section1.joist_class.width if i % n_joists2 == 0 else self.section1.width,
                self.cutout_y,
                0
            )
            for i, footing in enumerate(section2)
        ])
        return self.section1.footings() + section2

    def all(self) -> ShapeCollection:
        return self.frame() + self.footings()
