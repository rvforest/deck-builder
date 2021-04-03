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
            joist_height=EIGHT,
            joist_width=TWO,
            max_spacing=16,
            joist_overhang=ft(2),
            beam_height=EIGHT,
            beam_width=FOUR,
            beam_overhang=ft(2)
    ):
        self.width = width
        self.length = length
        self.joist_height = joist_height
        self.joist_width = joist_width
        self.max_spacing = max_spacing
        self.joist_overhang = joist_overhang
        self.beam_height = beam_height
        self.beam_width = beam_width
        self.beam_overhang = beam_overhang

    @property
    def n_joists(self):
        return n_members(self.width, lumber_width=TWO, max_span=self.max_spacing)

    @property
    def n_beams(self):
        return n_members(self.inner_length, self.beam_width, max_span=joist_spans[self.joist_height])

    @property
    def inner_length(self):
        return self.length - 2 * self.joist_overhang

    def frame(self):
        return self._frame(n_joist_spans=1, joist_len=self.length)

    @property
    def joist_spacing(self):
        """Amount of space between joists."""
        return oc_spacing(self.width, self.joist_width, self.n_joists)

    @property
    def beam_spacing(self):
        """Amount of space between joists."""
        return oc_spacing(self.inner_length, self.beam_width, self.n_beams)

    def _frame(self, n_joist_spans, joist_len, row_offset=0.0):
        rim_joist = lumber(self.joist_width, self.joist_height, orient_towards='y')
        joist = lumber(self.joist_width, self.joist_height)
        f = rim_joist(self.width)
        row_position = row_offset
        for i in range(n_joist_spans):
            for j in range(0, self.n_joists):
                f += su.right(row_position)(su.forward(j * self.joist_spacing)(joist(joist_len)))
            row_position += joist_len + self.joist_width
            f += su.right(row_position - self.joist_width)(rim_joist(self.width))

        return f


class FlushBeamDeck(Deck):

    def frame(self):
        joist_len = self.length / (self.n_beams - 1)
        return self._frame(self.n_beams - 1, joist_len, row_offset=self.beam_width)


deck_block = su.linear_extrude(height=7.75, scale=8/10.75)(s.square(10.75, center=True)) \
             - su.up(8)(s.cube([12, 1.5, 4], center=True)) \
             - su.up(8)(s.cube([1.5, 12, 4], center=True)) \
             - su.up(7)(s.cube([3.5, 3.5, 2], center=True))


if __name__ == '__main__':
    d = FlushBeamDeck(ft(20), ft(16))
    foo = d.frame()
