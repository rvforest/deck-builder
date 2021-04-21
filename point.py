from __future__ import annotations
from enum import Enum
from typing import Tuple, TypeVar, Union

T = TypeVar('T')


class Dim(Enum):
    X = 0
    Y = 1
    Z = 2


class NDPoint:

    @property
    def ndim(self) -> int:
        raise NotImplementedError

    @property
    def _dim_vals(self) -> Tuple[float, ...]:
        raise NotImplementedError

    def __iter__(self) -> float:
        yield from self._dim_vals

    def __getitem__(self, item: Union[int, Dim]) -> float:
        if isinstance(item, Dim):
            item = item.value
        return self._dim_vals[item]

    def __add__(self: T, other: T) -> T:
        if self.ndim != other.ndim:
            raise ValueError(
                f"Points must be of the same dimension for addition. "
                f"Left point is dim {self.ndim} and right point is dim {other.ndim}"
            )
        results = []
        for a, b in zip(self, other):
            results.append(a + b)
        return type(self)(*results)

    def __rmul__(self: T, other: float) -> T:
        results = (other * val for val in self)
        return type(self)(*results)

    def __sub__(self: T, other: T) -> T:
        if self.ndim != other.ndim:
            raise ValueError(
                f"Points must be of the same dimension for subtraction. "
                f"Left point is dim {self.ndim} and right point is dim {other.ndim}"
            )
        results = []
        for a, b in zip(self, other):
            results.append(a - b)
        return type(self)(*results)

    def __len__(self) -> int:
        return self.ndim

    def __contains__(self, item):
        for val in self:
            if val == item:
                return True
        return False


class Point3D(NDPoint):

    ndim = 3

    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    @property
    def _dim_vals(self) -> Tuple[float, float, float]:
        return self.x, self.y, self.z

    def get_2d_point(self, exclude_dim: Dim) -> Point2D:
        keep_dims = [self[d] for d in Dim if d != exclude_dim]
        return Point2D(*keep_dims)


class Point2D(NDPoint):

    ndim = 2

    def __init__(self, i: float, j: float):
        self.i = i
        self.j = j

    @property
    def _dim_vals(self) -> Tuple[float, float]:
        return self.i, self.j
