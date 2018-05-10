# Copyright (C) 2018 R. Knuus

#############################################################################
##
## Copyright (C) 2017 Riverbank Computing Limited.
## Copyright (C) 2010 Nokia Corporation and/or its subsidiary(-ies).
## All rights reserved.
##
## This file was part of the examples of PyQt.
##
## $QT_BEGIN_LICENSE:BSD$
## You may use this file under the terms of the BSD license as follows:
##
## "Redistribution and use in source and binary forms, with or without
## modification, are permitted provided that the following conditions are
## met:
##   * Redistributions of source code must retain the above copyright
##     notice, this list of conditions and the following disclaimer.
##   * Redistributions in binary form must reproduce the above copyright
##     notice, this list of conditions and the following disclaimer in
##     the documentation and/or other materials provided with the
##     distribution.
##   * Neither the name of Nokia Corporation and its Subsidiary(-ies) nor
##     the names of its contributors may be used to endorse or promote
##     products derived from this software without specific prior written
##     permission.
##
## THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
## "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
## LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
## A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
## OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
## SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
## LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
## DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
## THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
## (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
## OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE."
## $QT_END_LICENSE$
##
#############################################################################

from INCode.ui_diagramconfiguration import Ui_DiagramConfiguration
from PyQt5.QtCore import QAbstractItemModel, QFile, QIODevice, QItemSelectionModel, QModelIndex, Qt
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog, QMainWindow


class TreeItem(object):
    def __init__(self, data, parent=None):
        self.parent_ = parent
        self.data_ = data
        self.children_ = []

    def child(self, row):
        if row >= self.childCount():
            return None
        return self.children_[row]

    def childCount(self):
        return len(self.children_)

    def childNumber(self):
        if self.parent_ != None:
            return self.parent_.children_.index(self)
        return 0

    def columnCount(self):
        return len(self.data_)

    def data(self, column):
        if column >= self.columnCount():
            return None
        return self.data_[column]

    def insertChildren(self, position, count, columns):
        if position < 0 or position > self.childCount():
            return False

        for row in range(count):
            data = [None for v in range(columns)]
            item = TreeItem(data, self)
            self.children_.insert(position, item)

        return True

    def insertColumns(self, position, columns):
        if position < 0 or position > self.columnCount():
            return False

        for column in range(columns):
            self.data_.insert(position, None)

        for child in self.children_:
            child.insertColumns(position, columns)

        return True

    def parent(self):
        return self.parent_

    def removeChildren(self, position, count):
        if position < 0 or position + count > self.childCount():
            return False

        for row in range(count):
            self.children_.pop(position)

        return True

    def removeColumns(self, position, columns):
        if position < 0 or position + columns > self.columnCount():
            return False

        for column in range(columns):
            self.data_.pop(position)

        for child in self.children_:
            child.removeColumns(position, columns)

        return True

    def setData(self, column, value):
        if column < 0 or column >= self.columnCount():
            return False

        self.data_[column] = value

        return True


class TreeModel(QAbstractItemModel):
    def __init__(self, headers, data, parent=None):
        super(TreeModel, self).__init__(parent)

        root_data = [header for header in headers]
        self.root_item_ = TreeItem(root_data)
        self.setupModelData(data, self.root_item_)

    def columnCount(self, parent=QModelIndex()):
        return self.root_item_.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return None

        if role != Qt.DisplayRole and role != Qt.EditRole:
            return None

        item = self.getItem(index)
        if not item:
            return None
        callable = item.data(index.column())
        if not callable:
            return None
        return callable.get_name()

    def getItem(self, index):
        if index.isValid():
            item = index.internalPointer()
            if item:
                return item

        return self.root_item_

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.root_item_.data(section)

        return None

    def index(self, row, column, parent=QModelIndex()):
        if parent.isValid() and parent.column() != 0:
            return QModelIndex()

        parent_item = self.getItem(parent)
        child_item = parent_item.child(row)
        if child_item:
            return self.createIndex(row, column, child_item)
        else:
            return QModelIndex()

    def insertColumns(self, position, columns, parent=QModelIndex()):
        self.beginInsertColumns(parent, position, position + columns - 1)
        success = self.root_item_.insertColumns(position, columns)
        self.endInsertColumns()

        return success

    def insertRows(self, position, rows, parent=QModelIndex()):
        parent_item = self.getItem(parent)
        self.beginInsertRows(parent, position, position + rows - 1)
        success = parent_item.insertChildren(position, rows, self.root_item_.columnCount())
        self.endInsertRows()

        return success

    def parent(self, index):
        if not index.isValid():
            return QModelIndex()

        child_item = self.getItem(index)
        parent_item = child_item.parent()

        if parent_item == self.root_item_:
            return QModelIndex()

        return self.createIndex(parent_item.childNumber(), 0, parent_item)

    def removeColumns(self, position, columns, parent=QModelIndex()):
        self.beginRemoveColumns(parent, position, position + columns - 1)
        success = self.root_item_.removeColumns(position, columns)
        self.endRemoveColumns()

        if self.root_item_.columnCount() == 0:
            self.removeRows(0, self.rowCount())

        return success

    def removeRows(self, position, rows, parent=QModelIndex()):
        parent_item = self.getItem(parent)

        self.beginRemoveRows(parent, position, position + rows - 1)
        success = parent_item.removeChildren(position, rows)
        self.endRemoveRows()

        return success

    def rowCount(self, parent=QModelIndex()):
        parent_item = self.getItem(parent)

        return parent_item.childCount()

    def setData(self, index, value, role=Qt.EditRole):
        item = self.getItem(index)
        result = item.setData(index.column(), value)

        if result:
            self.dataChanged.emit(index, index)

        return result

    def setHeaderData(self, section, orientation, value, role=Qt.EditRole):
        if role != Qt.EditRole or orientation != Qt.Horizontal:
            return False

        result = self.root_item_.setData(section, value)
        if result:
            self.headerDataChanged.emit(orientation, section, section)

        return result

    def setupModelData(self, entries, parent):
        for nodeData, children in entries:
            parent.insertChildren(parent.childCount(), 1, self.root_item_.columnCount())
            node = parent.child(parent.childCount() - 1)
            node.setData(0, nodeData)
            self.setupModelData(children, node)


class DiagramConfiguration(QMainWindow, Ui_DiagramConfiguration):
    def __init__(self, index, entry_point_item, parent=None):
        super(DiagramConfiguration, self).__init__(parent)
        self.index_ = index
        entry_point = entry_point_item.get_callable()

        self.setupUi(self)

        # TODO(KNR): known issue: cannot handle recursion...
        want_to_get_rid_of_headers = [""]
        data = [(entry_point, [(child, []) for child in entry_point.get_referenced_callables()])]
        model = TreeModel(want_to_get_rid_of_headers, data)
        self.view_.setModel(model)
        self.view_.header().hide()
        self.view_.expandAll()
        for column in range(model.columnCount()):
            self.view_.resizeColumnToContents(column)

        self.exitAction_.triggered.connect(QApplication.instance().quit)

        self.view_.selectionModel().selectionChanged.connect(self.updateActions)

        self.actionsMenu_.aboutToShow.connect(self.updateActions)
        self.revealChildrenAction_.triggered.connect(self.revealChildren)

        self.updateActions()

    def revealChildren(self):
        model = self.view_.model()
        index = self.view_.selectionModel().currentIndex()

        # if model.columnCount(index) == 0:
        #     if not model.insertColumn(0, index):
        #         return

        callable = model.getItem(index).data(0)
        if not callable.is_definition():
            callable = self.index_.load_definition(callable)
            if not callable.is_definition():
                return

        for referenced_callable in callable.get_referenced_callables():
            if not model.insertRow(0, index):
                return

            for column in range(model.columnCount(index)):
                child = model.index(0, column, index)
                print('adding child', referenced_callable.get_name())
                model.setData(child, referenced_callable, Qt.DisplayRole)

        self.view_.selectionModel().setCurrentIndex(model.index(0, 0, index), QItemSelectionModel.ClearAndSelect)
        self.updateActions()

    def updateActions(self):
        hasSelection = not self.view_.selectionModel().selection().isEmpty()
        index = self.view_.selectionModel().currentIndex()
        hasNoChildren = (self.view_.model().getItem(index).childCount() == 0)
        self.revealChildrenAction_.setEnabled(hasSelection and hasNoChildren)

        hasCurrent = index.isValid()
        if hasCurrent:
            self.view_.closePersistentEditor(index)

            row = index.row()
            column = index.column()
            if index.parent().isValid():
                self.statusBar().showMessage("Position: (%d,%d)" % (row, column))
            else:
                self.statusBar().showMessage("Position: (%d,%d) in top level" % (row, column))
