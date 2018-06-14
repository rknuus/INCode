# Copyright (C) 2018 R. Knuus

from enum import IntEnum
from INCode.ui_diagramconfiguration import Ui_DiagramConfiguration
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem


class TreeColumns(IntEnum):
    FIRST_COLUMN = 0
    COLUMN_COUNT = 1


class CallableTreeItem(QTreeWidgetItem):
    def __init__(self, callable, index, parent=None):
        super(QTreeWidgetItem, self).__init__(parent)
        self.index_ = index
        self.callable_id_ = callable.get_id()
        self.setText(TreeColumns.FIRST_COLUMN, callable.get_name())
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setCheckState(TreeColumns.FIRST_COLUMN, CallableTreeItem.get_check_state_(callable))
        # TODO(KNR): probably prevent drag'n'drop operation

    def get_callable(self):
        return self.index_.lookup(self.callable_id_)

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
        callable = self.index_.lookup(self.callable_id_)
        if state == Qt.Checked:
            callable.include()
        else:
            callable.exclude()


class DiagramConfiguration(QMainWindow, Ui_DiagramConfiguration):
    def __init__(self, index, entry_point_item, parent=None):
        super(DiagramConfiguration, self).__init__(parent)
        self.index_ = index
        entry_point = entry_point_item.get_callable()

        self.setupUi(self)

        self.tree_.setColumnCount(TreeColumns.COLUMN_COUNT)
        self.tree_.header().hide()
        # TODO(KNR): to store the root item as member of this class is a hack, the tree should somehow provide
        # this information
        self.entry_point_item_ = CallableTreeItem(entry_point, self.index_, self.tree_)
        for child in entry_point.get_referenced_callables():
            CallableTreeItem(child, self.index_, self.entry_point_item_)
        self.tree_.expandAll()
        for column in range(self.tree_.columnCount()):
            self.tree_.resizeColumnToContents(column)

        self.exitAction_.triggered.connect(QApplication.instance().quit)

        self.revealChildrenAction_.triggered.connect(self.revealChildren)
        self.exportAction_.triggered.connect(self.export)

    # TODO(KNR): use lower case with underscores for method and variable names
    def revealChildren(self):
        current_item = self.tree_.currentItem()
        if not current_item or current_item.childCount() > 0:
            return
        callable = current_item.get_callable()
        if not callable.is_definition():
            callable = self.index_.load_definition(callable)
            if not callable.is_definition():
                return  # TODO(KNR): really?

        for child in callable.get_referenced_callables():
            child.initialize()  # lazy load the referenced callables
            CallableTreeItem(child, self.index_, current_item)

    def export(self):
        callable = self.entry_point_item_.get_callable()
        print('exporting ', callable.get_name())
        print(callable.export())
