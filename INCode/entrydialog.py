# Copyright (C) 2018 R. Knuus

from INCode.diagramconfiguration import DiagramConfiguration
from INCode.models import CompilationDatabases, Index
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

        self.db_ = None
        self.entry_files_ = QStandardItemModel(self.entry_file_list_)
        self.entry_points_ = QStandardItemModel(self.entry_point_list_)
        self.browse_compilation_database_button_.clicked.connect(self.onBrowse)
        self.entry_file_list_.setModel(self.entry_files_)
        self.entry_file_selection_ = self.entry_file_list_.selectionModel()
        self.entry_file_selection_.currentChanged.connect(self.onSelectEntryFile)

    def onBrowse(self):
        path = QFileDialog.getOpenFileName(self, 'Open compilation database', '', '*.json')
        if path and len(path) > 0:
            path = path[0]
            if not path:
                return
            self.compilation_database_path_.setText(path)
            self.db_ = CompilationDatabases()  # to clear any previous compilation database
            self.db_.add_compilation_database(os.path.dirname(path))
            index = Index(self.db_)
            self.entry_points_.clear()
            self.entry_files_.clear()
            file_paths = self.db_.get_files()
            for file in file_paths:
                item = QStandardItem(file)
                self.entry_files_.appendRow(item)
            index.common_path = os.path.commonprefix(file_paths)

    def onSelectEntryFile(self, current, previous):
        if not current:
            return
        entry_file_path = self.entry_files_.item(current.row(), 0).text()
        entry_file = Index().load(entry_file_path)
        self.entry_points_.clear()
        for callable in entry_file.callables:
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
            self.hide()
            self.window_ = DiagramConfiguration(entry_point)
            self.window_.show()
