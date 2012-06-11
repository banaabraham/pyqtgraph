from pyqtgraph.Qt import QtGui
from ScatterPlotItem import ScatterPlotItem, PathSpotItem, Symbols, coords, makeSymbolPixmap

__all__ = ['ErrorBarPlotItem']

## Build all symbol paths
KEY = 'b'
Symbols[KEY] = QtGui.QPainterPath()
coords[KEY] = [ # bar, like H rotated
        (-0.5, -0.5), (0., -0.5), (0., 0.5), (-0.5, 0.5),
        (0.5, 0.5), (0., 0.5), (0., -0.5), (0.5, -0.5) ]

k, c = KEY, coords[KEY]
Symbols[k].moveTo(*c[0])
for x,y in c[1:]:
    Symbols[k].lineTo(x, y)
Symbols[k].closeSubpath()

class ErrorBarPlotItem(ScatterPlotItem):
    
    def generateSpotItems(self):
        """use a SpotItem which scales only in y individually"""
        for rec in self.data:
            if rec['item'] is None:
                rec['item'] = BarSpotItem(rec, self)
        self.measureSpotSizes(self.data)
        self.sigPlotChanged.emit(self)

class BarSpotItem(PathSpotItem):
    """Scales in y direction only"""
    def __init__(self, *args, **kwargs):
        PathSpotItem.__init__(self, *args, **kwargs)

    def updateItem(self):
        PathSpotItem.updateItem(self)
        self.resetTransform()
        self.scale(1.0, self.size())
