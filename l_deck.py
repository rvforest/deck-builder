from __future__ import annotations
import math
from typing import Tuple

from colors import BROWN
from deck import Deck
from deck_joists_on_blocks import DeckJoistsOnBlocks, DeckBlockFrame
from decking import Decking
from layers import Layer
from lumber import MiteredBoard, DeckingBoard
from point import Point3D, Dim
from shapes import ShapeCollection
from util import oc_spacing, n_members

STAIR_OFFSET = 4


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
            include_end_joist=(True, False),
            n_rim_joist=(1, 2),
            max_joist_spacing=16,
            deck=section1
        )
        print(f"# section 1 joists: {self.section1.n_joists}")
        # extra_space = self.section1.joist_spacing
        extra_space = 12
        self.section2_start = (
            self.ldeck.section1.width - section1.block_overhang2 - section2.joist_class.width + extra_space
        )
        self.section2 = DeckBlockFrame(
            section2.width - (extra_space - self.ldeck.block_overhang2) + section2.joist_class.width,
            section2.length,
            block_overhang1=0,
            block_overhang2=section2.block_overhang2,
            include_rim_joist=(False, False),
            n_rim_joist=(1, 2),
            include_end_joist=(True, True),
            loc=Point3D(
                x=self.section2_start,
                y=ldeck.cutout_y,
                z=0
            ),
            max_joist_spacing=16,
            deck=section2
        )
        print(f"# section 2 joists: {self.section2.n_joists}")
        print(f"# section 2 joist spacing: {self.section2.joist_spacing}")
        self.thickness = self.section1.thickness
        self.cutout_x = ldeck.cutout_x
        self.cutout_y = ldeck.cutout_y

    def shape(self) -> ShapeCollection:
        joist = self.ldeck.joist_class
        l_blocking_span = self.cutout_y - self.ldeck.joist_overhang + 3 * joist.width / 2
        n_blocking_boards_at_l = n_members(l_blocking_span, joist.width, max_span=16)
        blocking_spacing = oc_spacing(l_blocking_span, joist.width, n_blocking_boards_at_l)
        n_blocking_boards_at_l -= 1  # Last blocking board falls on existing rim joist
        print(f"Blocking spacing at L: {blocking_spacing:.2f}")

        frame = self.section1.shape() + self.section2.shape()

        # Double rim joist
        frame += ShapeCollection([
                self.section1.outer_joist_class(
                    self.ldeck.width,
                    position=Point3D(
                        0,
                        self.section1.length - self.section1.joist_class.width,
                        self.section1.outer_height_offset
                    )
                ),
                self.section1.outer_joist_class(
                    self.ldeck.width,
                    position=Point3D(
                        0,
                        self.section1.length - 2 * self.section1.joist_class.width,
                        self.section1.outer_height_offset
                    )
                ),
            ])
        # End Joist at L
        frame += ShapeCollection([
            self.section2.outer_joist_class(
                self.cutout_y - self.section2.outer_joist_class.width,
                position=Point3D(
                    x=self.ldeck.width - self.cutout_x - self.section2.outer_joist_class.width,
                    y=self.section2.outer_joist_class.width,
                    z=0
                ),
                orient_towards=Dim.Y
            ),
        ])
        # Rim Joist at L
        frame += ShapeCollection([
            self.section2.outer_joist_class(
                self.cutout_x + self.section2.outer_joist_class.width + self.ldeck.block_overhang2 - joist.width,
                position=Point3D(
                    x=(self.ldeck.width - self.cutout_x - self.section2.outer_joist_class.width
                        - self.ldeck.block_overhang2 + joist.width),
                    y=self.cutout_y,
                    z=0
                ),
                orient_towards=Dim.X
            )
        ])
        # Blocking at L overhang
        frame += ShapeCollection([
            self.section2.joist_class(
                self.ldeck.block_overhang2 - self.section2.outer_joist_class.width,
                position=Point3D(
                    x=(self.ldeck.width - self.cutout_x + self.section2.joist_class.width
                        - self.section2.outer_joist_class.width - self.ldeck.block_overhang2),
                    y=(self.ldeck.joist_overhang - self.section2.joist_class.width / 2
                       + i * blocking_spacing),
                    z=0
                ),
                orient_towards=Dim.X,
                layer=Layer.BLOCKING
            )
            for i in range(n_blocking_boards_at_l)
        ])
        # Stairs
        stairs = ShapeCollection([
            joist(
                self.ldeck.tread_width,
                Point3D(
                    x=self.ldeck.width - self.ldeck.cutout_x,
                    y=self.cutout_y - joist.width,
                    z=0
                ),
                orient_towards=Dim.X,
                layer=Layer.STAIRS
            ),
            joist(
                self.ldeck.tread_width,
                Point3D(
                    x=self.ldeck.width - self.ldeck.cutout_x,
                    y=self.cutout_y - self.ldeck.tread_depth,
                    z=0
                ),
                orient_towards=Dim.X,
                layer=Layer.STAIRS
            )
        ])
        # Blocking for stairs
        n_blocking_boards_stairs = n_members(self.ldeck.tread_width, joist.width, max_span=12)
        blocking_spacing = oc_spacing(self.ldeck.tread_width, joist.width, n_blocking_boards_stairs)
        stair_blocking_len = self.ldeck.tread_depth - 2 * joist.width
        print(f"Stair blocking len: {stair_blocking_len}")
        stairs += ShapeCollection([
            joist(
                stair_blocking_len,
                Point3D(
                    x=self.ldeck.width - self.ldeck.cutout_x + i * blocking_spacing,
                    y=self.cutout_y - joist.width - stair_blocking_len,
                    z=0
                ),
                orient_towards=Dim.Y,
                layer=Layer.STAIRS
            )
            for i in range(n_blocking_boards_stairs)
        ])

        stairs = stairs.translate(0, 0, -STAIR_OFFSET)
        frame += stairs
        return frame


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
        self._n_boards1 = None
        self._n_boards2 = None

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
            print(f'Width-to-width decking gap: {gap:.3f}"')

        return self._w2w_gap

    def _n_boards(self, length: float) -> float:
        return length / (self.section1.decking_board_class.width + self.w2w_gap)

    @property
    def n_boards1(self) -> Tuple[int, float]:
        if self._n_boards1 is None:
            result = self._n_boards(
                self.cutout_y - self.decking_start - self.board_overhang
                + self.section1.decking_board_class.width + self.w2w_gap
            )
            assert result % 1 == 0
            print(f"{int(result)} boards in section 1")
            self._n_boards1 = int(result), 0
        return self._n_boards1

    @property
    def n_boards2(self) -> Tuple[int, float]:
        if self._n_boards2 is None:
            result = self._n_boards(
                self.ldeck.section2.length
                + 2 * self.board_overhang
                - 2 * self.ldeck.decking_board_class.width
                - 1 * self.w2w_gap
            )
            last_board_width = (result % 1) * (self.ldeck.decking_board_class.width + self.w2w_gap) - self.w2w_gap
            print(f"{int(result)} boards in section 2")
            print(f'Last board ripped to {last_board_width:0.2f}".')
            self._n_boards2 = int(result), last_board_width
        return self._n_boards2

    def shape(self) -> ShapeCollection:
        board = self.ldeck.decking_board_class.copy()
        board.w2w_gap = self.w2w_gap
        board.e2e_gap = self.e2e_gap
        board_spacing = board.width + self.w2w_gap

        section1_len = self.ldeck.width - self.ldeck.cutout_x + 2 * self.board_overhang - 2 * board.width
        boards = ShapeCollection([
            # Section 1 - shorter decking span
            board(
                section1_len - 2 * self.e2e_gap,
                orient_towards=Dim.X,
                position=Point3D(
                    x=-self.board_overhang + board.width + self.e2e_gap,
                    y=i * board_spacing + LDecking.decking_start,
                    z=0
                )
            )
            for i in range(self.n_boards1[0])
        ])

        # Section 2 - longer decking span
        boards += ShapeCollection([
            board(
                self.ldeck.width + 2 * self.board_overhang - 2 * board.width - 2 * self.e2e_gap,
                orient_towards=Dim.X,
                position=Point3D(
                    x=-self.board_overhang + board.width + self.e2e_gap,
                    y=(i + 1) * board_spacing + self.ldeck.cutout_y - self.board_overhang,
                    z=0
                )
            )
            for i in range(self.n_boards2[0])
        ])

        # Final board needs to be ripped
        boards += ShapeCollection([
            DeckingBoard(
                self.w2w_gap,
                self.e2e_gap,
                width=self.n_boards2[1],
                height=board.height,
                length=self.ldeck.width + 2 * self.board_overhang - 2 * board.width,
                position=Point3D(
                    x=-self.board_overhang + board.width,
                    y=(self.n_boards2[0] + 1) * board_spacing + self.ldeck.cutout_y - self.board_overhang,
                    z=0
                ),
                color=self.section1.decking_board_class.color
            )
        ])

        stair_treads = ShapeCollection([
            board(
                self.ldeck.tread_width,
                Point3D(
                    x=self.ldeck.width - self.ldeck.cutout_x,
                    y=(self.cutout_y - self.ldeck.tread_depth
                       - self.board_overhang + i * (board.width + self.w2w_gap)),
                    z=0
                ),
                orient_towards=Dim.X,
                layer=Layer.STAIRS
            )
            for i in range(2)
        ])
        boards += stair_treads.translate(0, 0, -STAIR_OFFSET)

        # picture frame
        boards += ShapeCollection([
            MiteredBoard(
                board.width,
                board.height,
                self.ldeck.length + self.board_overhang - LDecking.decking_start,
                position=Point3D(-self.board_overhang, LDecking.decking_start, 0),
                orient_towards=Dim.Y,
                end_miter='down',
                color=BROWN
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
                end_miter='down',
                color=BROWN
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
                end_miter='up',
                color=BROWN
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
                end_miter='up',
                color=BROWN
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
                end_miter='down',
                color=BROWN
            ),
        ])
        return boards


class LDeckOnBlocks(Deck):
    """An L-shaped deck defined as a rectangle with a cutout in the SW corner."""

    def __init__(
            self,
            *args,
            block_overhang1,
            block_overhang2,
            block_overhang3,
            cutout_x,
            cutout_y,
            tread_depth=11,
            tread_width=38,
            **kwargs
    ):
        """
        :param tread_width:
        :param cutout_x: float Length of cutout in x direction.
        :param cutout_y: float Length of cutout in y direction.
        :param args:
        """
        self.block_overhang1 = block_overhang1
        self.block_overhang2 = block_overhang2
        self.block_overhang3 = block_overhang3
        self.cutout_x = cutout_x
        self.cutout_y = cutout_y
        self.tread_depth = tread_depth
        self.tread_width = tread_width
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

        self._frame_cache = None

    @property
    def _decking(self) -> LDecking:
        return LDecking(self)

    @property
    def _frame(self) -> LDeckFrame:
        if self._frame_cache is None:
            self._frame_cache = LDeckFrame(self)
        return self._frame_cache

    def footings(self) -> ShapeCollection:
        section1 = self.section1.footings()
        frame2 = self._frame.section2
        section2 = self.section2.footings(loc=frame2.loc, n_joists=frame2.n_joists, joist_spacing=frame2.joist_spacing)
        return section1 + section2

    def all(self, show_decking=True, show_frame=False) -> ShapeCollection:
        shape_collection = ShapeCollection([])
        if show_frame:
            shape_collection = self.frame() + self.footings()
        if show_decking:
            shape_collection += self.decking()
        return shape_collection
