from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Tuple



class Dim(Enum):
    X = 0
    Y = 1
    Z = 2


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

    def get_2d_point(self, exclude_dim: Dim) -> Tuple[float, float]:
        keep_dims = [self[d] for d in Dim if d != exclude_dim]
        return tuple(*keep_dims)
