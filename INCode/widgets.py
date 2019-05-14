# Copyright (C) 2018 R. Knuus
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QGraphicsView, QGraphicsScene, QGraphicsItem
from PyQt5.QtSvg import QGraphicsSvgItem, QSvgRenderer


class SvgView(QGraphicsView):
    def __init__(self, parent=None):
        super(SvgView, self).__init__(parent)
        self.setScene(QGraphicsScene(self))
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    def load_svg_content(self, content):
        s = self.scene()
        s.clear()
        self.resetTransform()
        item = QGraphicsSvgItem()
        item.setSharedRenderer(QSvgRenderer(content))
        item.setFlags(QGraphicsItem.ItemClipsToShape)
        item.setCacheMode(QGraphicsItem.NoCache)
        item.setZValue(0)
        s.addItem(item)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            super().wheelEvent(event)
        else:
            factor = pow(1.2, event.angleDelta().y() / 240.0)
            self.scale(factor, factor)
        event.accept()
