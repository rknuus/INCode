# Copyright (C) 2018 R. Knuus

from enum import IntEnum
from INCode.ui_diagramconfiguration import Ui_DiagramConfiguration
from PyQt5.QtCore import QModelIndex, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidget, QTreeWidgetItem

class TreeColumns(IntEnum):
    FIRST_COLUMN = 0
    COLUMN_COUNT = 1


class CallableTreeItem(QTreeWidgetItem):
    def __init__(self, callable, parent=None):
        super(QTreeWidgetItem, self).__init__(parent)

        if isinstance(parent, CallableTreeItem):
            parent.referenced_items_.append(self)
        self.index_ = callable.index_
        self.callable_id_ = callable.get_id()
        self.state_ = Qt.Unchecked
        self.sender_ = callable._get_sender(callable.cursor_)
        self.referenced_items_ = []
        self.setText(TreeColumns.FIRST_COLUMN, callable.get_name())
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setCheckState(TreeColumns.FIRST_COLUMN, self.get_check_state())
        # TODO(KNR): probably prevent drag'n'drop operation

    def get_callable(self):
        return self.index_.lookup(self.callable_id_)

    def setData(self, column, role, value):
        if column == TreeColumns.FIRST_COLUMN and role == Qt.CheckStateRole:
            self.update_check_state(value)
        super(CallableTreeItem, self).setData(column, role, value)

    def get_check_state(self):
        return self.state_

    def update_check_state(self, state):
        self.state_ = state

    def include(self):
        self.state_ = Qt.Checked

    def exclude(self):
        self.state_ = Qt.Unchecked

    def is_included(self):
        return self.state_ == Qt.Checked

    def export(self):
        callable = self.get_callable();
        sender = callable.get_translation_unit() if self.is_included() else ''
        return '@startuml\n\n{}\n@enduml'.format(self.export_relations_(sender))

    def export_relations_(self, parent_sender):
        diagram = ''
        for child_item in self.referenced_items_:
            child_callable = child_item.get_callable()
            sender = self.sender_ if self.is_included() else parent_sender
            if child_item.is_included():
                diagram += '{} -> {}: {}\n'.format(sender, child_callable.sender_, child_callable.get_name())
            diagram += child_item.export_relations_(sender)
        return diagram


class DiagramConfiguration(QMainWindow, Ui_DiagramConfiguration):
    def __init__(self, entry_point_item, parent=None):
        super(DiagramConfiguration, self).__init__(parent)
        entry_point = entry_point_item.get_callable()
        self.index_ = entry_point.index_

        self.setupUi(self)

        self.tree_.setColumnCount(TreeColumns.COLUMN_COUNT)
        self.tree_.header().hide()
        # TODO(KNR): to store the root item as member of this class is a hack, the tree should somehow provide
        # this information
        self.entry_point_item_ = CallableTreeItem(entry_point, self.tree_)
        for child in entry_point.get_referenced_callables():
            child_item = CallableTreeItem(child, self.entry_point_item_)

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

        for child in callable.get_referenced_callables():
            child.initialize()  # lazy load the referenced callables
            child_tree_item = CallableTreeItem(child, current_item)

    def export(self):
        print('exporting ', self.entry_point_item_.get_callable().get_name())
        print(self.entry_point_item_.export())
