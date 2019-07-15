# Copyright (C) 2018 R. Knuus

from datetime import datetime
from enum import IntEnum
from INCode.models import Index
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
    load_view_signal = pyqtSignal(bytes)

    def __init__(self, entry_point_item, parent=None):
        super(DiagramConfiguration, self).__init__(parent)
        entry_point = entry_point_item.callable

        self.setupUi(self)

        self.current_diagram_ = None

        self.temp_dir_ = tempfile.mkdtemp()
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
        self.togglePreviewAction_.triggered.connect(self.toggle_preview)
        self.toggleLayoutAction_.triggered.connect(self.toggle_layout)
        self.load_view_signal.connect(self.load_svg_view)

        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(lambda: Thread(target=self.init_preview).start())
        self.preview_timer.start(2000)

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

    def init_preview(self):
        if self.svg_view_.isVisible():
            content = self.generate_uml()
            if content:
                self.load_view_signal.emit(content)

    def export(self):
        print('exporting ', self.entry_point_item_.callable.name)
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
        content = self.entry_point_item_.export()
        if content == self.current_diagram_ or content == '@startuml\n\n\n@enduml':
            return False
        self.current_diagram_ = content
        print(content)
        try:
            output = render(content,
                            engine="plantuml",
                            format="svg",
                            cacheopts={
                                "use_cache": False
                            })[0]
        except RequestException:
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            temp_file_name = path.join(self.temp_dir_, timestamp) + ".svg"
            cmd = "echo '{}' | plantuml -pipe > {} -tsvg".format(content, temp_file_name)
            subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
            output = open(temp_file_name, "rb").read()
            subprocess.call(["rm", temp_file_name])
        return output

    def load_svg_view(self, content):
        if not content:
            return
        if not isinstance(content, bytes):
            raise TypeError("Excepted type 'bytes', not '{}'".format(type(content)))
        self.svg_view_.loadSvgContent(content)



