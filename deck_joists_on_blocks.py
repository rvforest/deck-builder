from deck import Deck
from surroundings import Ground, House
from lumber import LumberSize
from shapes import ShapeCollection


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
            joist_class=self.joist_class,
            decking_class=self.decking_class,
            footing_class=self.footing_class,
            max_spacing=self.max_spacing,
            joist_overhang=self.joist_overhang,
            beam_overhang=self.beam_overhang
        )
        self._section2 = DeckJoistsOnBlocks(
            width=self.cutout_x,
            length=self.length - self.cutout_y,
            height=self.height,
            beam_class=self.beam_class,
            joist_class=self.joist_class,
            decking_class=self.decking_class,
            footing_class=self.footing_class,
            max_spacing=self.max_spacing,
            joist_overhang=self.joist_overhang,
            beam_overhang=self.beam_overhang
        )

    def frame(self) -> ShapeCollection:
        return self._section1.frame() + self._section2.frame().translate(*self.section2_start)

    def footings(self) -> ShapeCollection:
        return self._section1.footings() + self._section2.footings().translate(*self.section2_start)

    def all(self) -> ShapeCollection:
        return self.frame() + self.footings()


