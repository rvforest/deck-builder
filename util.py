from abc import abstractmethod
from typing import Protocol

import ezdxf
from ezdxf.layouts import Modelspace

from shapes import Dim


def ft(f):
    return 12 * f


class DXFWritable(Protocol):

    @abstractmethod
    def render_dxf(self, plane: Dim, msp: Modelspace):
        raise NotImplementedError


def write_dxf_doc(obj: DXFWritable, plane: Dim, filename: str):
    doc = ezdxf.new(dxfversion='AC1024')
    modelspace = doc.modelspace()
    obj.render_dxf(plane, modelspace)
    doc.saveas(filename)
