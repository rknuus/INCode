# Copyright (C) 2018 R. Knuus

from INCode.diagramconfiguration import DiagramConfiguration
from INCode.models import Index
from INCode.ui_entrydialog import Ui_EntryDialog
from PyQt5.QtGui import QStandardItem, QStandardItemModel
from PyQt5.QtWidgets import QApplication, QDialog, QFileDialog
import os


class CallableItem(QStandardItem):
    def __init__(self, callable):
        super(QStandardItem, self).__init__(callable.get_name())
        self.callable_ = callable

    def get_callable(self):
        return self.callable_


class EntryDialog(QDialog, Ui_EntryDialog):
    def __init__(self, parent=None):
        super(EntryDialog, self).__init__(parent)

        self.setupUi(self)

        # TODO(KNR): prevent editing the entry file and entry point lists

        self.entry_files_ = QStandardItemModel(self.entry_file_list_)
        self.entry_points_ = QStandardItemModel(self.entry_point_list_)
        self.browse_compilation_database_button_.clicked.connect(self.onBrowse)
        self.index_ = Index()

    def onBrowse(self):
        path = QFileDialog.getOpenFileName(self, 'Open compilation database', '', '*.json')
        if path and len(path) > 0:
            path = path[0]
            if not path:
                return
            self.compilation_database_path_.setText(path)
            self.index_ = Index()
            self.index_.add_compilation_database(os.path.dirname(path))
            self.entry_points_.clear()
            self.entry_files_.clear()
            for file in self.index_.get_files():
                item = QStandardItem(file)
                self.entry_files_.appendRow(item)
            self.entry_file_list_.setModel(self.entry_files_)
            self.entry_file_selection_ = self.entry_file_list_.selectionModel()
            # TODO(KNR): if possible do connection in constructor
            self.entry_file_selection_.currentChanged.connect(self.onSelectEntryFile)

    def onSelectEntryFile(self, current, previous):
        if not current:
            return
        entry_file_path = self.entry_files_.item(current.row(), 0).text()
        entry_file = self.index_.load(entry_file_path)
        self.entry_points_.clear()
        for callable in entry_file.get_callables():
            item = CallableItem(callable)
            self.entry_points_.appendRow(item)
        self.entry_point_list_.setModel(self.entry_points_)

    def reject(self):
        QApplication.instance().quit()

    def accept(self):
        current = self.entry_point_list_.selectionModel().selectedIndexes()
        if current and len(current) > 0:
            entry_point = self.entry_points_.item(current[0].row(), 0)
            self.hide()
            self.window_ = DiagramConfiguration(self.index_, entry_point)
            self.window_.show()
