from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple

from shapes import X, Y, Z


@dataclass
class Point3D:
    x: float
    y: float
    z: float

    def __add__(self, other: Point3D):
        return Point3D(self.x + other.x, self.y + other.y, self.z + other.z)

    def __getitem__(self, item):
        vals = (self.x, self.y, self.z)
        return vals[item]

    def as_tuple(self) -> Tuple[float, float, float]:
        return self.x, self.y, self.z

    def drop_dim(self, dim: int) -> Tuple[float, float]:
        keep_dims = list({X, Y, Z} - {dim})
        return self[keep_dims[0]], self[keep_dims[1]]