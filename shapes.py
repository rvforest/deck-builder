from abc import abstractmethod
from dataclasses import dataclass
from itertools import product
from typing import List, Tuple, Protocol

from point import Dim, Point3D
from utils import xor


class Shape(Protocol):

    position: Point3D

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
    position: Point3D

    @property
    def bottom(self) -> List[Point3D]:
        return self._side(z=self.position.z)

    @property
    def top(self) -> List[Point3D]:
        return self._side(z=self.z_len)

    @property
    def back(self) -> List[Point3D]:
        return self._side(x=self.position.x)

    @property
    def front(self) -> List[Point3D]:
        return self._side(x=self.x_len)

    @property
    def left(self) -> List[Point3D]:
        return self._side(y=0)

    @property
    def right(self) -> List[Point3D]:
        return self._side(y=self.y_len)

    def get_path(self, face: str) -> List[Tuple[float, float, float]]:
        valid_vals = ('front', 'back', 'top', 'bottom', 'left', 'right')
        if face not in valid_vals:
            raise ValueError(f"Invalid value face='{face}'. Argument must be one of: {', '.join(valid_vals)}")
        points = getattr(self, face) + [self.position]
        return [point.as_tuple() for point in points]

    def get_2d_path(self, face: str) -> List[Tuple[float, float]]:
        exclude_dim = {
            'front': Dim.Y,
            'back': Dim.Y,
            'top': Dim.Z,
            'bottom': Dim.Z,
            'left': Dim.X,
            'right': Dim.X
        }
        valid_vals = list(exclude_dim.keys())
        if face not in valid_vals:
            raise ValueError(f"Invalid value face='{face}'. Argument must be one of: {', '.join(valid_vals)}")

        points = getattr(self, face) + [self.position]
        return [point.get_2d_point(exclude_dim[face]) for point in points]

    def _side(self, **kwargs) -> List[Point3D]:
        var_axes = list({'x', 'y', 'z'} - set((kwargs.keys())))
        result = []
        for i, j in product([False, True], repeat=2):
            dims = kwargs.copy()
            dims[var_axes[0]] = i * getattr(self, var_axes[0] + '_len')
            dims[var_axes[1]] = xor(i, j) * getattr(self, var_axes[1] + '_len')
            result.append(Point3D(**dims) + self.position)

        return result


if __name__ == '__main__':
    print(Cuboid(2, 6, 120, Point3D(1, 1, 0)).top)
    print(Cuboid(2, 6, 120, Point3D(1, 1, 0)).bottom)
    print(Cuboid(2, 6, 120, Point3D(1, 1, 0)).front)
    print(Cuboid(2, 6, 120, Point3D(1, 1, 0)).get_path('bottom'))
