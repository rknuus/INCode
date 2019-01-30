# Copyright (C) 2018 R. Knuus

from enum import IntEnum
from INCode.ui_diagramconfiguration import Ui_DiagramConfiguration
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem
import os.path


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
        self.referenced_items_ = []
        self.setText(TreeColumns.FIRST_COLUMN, callable.get_name())
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setCheckState(TreeColumns.FIRST_COLUMN, Qt.Unchecked)
        # TODO(KNR): probably prevent drag'n'drop operation

    def get_callable(self):
        return self.index_.lookup(self.callable_id_)

    def get_check_state(self):
        return self.checkState(TreeColumns.FIRST_COLUMN)

    def include(self):
        self.setCheckState(TreeColumns.FIRST_COLUMN, Qt.Checked)

    def exclude(self):
        self.setCheckState(TreeColumns.FIRST_COLUMN, Qt.Unchecked)

    def is_included(self):
        return self.get_check_state() == Qt.Checked

    def export(self):
        callable = self.get_callable()
        sender = callable.sender_ if self.is_included() else ''
        return '@startuml\n\n{}\n@enduml'.format(self.export_relations_(sender))

    def export_relations_(self, parent_sender):
        callable = self.get_callable()
        diagram = ''
        for child_item in self.referenced_items_:
            child_callable = child_item.get_callable()
            sender = callable.sender_ if self.is_included() else parent_sender
            if child_item.is_included():
                diagram += '{} -> {}: {}\n'.format(sender,
                                                   child_callable.sender_,
                                                   child_callable._get_name(True))
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
            CallableTreeItem(child, self.entry_point_item_)

        self.tree_.expandAll()
        for column in range(self.tree_.columnCount()):
            self.tree_.resizeColumnToContents(column)

        self.exitAction_.triggered.connect(QApplication.instance().quit)

        self.revealChildrenAction_.triggered.connect(self.reveal_children)
        self.exportAction_.triggered.connect(self.export)

    def reveal_children(self):
        current_item = self.tree_.currentItem()
        if not current_item or current_item.childCount() > 0:
            return
        callable = current_item.get_callable()

        for child in callable.get_referenced_callables():
            child.initialize()  # lazy load the referenced callables
            child_tree_item = CallableTreeItem(child, current_item)
            child_tree_item.setExpanded(True)

    def export(self):
        print('exporting ', self.entry_point_item_.get_callable().get_name())
        print(self.entry_point_item_.export())
