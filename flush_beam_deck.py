from deck import Deck


class FlushBeamDeck(Deck):

    @property
    def n_joist_spans(self):
        return self.n_beams - 1

    @property
    def joist_len(self):
        return self.length / (self.n_beams - 1)

    @property
    def row_offset(self):
        return self.beam_class.width

    def footings(self):
        pass