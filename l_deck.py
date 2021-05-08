from __future__ import annotations
import math
from typing import Tuple

from deck import Deck
from deck_joists_on_blocks import DeckJoistsOnBlocks, DeckBlockFrame
from decking import Decking
from lumber import MiteredBoard, DeckingBoard
from point import Point3D, Dim
from shapes import ShapeCollection


class LDeckFrame:
    def __init__(self, ldeck: LDeckOnBlocks):
        self.ldeck = ldeck
        section1 = ldeck.section1
        section2 = ldeck.section2
        self.section1 = DeckBlockFrame(
            section1.width,
            section1.length,
            block_overhang1=section1.block_overhang1,
            block_overhang2=section1.block_overhang2,
            include_rim_joist=(True, False),
            n_rim_joist=(1, 2),
            max_joist_spacing=16,
            deck=section1
        )
        self.section2 = DeckBlockFrame(
            section2.width,
            section2.length,
            block_overhang1=section2.block_overhang1,
            block_overhang2=section2.block_overhang2,
            include_rim_joist=(True, False),
            n_rim_joist=(1, 2),
            include_end_joist=(False, True),
            loc=Point3D(section1.width, ldeck.cutout_y, 0),
            max_joist_spacing=16,
            deck=section2
        )
        self.thickness = self.section1.thickness
        self.cutout_x = ldeck.cutout_x
        self.cutout_y = ldeck.cutout_y

    def shape(self) -> ShapeCollection:
        return (
            self.section1.shape()
            + self.section2.shape()
            + ShapeCollection([
                self.section1.outer_joist_class(
                    self.section1.true_width + self.section2.true_width,
                    position=Point3D(
                        0,
                        self.section1.length - self.section1.joist_class.width,
                        self.section1.outer_height_offset
                    )
                ),
                self.section1.outer_joist_class(
                    self.section1.true_width + self.section2.true_width,
                    position=Point3D(
                        0,
                        self.section1.length - 2 * self.section1.joist_class.width,
                        self.section1.outer_height_offset
                    )
                )
            ])
        )


class LDecking:

    decking_start = 0.5
    board_overhang = 1
    e2e_gap = 1 / 8

    def __init__(self, ldeck: LDeckOnBlocks):
        self.ldeck = ldeck

        self.section1 = ldeck.section1
        self.section2 = ldeck.section2
        self.cutout_x = ldeck.cutout_x
        self.cutout_y = ldeck.cutout_y

        self._w2w_gap = None

    @property
    def w2w_gap(self):
        if self._w2w_gap is None:
            board = self.ldeck.decking_board_class
            len_to_deck = self.cutout_y - LDecking.decking_start - self.board_overhang
            n_boards = math.floor(len_to_deck / board.width)
            gap = (len_to_deck - board.width * n_boards) / n_boards

            if gap < Decking.w2w_gap_min:
                n_boards -= 1
                gap = (len_to_deck - board.width * n_boards) / n_boards

            if gap > Decking.w2w_gap_max:
                raise ValueError(
                    'Could not find gap to match deck dimensions. '
                    f'Required gap is {gap:.2f}" but max gap size is {Decking.w2w_gap_max}"'
                )

            self._w2w_gap = gap

        return self._w2w_gap

    def _n_boards(self, length: float) -> float:
        return length / (self.section1.decking_board_class.width + self.w2w_gap)

    @property
    def n_boards1(self) -> Tuple[int, float]:
        result = self._n_boards(
            self.cutout_y - self.decking_start - self.board_overhang
            + self.section1.decking_board_class.width + self.w2w_gap
        )
        assert result % 1 == 0
        return int(result), 0

    @property
    def n_boards2(self) -> Tuple[int, float]:
        result = self._n_boards(
            self.ldeck.length
            - self.cutout_y
            + 2 * self.board_overhang
            - self.ldeck.decking_board_class.width
            - self.w2w_gap
        )
        return int(result), result % 1

    def shape(self) -> ShapeCollection:
        board = self.ldeck.decking_board_class.copy()
        board.w2w_gap = self.w2w_gap
        board.e2e_gap = self.e2e_gap
        board_spacing = board.width + self.w2w_gap

        section1_len = self.ldeck.width - self.ldeck.cutout_x + 2 * self.board_overhang - 2 * board.width
        boards = ShapeCollection([
            # Section 1 - shorter decking span
            board(
                section1_len,
                orient_towards=Dim.X,
                position=Point3D(
                    x=-self.board_overhang + board.width,
                    y=i * board_spacing + LDecking.decking_start,
                    z=0
                )
            )
            for i in range(self.n_boards1[0])
        ])

        # Section 2 - longer decking span
        boards += ShapeCollection([
            board(
                self.ldeck.width + 2 * self.board_overhang - 2 * board.width,
                orient_towards=Dim.X,
                position=Point3D(
                    x=-self.board_overhang + board.width,
                    y=i * board_spacing + self.ldeck.cutout_y - self.board_overhang,
                    z=0
                )
            )
            for i in range(1, self.n_boards2[0])
        ])

        # Final board needs to be ripped
        boards += ShapeCollection([
            DeckingBoard(
                self.w2w_gap,
                self.e2e_gap,
                width=board.width * self.n_boards2[1],
                height=board.height,
                length=self.ldeck.width + 2 * self.board_overhang - 2 * board.width,
                position=Point3D(
                    x=-self.board_overhang + board.width,
                    y=self.n_boards2[0] * board_spacing + self.ldeck.cutout_y - self.board_overhang,
                    z=0
                ),
                color=self.section1.decking_board_class.color
            )
        ])

        # picture frame
        boards += ShapeCollection([
            MiteredBoard(
                board.width,
                board.height,
                self.ldeck.length + self.board_overhang - LDecking.decking_start,
                position=Point3D(-self.board_overhang, LDecking.decking_start, 0),
                orient_towards=Dim.Y,
                end_miter='down'
            ),
            MiteredBoard(
                board.width,
                board.height,
                self.ldeck.width + 2 * self.board_overhang,
                position=Point3D(
                    -self.board_overhang,
                    self.ldeck.length + self.board_overhang - board.width,
                    0
                ),
                orient_towards=Dim.X,
                start_miter='down',
                end_miter='down'
            ),
            MiteredBoard(
                board.width,
                board.height,
                self.ldeck.section2.length + 2 * self.board_overhang,
                position=Point3D(
                    -self.board_overhang + self.ldeck.width + 2 * self.board_overhang - board.width,
                    self.cutout_y - self.board_overhang,
                    0
                ),
                orient_towards=Dim.Y,
                start_miter='up',
                end_miter='up'
            ),
            MiteredBoard(
                board.width,
                board.height,
                self.cutout_x + board.width,
                position=Point3D(
                    -self.board_overhang + self.ldeck.section1.width + 2 * self.board_overhang - board.width,
                    self.cutout_y - self.board_overhang,
                    0
                ),
                orient_towards=Dim.X,
                start_miter='down',
                end_miter='up'
            ),
            MiteredBoard(
                board.width,
                board.height,
                self.cutout_y - self.board_overhang + board.width - LDecking.decking_start,
                position=Point3D(
                    -self.board_overhang + self.ldeck.section1.width + 2 * self.board_overhang - board.width,
                    LDecking.decking_start,
                    0
                ),
                orient_towards=Dim.Y,
                start_miter=None,
                end_miter='down'
            ),
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
            outer_joist_class=self.outer_joist_class,
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
            outer_joist_class=self.outer_joist_class,
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
        return LDeckFrame(self)

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

    def all(self, show_decking=True, show_frame=False) -> ShapeCollection:
        shape_collection = ShapeCollection([])
        if show_frame:
            shape_collection = self.frame() + self.footings()
        if show_decking:
            shape_collection += self.decking()
        return shape_collection
