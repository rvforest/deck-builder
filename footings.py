from typing import Optional

from layers import Layer
from point import Point3D
from shapes import Shape, TrapezoidalPrism


class FootingFactory:

    height: float

    def __call__(self, position: Optional[Point3D] = None) -> Shape:
        raise NotImplementedError


class DeckBlockFactory(FootingFactory):

    def __init__(
            self,
            block_height: float = 7.75,
            block_slot_height: float = 6,
            block_base_len: float = 10.75,
            block_top_len: float = 8,
    ):
        self.block_height = block_height
        self.block_slot_height = block_slot_height
        self.block_base_len = block_base_len
        self.block_top_len = block_top_len

        self.height = block_slot_height
        self.block_scale = self.block_top_len / self.block_base_len

    def __call__(self, position: Optional[Point3D] = None) -> TrapezoidalPrism:
        return TrapezoidalPrism(
            bottom_square_len=self.block_base_len,
            top_square_len=self.block_top_len,
            height=self.block_height,
            position=position,
            layer=Layer.FOOTINGS,
            bottom_layer=Layer.FOOTINGS_BOTTOM,
            color=(0.5, 0.5, 0.5)
        )
