# Copyright (C) 2018 R. Knuus

from enum import IntEnum
from INCode.ui_diagramconfiguration import Ui_DiagramConfiguration
from INCode.models import Index
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

        self.callable_id_ = callable.id
        self.referenced_items_ = []
        self.setText(TreeColumns.FIRST_COLUMN, callable.name)
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setCheckState(TreeColumns.FIRST_COLUMN, Qt.Unchecked)
        # TODO(KNR): probably prevent drag'n'drop operation

    @property
    def callable(self):
        return Index().lookup(self.callable_id_)

    @property
    def check_state(self):
        return self.checkState(TreeColumns.FIRST_COLUMN)

    def include(self):
        self.setCheckState(TreeColumns.FIRST_COLUMN, Qt.Checked)

    def exclude(self):
        self.setCheckState(TreeColumns.FIRST_COLUMN, Qt.Unchecked)

    def is_included(self):
        return self.check_state == Qt.Checked

    def export(self):
        callable = self.callable
        sender = callable.sender if self.is_included() else ''
        return '@startuml\n\n{}\n@enduml'.format(self.export_relations_(sender))

    def export_relations_(self, parent_sender):
        callable = self.callable
        diagram = ''
        for child_item in self.referenced_items_:
            child_callable = child_item.callable
            sender = callable.sender if self.is_included() else parent_sender
            if child_item.is_included():
                child_diagram_name = child_callable.caller.get_diagram_name()
                diagram += '"{}" -> "{}": {}\n'.format(sender if sender else "-",
                                                       child_callable.sender if child_callable.sender else "-",
                                                       child_diagram_name if child_diagram_name else "-")
            diagram += child_item.export_relations_(sender)
        return diagram


class DiagramConfiguration(QMainWindow, Ui_DiagramConfiguration):
    def __init__(self, entry_point_item, parent=None):
        super(DiagramConfiguration, self).__init__(parent)
        entry_point = entry_point_item.callable

        self.setupUi(self)

        self.tree_.setColumnCount(TreeColumns.COLUMN_COUNT)
        self.tree_.header().hide()
        # TODO(KNR): to store the root item as member of this class is a hack, the tree should somehow provide
        # this information
        self.entry_point_item_ = CallableTreeItem(entry_point, self.tree_)
        for child in entry_point.referenced_callables:
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

        callable = current_item.callable
        if not callable.is_definition():
            callable = Index().load_definition(callable)

        for child in callable.referenced_callables:
            child_tree_item = CallableTreeItem(child, current_item)
            child_tree_item.setExpanded(True)

    def export(self):
        print('exporting ', self.entry_point_item_.callable.name)
        print(self.entry_point_item_.export())
