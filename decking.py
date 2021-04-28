import math

from lumber import LumberFactory, LumberSize
from point import Dim, Point3D
from shapes import ShapeCollection
from util import render_all, ft


class Decking:

    w2w_gap = 0.2
    e2e_gap = 0.2

    def __init__(self, width: float, length: float, board_cls: LumberFactory):
        self.width = width
        self.length = length
        self.board_cls = board_cls

    def all(self) -> ShapeCollection:
        raise NotImplementedError


class SingleSpanDecking(Decking):

    def all(self) -> ShapeCollection:
        board = self.board_cls
        n_boards = math.ceil(self.length / (board.width + Decking.w2w_gap))
        boards = ShapeCollection([
            board(self.width, orient_towards=Dim.X, position=Point3D(
                x=0,
                y=i * (board.width + Decking.w2w_gap),
                z=0
            ))
            for i in range(n_boards)
        ])
        return boards


if __name__ == '__main__':
    decking = SingleSpanDecking(
        ft(20), ft(16),
        LumberFactory(LumberSize.SIX.value, LumberSize.ONE.value, draw_x=False)
    )
    render_all(decking.all(), 'decking_test')
