# Copyright (C) 2020 R. Knuus

from datetime import datetime
from enum import IntEnum
from INCode.ui_diagramconfiguration import Ui_DiagramConfiguration
from os import path
from plantweb.render import render
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem
from requests import RequestException
from threading import Thread
import subprocess
import tempfile


class TreeColumns(IntEnum):
    FIRST_COLUMN = 0
    COLUMN_COUNT = 1


class CallableTreeItem(QTreeWidgetItem):
    def __init__(self, callable, manager, parent=None):
        super(QTreeWidgetItem, self).__init__(parent)

        self.callable = callable
        self.manager_ = manager
        self.setText(TreeColumns.FIRST_COLUMN, callable.name)
        self.setFlags(self.flags() | Qt.ItemIsUserCheckable)
        self.setCheckState(TreeColumns.FIRST_COLUMN, Qt.Unchecked)
        # TODO(KNR): probably prevent drag'n'drop operation

    def is_included(self):
        return self.checkState(TreeColumns.FIRST_COLUMN) == Qt.Checked


class DiagramConfiguration(QMainWindow, Ui_DiagramConfiguration):
    load_view_signal = pyqtSignal(bytes)

    def __init__(self, manager, entry_point_item, parent=None):
        super(DiagramConfiguration, self).__init__(parent)
        self.manager_ = manager
        entry_point = entry_point_item.callable

        self.setupUi(self)

        self.current_diagram_ = None

        self.temp_dir_ = tempfile.mkdtemp()
        self.tree_.setColumnCount(TreeColumns.COLUMN_COUNT)
        self.tree_.header().hide()
        self.entry_point_item_ = CallableTreeItem(callable=entry_point, manager=self.manager_, parent=self.tree_)
        for call in self.manager_.get_calls_of(entry_point.name):
            CallableTreeItem(callable=call, manager=self.manager_, parent=self.entry_point_item_)

        self.tree_.expandAll()
        for column in range(self.tree_.columnCount()):
            self.tree_.resizeColumnToContents(column)

        self.exitAction_.triggered.connect(QApplication.instance().quit)

        self.tree_.itemChanged.connect(self.update_included_callables)
        self.revealChildrenAction_.triggered.connect(self.reveal_children)
        self.exportAction_.triggered.connect(self.export)
        self.togglePreviewAction_.triggered.connect(self.toggle_preview)
        self.toggleLayoutAction_.triggered.connect(self.toggle_layout)
        self.load_view_signal.connect(self.load_svg_view)

        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(lambda: Thread(target=self.init_preview).start())
        self.preview_timer.start(2000)

    def update_included_callables(self, item, column):
        if item.is_included():
            self.manager_.include(item.callable.name)
        else:
            self.manager_.exclude(item.callable.name)

    def reveal_children(self):
        current_item = self.tree_.currentItem()
        if not current_item or current_item.childCount() > 0:
            return

        callable = current_item.callable
        if not callable.is_definition():
            callable = self.manager_.load_definition(callable.name)
            current_item.callable = callable

        for call in self.manager_.get_calls_of(callable.name):
            child_tree_item = CallableTreeItem(callable=call, manager=self.manager_, parent=current_item)
            child_tree_item.setExpanded(True)

    def init_preview(self):
        if self.svg_view_.isVisible():
            content = self.generate_uml()
            if content:
                self.load_view_signal.emit(content)

    def export(self):
        content = self.generate_uml()
        self.load_svg_view(content)

    def toggle_preview(self):
        if self.svg_view_.isVisible():
            self.svg_view_.hide()
        else:
            self.svg_view_.show()

    def toggle_layout(self):
        orientation = Qt.Vertical if self.wrapper.orientation() == Qt.Horizontal else Qt.Horizontal
        self.wrapper.setOrientation(orientation)

    def generate_uml(self):
        content = self.manager_.export()
        if content == self.current_diagram_ or content == '@startuml\n\n\n@enduml':
            return False
        self.current_diagram_ = content
        try:
            output = render(content,
                            engine='plantuml',
                            format='svg',
                            cacheopts={
                                'use_cache': False
                            })[0]
        except RequestException:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')  # TODO(KNR): replace by mktemp
            temp_file_name = path.join(self.temp_dir_, timestamp) + '.svg'
            cmd = "echo '{}' | plantuml -pipe > {} -tsvg".format(content, temp_file_name)
            subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
            output = open(temp_file_name, 'rb').read()
            subprocess.call(['rm', temp_file_name])  # TODO(KNR): replace by pythoning file remove (if still necessary for mktemp)
        return output

    def load_svg_view(self, content):
        if not content:
            return
        if not isinstance(content, bytes):
            raise TypeError("Excepted type 'bytes', not '{}'".format(type(content)))
        self.svg_view_.loadSvgContent(content)
