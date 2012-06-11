from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.Point import Point
import pyqtgraph.functions as fn
from .GraphicsItem import GraphicsItem
from .GraphicsObject import GraphicsObject
import numpy as np
import scipy.stats
import weakref
import pyqtgraph.debug as debug
from ScatterPlotItem import ScatterPlotItem, PathSpotItem, Symbols, coords, makeSymbolPixmap
from collections import OrderedDict

__all__ = ['ErrorBarPlotItem']

## Build all symbol paths
Symbols['b'] = QtGui.QPainterPath()
coords['b'] = [ # bar, like H rotated
        (-0.5, -0.5), (0., -0.5), (0., 0.5), (-0.5, 0.5),
        (0.5, 0.5), (0., 0.5), (0., -0.5), (0.5, -0.5) ]

for k, c in coords.items():
    Symbols[k].moveTo(*c[0])
    for x,y in c[1:]:
        Symbols[k].lineTo(x, y)
    Symbols[k].closeSubpath()

class ErrorBarPlotItem(ScatterPlotItem):
    
    def generateSpotItems(self):
        for rec in self.data:
            if rec['item'] is None:
                rec['item'] = BarSpotItem(rec, self)
        self.measureSpotSizes(self.data)
        self.sigPlotChanged.emit(self)

class BarSpotItem(PathSpotItem):
    def __init__(self, *args, **kwargs):
        PathSpotItem.__init__(self, *args, **kwargs)

    def updateItem(self):
        PathSpotItem.updateItem(self)
        self.resetTransform()
        self.scale(1.0, self.size())
