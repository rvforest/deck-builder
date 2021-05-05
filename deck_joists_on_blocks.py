from typing import Type

from deck import Deck
from decking import SingleSpanDecking, Decking
from frame import SingleSpanFrame
from point import Point3D, Dim
from surroundings import Ground, House
from lumber import LumberSize
from shapes import ShapeCollection


class DeckBlockFrame(SingleSpanFrame):

    def __init__(
            self,
            *args,
            block_overhang1,
            block_overhang2,
            include_rim_joist=(True, True),
            n_rim_joist=(1, 1),
            include_end_joist=(True, True),
            loc: Point3D = Point3D(0, 0, 0),
            **kwargs
    ):
        self.true_include_rim_joist = include_rim_joist
        self.n_rim_joist = n_rim_joist
        self.true_include_end_joist = include_end_joist
        self.true_loc = loc
        kwargs['include_rim_joist'] = (False, False)
        kwargs['n_rim_joist'] = n_rim_joist
        ej1 = ej2 = True
        if (block_overhang1 == 0) and (not include_end_joist[0]):
            ej1 = False
        if (block_overhang2 == 0) and (not include_end_joist[1]):
            ej2 = False
        kwargs['include_end_joist'] = (ej1, ej2)
        kwargs['loc'] = Point3D(block_overhang1, 0, 0) + loc
        try:
            width = kwargs.pop('width')
        except KeyError:
            width = args[0]
            args = args[1:]
        self.block_overhang1 = block_overhang1
        self.block_overhang2 = block_overhang2
        super().__init__(width - block_overhang1 - block_overhang2, *args, **kwargs)
        self.true_width = width

    def shape(self) -> ShapeCollection:
        s = super().shape()
        joist = self.joist_class

        if self.true_include_rim_joist[0]:
            s += ShapeCollection([
                self.outer_joist_class(
                    self.true_width,
                    orient_towards=Dim.X,
                    position=self.true_loc + Point3D(0, 0, self.outer_height_offset)
                )
            ])
            if self.n_rim_joist[0] == 2:
                s += ShapeCollection([
                    self.outer_joist_class(
                        self.true_width,
                        orient_towards=Dim.X,
                        position=self.true_loc + Point3D(0, joist.width, self.outer_height_offset)
                    ),
                ])

        if self.true_include_rim_joist[1]:
            s += ShapeCollection([
                self.outer_joist_class(
                    self.true_width,
                    orient_towards=Dim.X,
                    position=Point3D(0, self.length - joist.width, self.outer_height_offset) + self.true_loc
                )
            ])
            if self.n_rim_joist[1] == 2:
                s += ShapeCollection([
                    self.outer_joist_class(
                        self.true_width,
                        orient_towards=Dim.X,
                        position=Point3D(0, self.length - 2 * joist.width, self.outer_height_offset) + self.true_loc
                    )
                ])

        if self.true_include_end_joist[0]:
            s += ShapeCollection([
                self.outer_joist_class(
                    self.joist_len,
                    orient_towards=Dim.Y,
                    position=self.true_loc + Point3D(0, self.joist_y_start, self.outer_height_offset)
                )
            ])
        if self.true_include_end_joist[1]:
            s += ShapeCollection([
                self.outer_joist_class(
                    self.joist_len,
                    orient_towards=Dim.Y,
                    position=self.true_loc + Point3D(
                        self.true_width - joist.width,
                        self.joist_y_start,
                        self.outer_height_offset
                    )
                )
            ])

        # Blocking on overhang
        if self.block_overhang1 > 0:
            s += ShapeCollection([
                joist(
                    self.block_overhang1 - joist.width,
                    orient_towards=Dim.X,
                    position=Point3D(joist.width, self.deck.joist_overhang - joist.width / 2, 0)
                ),
                joist(
                    self.block_overhang1 - joist.width,
                    orient_towards=Dim.X,
                    position=self.true_loc + self.true_loc + self.true_loc + self.true_loc + Point3D(
                        joist.width,
                        (self.length - 2 * self.deck.joist_overhang) / 2 + self.deck.joist_overhang - joist.width,
                        0
                    )
                ),
                joist(
                    self.block_overhang1 - joist.width,
                    orient_towards=Dim.X,
                    position=self.true_loc + Point3D(
                        joist.width,
                        self.length - self.deck.joist_overhang - 3/2 * joist.width,
                        0
                    )
                )
            ])
        if self.block_overhang2 > 0:
            s += ShapeCollection([
                joist(
                    self.block_overhang2 - joist.width,
                    orient_towards=Dim.X,
                    position=self.true_loc + Point3D(
                        self.true_width - self.block_overhang2,
                        self.deck.joist_overhang - joist.width / 2,
                        0
                    )
                ),
                joist(
                    self.block_overhang2 - joist.width,
                    orient_towards=Dim.X,
                    position=self.true_loc + Point3D(
                        self.true_width - self.block_overhang2,
                        (self.length - 2 * self.deck.joist_overhang) / 2 + self.deck.joist_overhang - joist.width,
                        0
                    )
                ),
                joist(
                    self.block_overhang2 - joist.width,
                    orient_towards=Dim.X,
                    position=self.true_loc + Point3D(
                        self.true_width - self.block_overhang2,
                        self.length - self.deck.joist_overhang - 3 / 2 * joist.width,
                        0
                    )
                ),
            ])
        return s


class DeckJoistsOnBlocks(Deck):

    def __init__(
            self,
            *args,
            block_overhang1,
            block_overhang2,
            decking_class: Type[Decking] = SingleSpanDecking,
            **kwargs
    ):
        self.block_overhang1 = block_overhang1
        self.block_overhang2 = block_overhang2
        self.decking_class = decking_class
        super().__init__(*args, **kwargs)

    @property
    def _frame(self) -> DeckBlockFrame:
        return DeckBlockFrame(
            self.width,
            self.length,
            max_joist_spacing=16,
            deck=self,
            block_overhang1=self.block_overhang1,
            block_overhang2=self.block_overhang2
        )

    def footings(self):
        b = ShapeCollection()
        for i in range(self.n_beams):
            for j in range(0, self._frame.n_joists):
                b.append(
                    self.footing_class().translate(
                        j * self._frame.joist_spacing + LumberSize.TWO.value / 2 + self.block_overhang1,
                        i * self.beam_spacing + self.joist_overhang,
                        0
                    )
                )
        return b.translate(0, 0, self.beam_height - self.footing_class.height)

    def _decking(self) -> Decking:
        return self.decking_class(self.width, self.length, self.decking_board_class)

    def all(self):
        return self.frame() + self.footings() + self.decking() + ShapeCollection([Ground(), House()])
