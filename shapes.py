from abc import abstractmethod
from typing import List, Protocol

from paths import trace_rectangle, trace_square, trace_isosceles_trapezoid
from point import Dim, Point3D, Point2D


class Shape(Protocol):
    position: Point3D

    @abstractmethod
    def get_2d_path(self, face: Dim) -> List[Point2D]:
        raise NotImplementedError


class Cuboid:

    def __init__(self, x_len: float, y_len: float, z_len: float, position: Point3D):
        self.x_len = x_len
        self.y_len = y_len
        self.z_len = z_len
        self.lengths = (x_len, y_len, z_len)
        self.position = position

    def get_2d_path(self, plane: Dim) -> List[Point2D]:
        args = [self.lengths[d.value] for d in Dim if d != plane]
        return trace_rectangle(args[0], args[1], self.position.get_2d_point(plane))


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
        return [point for point in points]

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
    pass
