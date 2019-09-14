
from OCC.Display import qtDisplay
from OCC.Display.backend import get_qt_modules

QtCore, QtGui, QtWidgets, QtOpenGL = get_qt_modules()

class point(object):
    def __init__(self, obj=None):
        self.x = 0
        self.y = 0
        if obj is not None:
            self.set(obj)

    def set(self, obj):
        self.x = obj.x()
        self.y = obj.y()

class MyqtViewer3d(qtDisplay.qtViewer3d):
    " Modify qtViewer3d to emit signals"

    def mousePressEvent(self, event):
        self.emit(QtCore.SIGNAL("LMBPressed"))
        #print 'LMBPressed signal emitted.'
        self.setFocus()
        self.dragStartPos = point(event.pos())
        self._display.StartRotation(self.dragStartPos.x, self.dragStartPos.y)

    def mouseReleaseEvent(self, event):
        self.emit(QtCore.SIGNAL("LMBReleased"))
        #print 'LMBReleased signal emitted.'
        pt = point(event.pos())
        modifiers = event.modifiers()

        if event.button() == QtCore.Qt.LeftButton:
            pt = point(event.pos())
            if self._select_area:
                [Xmin, Ymin, dx, dy] = self._drawbox
                self._display.SelectArea(Xmin, Ymin, Xmin + dx, Ymin + dy)
                self._select_area = False
            else:
                # multiple select if shift is pressed
                if modifiers == QtCore.Qt.ShiftModifier:
                    self._display.ShiftSelect(pt.x, pt.y)
                else:
                    # single select otherwise
                    self._display.Select(pt.x, pt.y)
        elif event.button() == QtCore.Qt.RightButton:
            if self._zoom_area:
                [Xmin, Ymin, dx, dy] = self._drawbox
                self._display.ZoomArea(Xmin, Ymin, Xmin + dx, Ymin + dy)
                self._zoom_area = False
