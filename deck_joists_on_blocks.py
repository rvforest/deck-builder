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