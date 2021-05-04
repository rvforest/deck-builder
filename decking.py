import math

from lumber import LumberFactory, LumberSize
from point import Dim, Point3D
from shapes import ShapeCollection
from util import render_all, ft


class Decking:

    w2w_gap = 3 / 8
    e2e_gap = 1 / 8

    def __init__(self, width: float, length: float, board_cls: LumberFactory):
        self.width = width
        self.length = length
        self.board_cls = board_cls

    def shape(self) -> ShapeCollection:
        raise NotImplementedError

    @property
    def n_boards(self) -> int:
        return math.ceil(self.length / (self.board_cls.width + Decking.w2w_gap))


class SingleSpanDecking(Decking):

    def shape(self) -> ShapeCollection:
        board = self.board_cls
        boards = ShapeCollection([
            board(self.width, orient_towards=Dim.X, position=Point3D(
                x=0,
                y=i * (board.width + Decking.w2w_gap),
                z=0
            ))
            for i in range(self.n_boards)
        ])
        return boards


class StaggeredThirdsDecking(Decking):

    def shape(self) -> ShapeCollection:
        max_len = ft(16)
        board = self.board_cls
        boards = []
        for i in range(self.n_boards):
            thirds = 1 - (i % 3) / 3  # Value is either 1, 2/3, or 1/3
            len1 = thirds * max_len
            len2 = self.width - len1 - Decking.e2e_gap
            y_pos = i * (board.width + Decking.w2w_gap)
            boards.append(board(len1, orient_towards=Dim.X, position=Point3D(
                x=0,
                y=y_pos,
                z=0
            )))
            boards.append(board(len2, orient_towards=Dim.X, position=Point3D(
                x=len1 + Decking.e2e_gap,
                y=y_pos,
                z=0
            )))

        return ShapeCollection(boards)


if __name__ == '__main__':
    decking = StaggeredThirdsDecking(
        ft(20), ft(16),
        LumberFactory(LumberSize.SIX.value, LumberSize.ONE.value, draw_x=False)
    )
    render_all(decking.shape(), 'decking_test')
