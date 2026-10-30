"""Modules for listing points in a path."""
from typing import List

from point import Point2D


def trace_rectangle(
        width: float,
        length: float,
        position: Point2D,
        center: bool = False,
        h_invert: bool = False
) -> List[Point2D]:
    """
    Get points of rectangle in order of path.

    :param width: Width of rectangle
    :param length: Length of rectangle
    :param position: Position of bottom left corner
    :param center: Is position based on center of object?
    :param h_invert: Inverts shape in horizontal direction
    :return:
    """
    rel_path = [
        Point2D(0, 0),
        Point2D(width, 0),
        Point2D(width, length),
        Point2D(0, length),
        Point2D(0, 0)
    ]
    if center:
        adj = Point2D(width / 2, length / 2)
    else:
        adj = Point2D(0, 0)

    if h_invert:
        rel_path = [point.h_invert() for point in rel_path]
        adj = adj.h_invert()

    result = [position + p - adj for p in rel_path]
    return result


def trace_square(side_len: float, position: Point2D, center: bool = False):
    return trace_rectangle(side_len, side_len, position, center)


def trace_isosceles_trapezoid(
        bottom_len: float,
        top_len: float,
        height: float,
        position: Point2D,
        center: bool = False,
        h_invert: bool = False
) -> List[Point2D]:
    """
    Get points of isosceles trapezoid  in order of path. Parallel sides are top and bottom.

    :param bottom_len: Length of bottom side
    :param top_len: Length of top side
    :param height: Height of trapezoid
    :param position: Position of bottom left corner
    :param center: Is position based on center of object?
    :param h_invert: Inverts shape in horizontal direction
    :return:
    """
    rel_path = [
        Point2D(0, 0),
        Point2D(bottom_len, 0),
        Point2D(bottom_len - (bottom_len - top_len) / 2, height),
        Point2D((bottom_len - top_len) / 2, height),
        Point2D(0, 0)
    ]
    if center:
        adj = Point2D(bottom_len / 2, height / 2)
    else:
        adj = Point2D(0, 0)

    if h_invert:
        rel_path = [point.h_invert() for point in rel_path]
        adj = adj.h_invert()

    return [position + p - adj for p in rel_path]
