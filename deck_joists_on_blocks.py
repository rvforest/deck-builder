from deck import Deck
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
            include_end_joist=(True, True),
            loc: Point3D = Point3D(0, 0, 0),
            **kwargs
    ):
        self.true_include_rim_joist = include_rim_joist
        self.true_include_end_joist = include_end_joist
        self.true_loc = loc
        kwargs['include_rim_joist'] = (False, False)
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
        if self.true_include_rim_joist[0]:
            s += ShapeCollection([self.joist_class(self.true_width, orient_towards=Dim.X).translate(*self.true_loc)])
        if self.true_include_rim_joist[1]:
            s += ShapeCollection([
                    self.joist_class(
                        self.true_width,
                        orient_towards=Dim.X,
                        position=Point3D(0, self.length - self.joist_class.width, 0) + self.true_loc
                    )
                ])
        if self.true_include_end_joist[0]:
            s += ShapeCollection([self.joist_class(
                self.joist_len,
                orient_towards=Dim.Y,
                position=self.true_loc + Point3D(0, self.joist_y_start, 0)
            )])
        if self.true_include_end_joist[1]:
            s += ShapeCollection([
                self.joist_class(
                    self.joist_len,
                    orient_towards=Dim.Y,
                    position=self.true_loc + Point3D(self.true_width - self.joist_class.width, self.joist_y_start, 0)
                )
            ])
        return s


class DeckJoistsOnBlocks(Deck):

    def __init__(self, *args, block_overhang1, block_overhang2, **kwargs):
        self.block_overhang1 = block_overhang1
        self.block_overhang2 = block_overhang2
        super().__init__(*args, **kwargs)

    @property
    def _frame(self) -> DeckBlockFrame:
        return DeckBlockFrame(
            self.width,
            self.length,
            max_joist_spacing=16,
            joist_class=self.joist_class,
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

    def all(self):
        return self.frame() + self.footings() + self.decking() + ShapeCollection([Ground(), House()])


class LDeckFrame:
    def __init__(self, section1: DeckJoistsOnBlocks, section2: DeckJoistsOnBlocks, cutout_x: float, cutout_y: float):
        self.section1 = DeckBlockFrame(
            section1.width,
            section1.length,
            max_joist_spacing=16,
            joist_class=section1.joist_class,
            include_rim_joist=(True, False),
            block_overhang1=section1.block_overhang1,
            block_overhang2=section1.block_overhang2,
        )
        self.section2 = DeckBlockFrame(
            section2.width,
            section2.length,
            max_joist_spacing=16,
            joist_class=section2.joist_class,
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

        self._section1 = DeckJoistsOnBlocks(
            width=self.width - self.cutout_x,
            length=self.length,
            height=self.height,
            beam_class=self.beam_class,
            joist_class=self.joist_class,
            decking_class=self.decking_class,
            footing_class=self.footing_class,
            joist_overhang=self.joist_overhang,
            beam_overhang=self.beam_overhang,
            block_overhang1=block_overhang1,
            block_overhang2=block_overhang2
        )
        self._section2 = DeckJoistsOnBlocks(
            width=self.cutout_x,
            length=self.length - self.cutout_y,
            height=self.height,
            beam_class=self.beam_class,
            joist_class=self.joist_class,
            decking_class=self.decking_class,
            footing_class=self.footing_class,
            joist_overhang=self.joist_overhang,
            beam_overhang=self.cutout_x,
            block_overhang1=0,
            block_overhang2=block_overhang3
        )

    @property
    def _frame(self) -> LDeckFrame:
        return LDeckFrame(self._section1, self._section2, self.cutout_x, self.cutout_y)

    def footings(self) -> ShapeCollection:
        n_joists2 = self._frame.section2.n_joists
        section2 = self._section2.footings()
        section2 = ShapeCollection([
            footing.translate(
                self._section1.width - self._section1.joist_class.width if i % n_joists2 == 0 else self._section1.width,
                self.cutout_y,
                0
            )
            for i, footing in enumerate(section2)
        ])
        return self._section1.footings() + section2

    def all(self) -> ShapeCollection:
        return self.frame() + self.footings()
