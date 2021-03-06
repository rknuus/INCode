# Copyright (C) 2020 R. Knuus

from INCode.call_tree_manager import CallTreeManager, CallTreeManagerState
from INCode.diagramconfiguration import DiagramConfiguration
from INCode.ui_entrydialog import Ui_EntryDialog
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog
import os


class CallableItem(QStandardItem):
    def __init__(self, callable):
        super(QStandardItem, self).__init__(callable.name)
        self.callable_ = callable

    @property
    def callable(self):
        return self.callable_


class EntryDialog(QDialog, Ui_EntryDialog):
    def __init__(self, parent=None):
        super(EntryDialog, self).__init__(parent)

        self.setupUi(self)

        # TODO(KNR): prevent editing the entry file and entry point lists

        self.manager_ = CallTreeManager()

        self.browse_compilation_database_button_.clicked.connect(self.on_browse)
        self.compilation_database_path_.editingFinished.connect(self.on_edit_db_path)
        self.extra_arguments_.editingFinished.connect(self.on_edit_extra_args)
        self.entry_files_ = QStandardItemModel(self.entry_file_list_)
        self.entry_file_list_.setModel(self.entry_files_)
        self.entry_file_selection_ = self.entry_file_list_.selectionModel()
        self.entry_file_selection_.currentChanged.connect(self.on_select_entry_file)
        self.entry_points_ = QStandardItemModel(self.entry_point_list_)

    def on_edit_extra_args(self):
        args = self.extra_arguments_.text()
        self.manager_.state_ = CallTreeManagerState.INITIALIZED  # TODO(KNR): yuck
        self.manager_.set_extra_arguments(args)
        if self.compilation_database_path_.text():
            self.on_edit_db_path()

    def on_browse(self):
        path = QFileDialog.getOpenFileName(self, 'Open compilation database', '', '*.json')
        if path and len(path) > 0:
            path = path[0]
            if not path:
                return
            self.compilation_database_path_.setText(path)  # TODO(KNR): prevent double-event
            self.set_db_path(path)

    def on_edit_db_path(self):
        path = self.compilation_database_path_.text()
        if not path:
            return
        self.set_db_path(path)

    def set_db_path(self, db_path):
        compilation_database_directory = os.path.dirname(db_path)
        os.chdir(compilation_database_directory)
        self.entry_points_.clear()
        self.entry_files_.clear()
        tu_list = self.manager_.open(db_path)
        common_path = os.path.commonprefix(list(tu_list))
        for tu in tu_list:
            item = QStandardItem(tu.replace(common_path, ''))
            item.setData(tu)
            self.entry_files_.appendRow(item)

    def on_select_entry_file(self, current, previous):
        if not current:
            return
        entry_file_path = self.entry_files_.item(current.row(), 0).data()
        callable_list = self.manager_.select_tu(entry_file_path)
        self.entry_points_.clear()
        for callable in callable_list:
            item = CallableItem(callable)
            self.entry_points_.appendRow(item)
        self.entry_point_list_.setModel(self.entry_points_)

    def reject(self):
        QApplication.instance().quit()

    def accept(self):
        if not self.entry_point_list_.selectionModel():
            return
        current = self.entry_point_list_.selectionModel().selectedIndexes()
        if current and len(current) > 0:
            entry_point = self.entry_points_.item(current[0].row(), 0)
            self.manager_.select_root(entry_point.callable.name)
            self.hide()
            self.window_ = DiagramConfiguration(self.manager_, entry_point)
            self.window_.show()
