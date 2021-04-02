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
        obj = s.cube([length, h, w])
        rotate_axis = [0, 0, 0]
        if orient_towards == 'y':
            rotate_axis[Z] = 90
        elif orient_towards == 'z':
            rotate_axis[Y] = 90
        return su.rotate(rotate_axis)(obj)

    return inner


def n_members(length, lumber_width, max_span):
    width_minus_last = length - lumber_width
    return math.ceil(width_minus_last / max_span) + 1


def oc_spacing(frame_width, lumber_width, n_members):
    return (frame_width - lumber_width) / (n_members - 1)


def frame(
        width,
        length,
        joist_height=EIGHT,
        joist_width=TWO,
        max_spacing=16,
        joist_overhang=ft(2),
        beam_width=TWO
):
    # Specify lumber sizes
    joist = lumber(joist_width, joist_height)
    rim_joist = lumber(joist_width, joist_height, orient_towards='y')

    # Get spacing
    n_joists = n_members(width, lumber_width=TWO, max_span=max_spacing)
    spacing = oc_spacing(width, joist_width, n_joists)

    inner_length = length - 2 * joist_overhang
    n_beams = n_members(inner_length, beam_width, max_span=joist_spans[joist_height])
    # beam_spacing = oc_spacing(inner_length, lumber_width=TWO, n_members=n_beams)
    joist_len = length / (n_beams - 1)


    # Build the f
    f = rim_joist(width)
    row_position = beam_width
    for i in range(n_beams - 1):
        for j in range(0, n_joists):
            f += su.right(row_position)(su.forward(j * spacing)(joist(joist_len)))
        row_position += joist_len + joist_width
        f += su.right(row_position - joist_width)(rim_joist(width))

    return f


