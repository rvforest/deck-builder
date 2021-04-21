from deck import Deck
from frame import Frame, SingleSpanFrame
from point import Point3D, Dim
from surroundings import Ground, House
from lumber import LumberSize, LumberFactory
from shapes import ShapeCollection
from util import even_spacing


class DeckBlockFrame(SingleSpanFrame):

    def __init__(self, *args, block_overhang, **kwargs):
        try:
            width = kwargs.pop('width')
        except KeyError:
            width = args[0]
            args = args[1:]
        self.block_overhang = block_overhang
        super().__init__(width - 2 * block_overhang, *args, **kwargs)
        self.true_width = width

    def shape(self) -> ShapeCollection:
        s = super().shape()
        s += ShapeCollection([
            self.joist_class(self.true_width, orient_towards=Dim.X),
            self.joist_class(
                self.true_width,
                orient_towards=Dim.X,
                position=Point3D(0, self.length - self.joist_class.width, 0)
            ),
            self.joist_class(self.length, orient_towards=Dim.Y),
            self.joist_class(self.length, orient_towards=Dim.Y).translate(
                x=self.true_width - self.joist_class.width,
                y=0,
                z=0
            ),
        ])
        return s


class DeckJoistsOnBlocks(Deck):

    def __init__(self, *args, block_overhang, **kwargs):
        self.block_overhang = block_overhang
        super().__init__(*args, **kwargs)

    @property
    def _frame(self) -> Frame:
        return DeckBlockFrame(
            self.width - 2 * self.block_overhang,
            self.length,
            max_joist_spacing=16,
            joist_class=self.joist_class,
            loc=Point3D(self.block_overhang, 0, 0),
            include_rim_joist=(False, False),
            block_overhang=self.block_overhang
        )

    def footings(self):
        b = ShapeCollection()
        for i in range(self.n_beams):
            for j in range(0, self._frame.n_joists):
                b.append(
                    self.footing_class().translate(
                        j * self._frame.joist_spacing + LumberSize.TWO.value / 2 + self.block_overhang,
                        i * self.beam_spacing + self.joist_overhang,
                        0
                    )
                )
        return b.translate(0, 0, self.beam_height - self.footing_class.height)

    def all(self):
        return self.frame() + self.footings() + self.decking() + ShapeCollection([Ground(), House()])


class LDeckOnBlocks(Deck):
    """An L-shaped deck defined as a rectangle with a cutout in the SW corner."""

    def __init__(self, *args, **kwargs):
        """
        :param cutout_x: float Length of cutout in x direction.
        :param cutout_y: float Length of cutout in y direction.
        :param args:
        :param kwargs:
        """
        self.cutout_x = kwargs.pop('cutout_x')
        self.cutout_y = kwargs.pop('cutout_y')
        super().__init__(*args, **kwargs)

        self.section1_width = self.width - self.cutout_x
        self.section2_width = self.cutout_x
        self.section1_length = self.length
        self.section2_length = self.length - self.cutout_y
        self.section2_start = (self.section1_width, self.cutout_y, 0)
        self._section1 = DeckJoistsOnBlocks(
            width=self.width - self.cutout_x,
            length=self.length,
            height=self.height,
            beam_class=self.beam_class,
            decking_class=self.decking_class,
            footing_class=self.footing_class,
            joist_overhang=self.joist_overhang,
            beam_overhang=self.beam_overhang
        )
        self._section2 = DeckJoistsOnBlocks(
            width=self.cutout_x,
            length=self.length - self.cutout_y,
            height=self.height,
            beam_class=self.beam_class,
            decking_class=self.decking_class,
            footing_class=self.footing_class,
            joist_overhang=self.joist_overhang,
            beam_overhang=self.cutout_x
        )

    def frame(self, include_far_rim_joist=True, include_first_end_joist=True) -> ShapeCollection:
        f = self._section1.frame(
            include_far_rim_joist=False,
            include_first_end_joist=include_first_end_joist
        )

        f += self._section2.frame(
            include_far_rim_joist=False,
            include_first_end_joist=False
        ).translate(*self.section2_start)

        if include_far_rim_joist:
            f.append(
                self.joist_class(self.width).translate(
                    0,
                    self.length - self.joist_class.width,
                    self.beam_height
                )
            )
        return f

    def footings(self) -> ShapeCollection:
        extra_blocks = ShapeCollection()
        for i in range(self.n_beams):
            extra_blocks.append(
                self.footing_class().translate(
                    self.section1_width - LumberSize.TWO.value / 2,
                    self.cutout_y + i * self._section2.beam_spacing + self.beam_overhang,
                    0
                )
            )
        extra_blocks = extra_blocks.translate(0, 0, self.beam_height - self.footing_class.height)

        return (
            self._section1.footings()
            + self._section2.footings().translate(*self.section2_start)
            + extra_blocks
        )

    def all(self) -> ShapeCollection:
        return self.frame() + self.footings()
