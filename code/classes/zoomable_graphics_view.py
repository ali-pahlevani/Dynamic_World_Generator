from PyQt5.QtWidgets import QGraphicsView, QLabel
from PyQt5.QtCore import Qt, QPoint, QEvent


class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.scale_label = QLabel("1 pixel = 10 cm", self)
        self.scale_label.setStyleSheet("background: transparent; font-size: 11pt; font-weight: bold; color: red;")
        self.scale_label.adjustSize()
        self.scale_label.move(10, 10)

        # Same look as the map preview's coordinate label (background:
        # transparent + adjustSize, which gives it that thin bordered badge
        # appearance), anchored to the bottom-right corner.
        #
        # Parented to the view itself (NOT the viewport): QAbstractScrollArea
        # runs its own internal layout over the viewport's children (to manage
        # scrollbars/corner widgets), which fights with manually-set geometry
        # on any widget placed inside it, leaving it stranded mid-transition.
        # The view has no such layout, so instead we anchor the label to the
        # viewport's on-screen rectangle (`viewport().geometry()`, already in
        # the view's coordinate space) — that rectangle already excludes the
        # frame and scrollbars, so the badge can never overlap them or spill
        # outside the window.
        self.coord_label = QLabel("X: — | Y: —", self)
        self.coord_label.setStyleSheet("background: transparent; border: 1px solid #D5D8DC; font-size: 11pt; font-weight: bold; color: #2C3E50;")
        self.coord_label.adjustSize()
        self._reposition_coord_label()

        self.is_panning = False
        self.last_pan_point = QPoint()
        self.setMouseTracking(True)
        self.viewport().setMouseTracking(True)

    def _reposition_coord_label(self):
        self.coord_label.adjustSize()
        vp = self.viewport().geometry()
        self.coord_label.move(vp.x() + vp.width() - self.coord_label.width() - 30,
                              vp.y() + vp.height() - self.coord_label.height() - 8)

    def viewportEvent(self, event):
        if event.type() in (QEvent.Resize, QEvent.Move):
            self._reposition_coord_label()
        return super().viewportEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scale_label.adjustSize()
        self.scale_label.move(10, self.height() - self.scale_label.height() - 12)
        self._reposition_coord_label()

    def wheelEvent(self, event):
        zoom_factor = 1.25 if event.angleDelta().y() > 0 else 0.8
        self.scale(zoom_factor, zoom_factor)

    def mousePressEvent(self, event):
        if event.button() == Qt.MiddleButton:
            self.is_panning = True
            self.last_pan_point = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        scene_pos = self.mapToScene(event.pos())
        self.coord_label.setText(f"X: {scene_pos.x() / 100:.2f} | Y: {-scene_pos.y() / 100:.2f}")
        self._reposition_coord_label()

        if self.is_panning:
            # Delta in view (pixel) coordinates so panning speed is zoom-invariant
            delta = event.pos() - self.last_pan_point
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
            self.last_pan_point = event.pos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        self.coord_label.setText("X: — | Y: —")
        self._reposition_coord_label()
        super().leaveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)
