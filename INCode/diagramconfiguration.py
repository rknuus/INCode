# Copyright (C) 2018 R. Knuus

from enum import IntEnum
from INCode.ui_diagramconfiguration import Ui_DiagramConfiguration
# from PyQt5.QtCore import QAbstractItemModel, QItemSelectionModel, QModelIndex, Qt
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem


class TreeColumns(IntEnum):
    FIRST_COLUMN = 0
    COLUMN_COUNT = 1


class CallableTreeItem(QTreeWidgetItem):
    def __init__(self, callable, parent=None):
        super(QTreeWidgetItem, self).__init__(parent)
        self.callable_ = callable
        self.setText(TreeColumns.FIRST_COLUMN, self.callable_.get_name())
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setCheckState(TreeColumns.FIRST_COLUMN, CallableTreeItem.get_check_state_(self.callable_))
        # TODO(KNR): probably prevent drag'n'drop operation

    def get_callable(self):
        return self.callable_

    def setData(self, column, role, value):
        if column == TreeColumns.FIRST_COLUMN and role == Qt.CheckStateRole:
            self.update_check_state_(value)
        super(CallableTreeItem, self).setData(column, role, value)

    @staticmethod
    def get_check_state_(callable):
        if callable.is_included():
            return Qt.Checked
        return Qt.Unchecked

    def update_check_state_(self, state):
        if state == Qt.Checked:
            print('include callable ', self.callable_.get_name())
            self.callable_.include()
        else:
            print('exclude callable ', self.callable_.get_name())
            self.callable_.exclude()

# class CallableTreeWidget(QTreeWidget):
#     pass


class DiagramConfiguration(QMainWindow, Ui_DiagramConfiguration):
    def __init__(self, index, entry_point_item, parent=None):
        super(DiagramConfiguration, self).__init__(parent)
        self.index_ = index
        entry_point = entry_point_item.get_callable()

        self.setupUi(self)
        # tree = CallableTreeWidget(self.tree_.parent())
        # tree.size = self.tree_.size
        # self.tree_ = tree

        # TODO(KNR): known issue: cannot handle recursion...
        self.tree_.setColumnCount(TreeColumns.COLUMN_COUNT)
        self.tree_.header().hide()
        # TODO(KNR): to store the root item as member of this class is a hack, the tree should somehow provide
        # this information
        self.entry_point_item_ = CallableTreeItem(entry_point, self.tree_)
        for child in entry_point.get_referenced_callables():
            CallableTreeItem(child, self.entry_point_item_)
        self.tree_.expandAll()
        for column in range(self.tree_.columnCount()):
            self.tree_.resizeColumnToContents(column)

        self.exitAction_.triggered.connect(QApplication.instance().quit)

        # self.view_.selectionModel().selectionChanged.connect(self.updateActions)

        # TODO(KNR): clean up
        self.actionsMenu_.aboutToShow.connect(self.updateActions)
        self.revealChildrenAction_.triggered.connect(self.revealChildren)
        self.exportAction_.triggered.connect(self.export)

        self.updateActions()

    # TODO(KNR): use lower case with underscores for method and variable names
    def revealChildren(self):
        current_item = self.tree_.currentItem()
        if not current_item:
            return
        callable = current_item.get_callable()
        if not callable.is_definition():
            callable = self.index_.load_definition(callable)
            if not callable.is_definition():
                return

        for child in callable.get_referenced_callables():
            CallableTreeItem(child, current_item)

    def export(self):
        # TODO(KNR): entry_point_item_ does not reflect updates when loading definitions later on
        callable = self.entry_point_item_.get_callable()
        print('exporting ', callable.get_name())
        print(callable.export())

    def updateActions(self):
        pass
        # hasSelection = not self.view_.selectionModel().selection().isEmpty()
        # index = self.view_.selectionModel().currentIndex()
        # hasNoChildren = (self.view_.model().getItem(index).childCount() == 0)
        # self.revealChildrenAction_.setEnabled(hasSelection and hasNoChildren)

        # hasCurrent = index.isValid()
        # if hasCurrent:
        #     self.view_.closePersistentEditor(index)

        #     row = index.row()
        #     column = index.column()
        #     if index.parent().isValid():
        #         self.statusBar().showMessage("Position: (%d,%d)" % (row, column))
        #     else:
        #         self.statusBar().showMessage("Position: (%d,%d) in top level" % (row, column))
