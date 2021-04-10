from __future__ import annotations
from abc import abstractmethod
from dataclasses import dataclass
from itertools import product
from typing import List, Tuple, Protocol

from utils import xor

X = 0
Y = 1
Z = 2


@dataclass
class Point:
    x: float
    y: float
    z: float

    def __add__(self, other: Point):
        return Point(self.x + other.x, self.y + other.y, self.z + other.z)

    def __getitem__(self, item):
        vals = (self.x, self.y, self.z)
        return vals[item]

    def as_tuple(self) -> Tuple[float, float, float]:
        return self.x, self.y, self.z

    def drop_dim(self, dim: int) -> Tuple[float, float]:
        keep_dims = list({X, Y, Z} - {dim})
        return self[keep_dims[0]], self[keep_dims[1]]


class Shape(Protocol):

    position: Point

    @abstractmethod
    def get_path(self, face: str) -> List[Tuple[float, float, float]]:
        raise NotImplementedError

    @abstractmethod
    def get_2d_path(self, face: str) -> List[Tuple[float, float]]:
        raise NotImplementedError


@dataclass
class Cuboid:
    x_len: float
    y_len: float
    z_len: float
    position: Point

    @property
    def bottom(self) -> List[Point]:
        return self._side(z=self.position.z)

    @property
    def top(self) -> List[Point]:
        return self._side(z=self.z_len)

    @property
    def back(self) -> List[Point]:
        return self._side(x=self.position.x)

    @property
    def front(self) -> List[Point]:
        return self._side(x=self.x_len)

    @property
    def left(self) -> List[Point]:
        return self._side(y=0)

    @property
    def right(self) -> List[Point]:
        return self._side(y=self.y_len)

    def get_path(self, face: str) -> List[Tuple[float, float, float]]:
        valid_vals = ('front', 'back', 'top', 'bottom', 'left', 'right')
        if face not in valid_vals:
            raise ValueError(f"Invalid value face='{face}'. Argument must be one of: {', '.join(valid_vals)}")
        points = getattr(self, face) + [self.position]
        return [point.as_tuple() for point in points]

    def get_2d_path(self, face: str) -> List[Tuple[float, float]]:
        exclude_dim = {
            'front': Y,
            'back': Y,
            'top': Z,
            'bottom': Z,
            'left': X,
            'right': X
        }
        valid_vals = list(exclude_dim.keys())
        if face not in valid_vals:
            raise ValueError(f"Invalid value face='{face}'. Argument must be one of: {', '.join(valid_vals)}")

        points = getattr(self, face) + [self.position]
        return [point.drop_dim(exclude_dim[face]) for point in points]

    def _side(self, **kwargs) -> List[Point]:
        var_axes = list({'x', 'y', 'z'} - set((kwargs.keys())))
        result = []
        for i, j in product([False, True], repeat=2):
            dims = kwargs.copy()
            dims[var_axes[0]] = i * getattr(self, var_axes[0] + '_len')
            dims[var_axes[1]] = xor(i, j) * getattr(self, var_axes[1] + '_len')
            result.append(Point(**dims) + self.position)

        return result


if __name__ == '__main__':
    print(Cuboid(2, 6, 120, Point(1, 1, 0)).top)
    print(Cuboid(2, 6, 120, Point(1, 1, 0)).bottom)
    print(Cuboid(2, 6, 120, Point(1, 1, 0)).front)
    print(Cuboid(2, 6, 120, Point(1, 1, 0)).get_path('bottom'))
