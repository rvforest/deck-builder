import math

import solid as s
import solid.utils as su

ONE = 0.75
TWO = 1.5
FOUR = 3.5
SIX = 5.5
EIGHT = 7.25
TEN = 9.25
TWELVE = 11.25

X = 0
Y = 1
Z = 2


def ft(f):
    return 12 * f


# southern pine
joist_spans = {
    SIX: ft(6) + 8,
    EIGHT: ft(10) + 1,
    TEN: ft(14),
    TWELVE: ft(16) + 6
}


def lumber(h, w, orient_towards='x'):
    """
    Lumber factory function
    :param orient_towards:
    :param h:
    :param w:

    """
    if orient_towards not in ('x', 'y', 'z'):
        raise ValueError("Invalid argument `orient_towards`. Value must be one of 'x', 'y', or 'z'")

    def inner(length):
        x, y, z = length, h, w
        if orient_towards == 'y':
            x, y = y, x
        elif orient_towards == 'z':
            x, z = z, x
        return s.cube([x, y, z])

    return inner


def n_members(length, lumber_width, max_span):
    width_minus_last = length - lumber_width
    return math.ceil(width_minus_last / max_span) + 1


def oc_spacing(frame_width, lumber_width, n):
    return (frame_width - lumber_width) / (n - 1)


class Deck:

    def __init__(
            self,
            width,
            length,
            height,
            joist_thickness=SIX,
            joist_width=TWO,
            max_spacing=16,
            joist_overhang=ft(2),
            beam_thickness=EIGHT,
            beam_width=FOUR,
            beam_overhang=ft(2),
            decking_thickness=ONE
    ):
        self.width = width
        self.length = length
        self.height = height
        self.joist_thickness = joist_thickness
        self.joist_width = joist_width
        self.max_spacing = max_spacing
        self.joist_overhang = joist_overhang
        self.beam_thickness = beam_thickness
        self.beam_width = beam_width
        self.beam_overhang = beam_overhang
        self.decking_thickness = decking_thickness

    @property
    def n_joist_spans(self):
        return 1

    @property
    def joist_len(self):
        return self.length

    @property
    def row_offset(self):
        return 0

    @property
    def n_joists(self):
        return n_members(self.width, lumber_width=TWO, max_span=self.max_spacing)

    @property
    def n_beams(self):
        return n_members(self.inner_length, self.beam_width, max_span=joist_spans[self.joist_thickness])

    @property
    def inner_length(self):
        return self.length - 2 * self.joist_overhang

    @property
    def joist_spacing(self):
        """Amount of space between joists."""
        return oc_spacing(self.width, self.joist_width, self.n_joists)

    @property
    def beam_spacing(self):
        """Amount of space between joists."""
        return oc_spacing(self.inner_length, self.beam_width, self.n_beams)

    @property
    def frame_height(self):
        return self.height - self.decking_thickness

    @property
    def beam_height(self):
        return self.frame_height - self.joist_thickness

    def frame(self):
        rim_joist = lumber(self.joist_width, self.joist_thickness)
        joist = lumber(self.joist_width, self.joist_thickness, orient_towards='y')
        f = rim_joist(self.width)
        row_position = self.row_offset
        for i in range(self.n_joist_spans):
            for j in range(0, self.n_joists):
                f += su.forward(row_position)(su.right(j * self.joist_spacing)(joist(self.joist_len)))
            row_position += self.joist_len + self.joist_width
            f += su.forward(row_position - self.joist_width)(rim_joist(self.width))

        return su.up(self.beam_height)(f)


class FlushBeamDeck(Deck):

    @property
    def n_joist_spans(self):
        return self.n_beams - 1

    @property
    def joist_len(self):
        return self.length / (self.n_beams - 1)

    @property
    def row_offset(self):
        return self.beam_width


class DeckJoistsOnBlocks(Deck):

    def blocks(self):
        b = []
        for i in range(self.n_beams):
            for j in range(1, self.n_joists - 1):
                b.append(
                    su.forward(i * self.beam_spacing + self.beam_overhang)(
                        su.right(j * self.joist_spacing + TWO / 2)(deck_block)
                    )
                )
        return sum(b)

    def all(self):
        return self.frame() + self.blocks()


deck_block = su.linear_extrude(height=7.75, scale=8/10.75)(s.square(10.75, center=True)) \
             - su.up(6 + FOUR / 2)(s.cube([12, TWO, FOUR], center=True)) \
             - su.up(6 + FOUR / 2)(s.cube([TWO, 12, FOUR], center=True)) \
             - su.up(6 + 1)(s.cube([FOUR, FOUR, 2], center=True))


if __name__ == '__main__':
    d = DeckJoistsOnBlocks(ft(20), ft(16), 6 + 5.5 + 0.75)
    foo = d.all()
