# Copyright (C) 2020 R. Knuus

from INCode.call_tree_manager import CallTreeManager
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

        # TODO(KNR): replace by user data
        self.manager_.set_extra_arguments('-isystem /usr/local/opt/llvm/bin/../include/c++/v1 -isystem /usr/include/c++/v1 -isystem /usr/local/include -isystem /usr/local/Cellar/llvm/10.0.0_3/lib/clang/10.0.0/include -isystem /usr/include')

        # self.db_ = None
        self.entry_files_ = QStandardItemModel(self.entry_file_list_)
        self.entry_points_ = QStandardItemModel(self.entry_point_list_)
        self.browse_compilation_database_button_.clicked.connect(self.onBrowse)
        self.entry_file_list_.setModel(self.entry_files_)
        self.entry_file_selection_ = self.entry_file_list_.selectionModel()
        self.entry_file_selection_.currentChanged.connect(self.onSelectEntryFile)

    # TODO(KNR): also support onEdit of self.compilation_database_path_
    def onBrowse(self):
        path = QFileDialog.getOpenFileName(self, 'Open compilation database', '', '*.json')
        if path and len(path) > 0:
            path = path[0]
            if not path:
                return
            compilation_database_directory = os.path.dirname(path)
            os.chdir(compilation_database_directory)
            self.compilation_database_path_.setText(path)
            self.entry_points_.clear()
            self.entry_files_.clear()
            tu_list = self.manager_.open(path)
            common_path = os.path.commonprefix(list(tu_list))
            for tu in tu_list:
                item = QStandardItem(tu.replace(common_path, ''))
                item.setData(tu)
                self.entry_files_.appendRow(item)

    def onSelectEntryFile(self, current, previous):
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
