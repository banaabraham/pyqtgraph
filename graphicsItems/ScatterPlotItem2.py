from pyqtgraph.Qt import QtGui, QtCore
from pyqtgraph.Point import Point
import pyqtgraph.functions as fn
from .GraphicsItem import GraphicsItem
from .GraphicsObject import GraphicsObject
import numpy as np
import scipy.stats
import weakref
import pyqtgraph.debug as debug
from collections import OrderedDict
from ScatterPlotItem import ScatterPlotItem, SpotItem
#import pyqtgraph as pg 

__all__ = ['ScatterPlotItem2', 'SpotItem2']


## Build all symbol paths
Symbols = OrderedDict([(name, QtGui.QPainterPath()) for name in ['o', 's', 't', 'd', '+']])
Symbols['o'].addEllipse(QtCore.QRectF(-0.5, -0.5, 1, 1))
Symbols['s'].addRect(QtCore.QRectF(-0.5, -0.5, 1, 1))
coords = {
    't': [(-0.5, -0.5), (0, 0.5), (0.5, -0.5)],
    'd': [(0., -0.5), (-0.4, 0.), (0, 0.5), (0.4, 0)],
    '+': [
        (-0.5, -0.05), (-0.5, 0.05), (-0.05, 0.05), (-0.05, 0.5),
        (0.05, 0.5), (0.05, 0.05), (0.5, 0.05), (0.5, -0.05), 
        (0.05, -0.05), (0.05, -0.5), (-0.05, -0.5), (-0.05, -0.05)
    ],
}
for k, c in coords.items():
    Symbols[k].moveTo(*c[0])
    for x,y in c[1:]:
        Symbols[k].lineTo(x, y)
    Symbols[k].closeSubpath()

# shape() and boundingRect() is used for picking, therefore it should provide
# the path of the actual item, i.e. the item geometry provided by the user.
# QGraphicsPixmapItem determines it from the pixmap (see shapeMode) or we
# provide it by overriding shape().

def makeSymbolPath(size, pen, brush, symbol):
    """Scales the symbol path to contain full pen width within given size."""
    shape = Symbols[symbol]
    shape = QtGui.QTransform.fromScale(size, size).map(shape)
    penOffset = pen.width()
    wscale, hscale = (1.-penOffset/shape.boundingRect().width(),
                      1.-penOffset/shape.boundingRect().height())
    shape = QtGui.QTransform.fromScale(wscale, hscale).map(shape)
    return shape

def makeSymbolPixmap(size, pen, brush, symbol):
    ## Render a spot with the given parameters to a pixmap
    # the pixmap should have the given size (regarding picking)
    image = QtGui.QImage(size, size, QtGui.QImage.Format_ARGB32_Premultiplied)
    image.fill(0)
    p = QtGui.QPainter(image)
    p.setRenderHint(p.Antialiasing)
    p.translate(size*0.5, size*0.5) # QGraphicsPixmapItem.offset
    if pen.width() == 0.0: # cosmetic pen
        pen.setWidth(1.0)
    p.setPen(pen)
    p.setBrush(brush)
    p.drawPath(makeSymbolPath(size, pen, brush, symbol))
    p.end()
    return QtGui.QPixmap(image)

class ScatterPlotItem2(ScatterPlotItem):
    """
    Displays a set of x/y points. Instances of this class are created
    automatically as part of PlotDataItem; these rarely need to be instantiated
    directly.
    
    The size, shape, pen, and fill brush may be set for each point individually 
    or for all points. 
    
    
    ========================  ===============================================
    **Signals:**
    sigPlotChanged(self)      Emitted when the data being plotted has changed
    sigClicked(self, points)  Emitted when the curve is clicked. Sends a list
                              of all the points under the mouse pointer.
    ========================  ===============================================
    
    """
    #sigPointClicked = QtCore.Signal(object, object)
    sigClicked = QtCore.Signal(object, object)  ## self, points
    sigPlotChanged = QtCore.Signal(object)
    
    def __init__(self, *args, **kargs):
        """
        Accepts the same arguments as setData()
        """
        prof = debug.Profiler('ScatterPlotItem.__init__', disabled=True)
        ScatterPlotItem.__init__(self)
        self.setFlag(self.ItemHasNoContents, True)
        self.data = np.empty(0, dtype=[('x', float), ('y', float), ('size', float), ('symbol', 'S1'), ('pen', object), ('brush', object), ('item', object), ('data', object)])
        #self.spots = []
        #self.fragments = None
        self.bounds = [None, None]
        self.opts = {'pxMode': True}
        #self.spotsValid = False
        #self.itemsValid = False
        self._spotPixmap = None
        
        self.setPen(200,200,200, update=False)
        self.setBrush(100,100,150, update=False)
        self.setSymbol('o', update=False)
        self.setSize(7, update=False)
        #self.setIdentical(False, update=False)
        prof.mark('1')
        self.setData(*args, **kargs)
        prof.mark('setData')
        prof.finish()
        
    def addPoints(self, *args, **kargs):
        """
        Add new points to the scatter plot. 
        Arguments are the same as setData()
        """
        
        ## deal with non-keyword arguments
        if len(args) == 1:
            kargs['spots'] = args[0]
        elif len(args) == 2:
            kargs['x'] = args[0]
            kargs['y'] = args[1]
        elif len(args) > 2:
            raise Exception('Only accepts up to two non-keyword arguments.')
        
        ## convert 'pos' argument to 'x' and 'y'
        if 'pos' in kargs:
            pos = kargs['pos']
            if isinstance(pos, np.ndarray):
                kargs['x'] = pos[:,0]
                kargs['y'] = pos[:,1]
            else:
                x = []
                y = []
                for p in pos:
                    if isinstance(p, QtCore.QPointF):
                        x.append(p.x())
                        y.append(p.y())
                    else:
                        x.append(p[0])
                        y.append(p[1])
                kargs['x'] = x
                kargs['y'] = y
        
        ## determine how many spots we have
        if 'spots' in kargs:
            numPts = len(kargs['spots'])
        elif 'y' in kargs and kargs['y'] is not None:
            numPts = len(kargs['y'])
        else:
            kargs['x'] = []
            kargs['y'] = []
            numPts = 0
        
        ## Extend record array
        oldData = self.data
        self.data = np.empty(len(oldData)+numPts, dtype=self.data.dtype)
        ## note that np.empty initializes object fields to None and string fields to ''
        
        self.data[:len(oldData)] = oldData
        for i in range(len(oldData)):
            oldData[i]['item']._data = self.data[i]  ## Make sure items have proper reference to new array
            
        newData = self.data[len(oldData):]
        newData['size'] = -1  ## indicates to use default size
        
        if 'spots' in kargs:
            spots = kargs['spots']
            for i in range(len(spots)):
                spot = spots[i]
                for k in spot:
                    #if k == 'pen':
                        #newData[k] = fn.mkPen(spot[k])
                    #elif k == 'brush':
                        #newData[k] = fn.mkBrush(spot[k])
                    if k == 'pos':
                        pos = spot[k]
                        if isinstance(pos, QtCore.QPointF):
                            x,y = pos.x(), pos.y()
                        else:
                            x,y = pos[0], pos[1]
                        newData[i]['x'] = x
                        newData[i]['y'] = y
                    elif k in ['x', 'y', 'size', 'symbol', 'pen', 'brush', 'data']:
                        newData[i][k] = spot[k]
                    #elif k == 'data':
                        #self.pointData[i] = spot[k]
                    else:
                        raise Exception("Unknown spot parameter: %s" % k)
        elif 'y' in kargs:
            newData['x'] = kargs['x']
            newData['y'] = kargs['y']
        
        if 'pxMode' in kargs:
            self.setPxMode(kargs['pxMode'], update=False)
            
        ## Set any extra parameters provided in keyword arguments
        for k in ['pen', 'brush', 'symbol', 'size', 'toolTips']:
            if k in kargs:
                setMethod = getattr(self, 'set' + k[0].upper() + k[1:])
                setMethod(kargs[k], update=False, dataSet=newData)
        
        if 'data' in kargs:
            self.setPointData(kargs['data'], dataSet=newData)
        
        #self.updateSpots()
        self.generateSpotItems()
        self.sigPlotChanged.emit(self)
        
        
    def setToolTips(self, toolTips, **kargs):
        update = kargs.pop('update', True)
        dataSet = kargs.pop('dataSet', self.data)
        self.opts['toolTips'] = toolTips
        if update:
            self.updateSpots(dataSet)

    def updateSpots(self, dataSet=None):
        if dataSet is None:
            dataSet = self.data
        for spot in dataSet['item']:
            spot.updateItem()
        
    def dataBounds(self, ax, frac=1.0, orthoRange=None):
        if frac >= 1.0 and self.bounds[ax] is not None:
            return self.bounds[ax]
        
        if self.data is None or len(self.data) == 0:
            return (None, None)
        
        if ax == 0:
            d = self.data['x']
            d2 = self.data['y']
        elif ax == 1:
            d = self.data['y']
            d2 = self.data['x']
        
        if orthoRange is not None:
            mask = (d2 >= orthoRange[0]) * (d2 <= orthoRange[1])
            d = d[mask]
            d2 = d2[mask]
            
        if frac >= 1.0:
            minIndex = np.argmin(d)
            maxIndex = np.argmax(d)
            minVal = d[minIndex]
            maxVal = d[maxIndex]
            if not self.opts['pxMode']:
                minVal -= self.data[minIndex]['size']
                maxVal += self.data[maxIndex]['size']
            self.bounds[ax] = (minVal, maxVal)
            return self.bounds[ax]
        elif frac <= 0.0:
            raise Exception("Value for parameter 'frac' must be > 0. (got %s)" % str(frac))
        else:
            return (scipy.stats.scoreatpercentile(d, 50 - (frac * 50)), scipy.stats.scoreatpercentile(d, 50 + (frac * 50)))
            
    def defaultSpotPixmap(self):
        ## Return the default spot pixmap
        if self._spotPixmap is None:
            self._spotPixmap = makeSymbolPixmap(size=self.opts['size'], brush=self.opts['brush'], pen=self.opts['pen'], symbol=self.opts['symbol'])
        return self._spotPixmap

    def boundingRect(self):
        (xmn, xmx) = self.dataBounds(ax=0)
        (ymn, ymx) = self.dataBounds(ax=1)
        if xmn is None or xmx is None:
            xmn = 0
            xmx = 0
        if ymn is None or ymx is None:
            ymn = 0
            ymx = 0
        # the bounding rect includes the spot geometries completely
        br = QtCore.QRectF(xmn, ymn, xmx-xmn, ymx-ymn)
        if self.opts['pxMode'] and len(self.data) > 0:
                # increase scatterplot bounding rect by scale invariant
                # spot item bounding rect size at the boundary
                size = self.mapFromScene(self.data[0]['item']
                                .boundingRect()).boundingRect()
                br.adjust(-size.width()*.5, -size.height()*.5,
                           size.width()*.5,  size.height()*.5)
        return br
        
class SpotItem2(SpotItem):
    """
    Class referring to individual spots in a scatter plot.
    These can be retrieved by calling ScatterPlotItem.points() or 
    by connecting to the ScatterPlotItem's click signals.
    """

    def __init__(self, data, plot):
        SpotItem.__init__(self, register=False)
        self._data = data
        self._plot = plot
        #self._viewBox = None
        #self._viewWidget = None
        self.setParentItem(plot)
        self.setPos(QtCore.QPointF(data['x'], data['y']))
        # set individual tooltip if provided
        tooltip = self._plot.opts.get('toolTips', None)
        if tooltip is not None:
            self.setToolTip(tooltip.arg(self.pos().x()).arg(self.pos().y()))
        self.updateItem()
    
class PixmapSpotItem2(SpotItem2, QtGui.QGraphicsPixmapItem):
    def __init__(self, data, plot):
        QtGui.QGraphicsPixmapItem.__init__(self)
        self.setFlags(self.flags() | self.ItemIgnoresTransformations)
        SpotItem2.__init__(self, data, plot)
        # for a transparent brush, picking works only on the pen in default shape mode
        self.setShapeMode(self.BoundingRectShape)
    
    def setPixmap(self, pixmap):
        QtGui.QGraphicsPixmapItem.setPixmap(self, pixmap)
        self.setOffset(-pixmap.width()*.5, -pixmap.height()*.5)
    
    def mapToScene(self, shape):
        """
        The pixmap item is scale invariant, translates only.
        Related to picking and QGraphicsScene.items(pos).
        For large asymmetric scaling factors (e.g. 1:1e5) the
        ScatterPlotItem.boundingRect() used for picking in QGraphicsScene.items()
        vanishes. This reimplementation ensures that scale invariant SpotItems
        are still pickable in this case.
        """
        mappedShape = QtGui.QGraphicsPixmapItem.mapToScene(self, shape)
        offset = (mappedShape.boundingRect().center() -
                  shape.boundingRect().center())
        return shape.translated(offset)

class PathSpotItem(SpotItem2, QtGui.QGraphicsPathItem):
    def __init__(self, data, plot):
        QtGui.QGraphicsPathItem.__init__(self)
        SpotItem2.__init__(self, data, plot)

    def updateItem(self):
        QtGui.QGraphicsPathItem.setPath(self, makeSymbolPath(
                self.size(), self.pen(), self.brush(), self.symbol()))
        QtGui.QGraphicsPathItem.setPen(self, self.pen())
        QtGui.QGraphicsPathItem.setBrush(self, self.brush())
