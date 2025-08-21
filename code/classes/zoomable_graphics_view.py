from PyQt5.QtWidgets import QGraphicsView, QLabel
from PyQt5.QtCore import Qt, QPointF

class ZoomableGraphicsView(QGraphicsView):
    def __init__(self, scene):
        super().__init__(scene)
        self.scale_label = QLabel("1 pixel = 10 cm", self)
        self.scale_label.setStyleSheet("background: transparent; font-size: 11pt; font-weight: bold; color: red;")
        self.scale_label.setGeometry(10, self.height() - 38, 105, 20)
        self.is_panning = False
        self.last_pan_point = QPointF()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.scale_label.move(10, self.height() - 38)

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
        if self.is_panning:
            delta = self.mapToScene(event.pos()) - self.mapToScene(self.last_pan_point)
            self.horizontalScrollBar().setValue(int(self.horizontalScrollBar().value() - delta.x()))
            self.verticalScrollBar().setValue(int(self.verticalScrollBar().value() - delta.y()))
            self.last_pan_point = event.pos()
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MiddleButton and self.is_panning:
            self.is_panning = False
            self.setCursor(Qt.ArrowCursor)
            event.accept()
        else:
            super().mouseReleaseEvent(event)