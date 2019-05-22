# Copyright (C) 2018 R. Knuus

import datetime
import subprocess
import tempfile
from io import BytesIO
from PIL import Image
import os.path
from enum import IntEnum
from threading import Thread
from plantuml import PlantUML, PlantUMLHTTPError
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow, QTreeWidgetItem, QDialog, QMessageBox, QFileDialog

from INCode.config import Config
from INCode.entrydialog import EntryDialog
from INCode.ui_diagramconfiguration import Ui_DiagramConfiguration
from INCode.models import Index


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
        self.setExpanded(True)
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

    def __init__(self, parent=None):
        super(DiagramConfiguration, self).__init__(parent)

        # Apply style sheet
        qss_file = "INCode/diagramconfiguration.qss"
        with open(qss_file, "r") as fh:
            self.setStyleSheet(fh.read())

        self.entry_point_item_ = None
        self.setupUi(self)
        self.setup_entry_point()

        self.temp_dir_ = tempfile.mkdtemp()
        self.current_diagram_ = None
        self.local_only_action_.setChecked(Config().load(Config.LOCAL_ONLY) is True)

        # Initialize Signals
        self.load_view_signal.connect(self.load_svg_view)

        # Update diagram preview timer
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(lambda: Thread(target=self.update_preview).start())
        self.preview_timer.start(2000)

    def setup_entry_point(self):
        if self.entry_point_item_:
            selection = QMessageBox.question(self, "New Entry Point", "Your complete progress will be lost.\n"
                                                                      "Do you wish to continue?",
                                             QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if selection == QMessageBox.No:
                return False

        self.tree_.clear()
        self.svg_view_.clear()
        dialog = EntryDialog()
        dialog.exec()
        if dialog.result() == QDialog.Rejected:
            self.exit()
            return

        entry_point = dialog.get_entry_point()

        self.entry_point_item_ = CallableTreeItem(entry_point, self.tree_)
        for child in entry_point.referenced_callables:
            CallableTreeItem(child, self.entry_point_item_)

        self.tree_.expandAll()
        self.tree_.resizeColumnToContents(TreeColumns.FIRST_COLUMN)
        return True

    def reveal_children(self):
        current_item = self.tree_.currentItem()
        if not current_item or current_item.childCount() > 0:
            return

        callable = current_item.callable
        if not callable.is_definition():
            callable = Index().load_definition(callable)

        for child in callable.referenced_callables:
            CallableTreeItem(child, current_item)

        # Adjust vertical scrollbar
        self.tree_.resizeColumnToContents(TreeColumns.FIRST_COLUMN)

    def toggle_local_only(self, local):
        Config().store(Config.LOCAL_ONLY, local)

    def update_preview(self):
        if self.svg_view_.isVisible():
            content = self.generate_uml()
            if content:
                self.load_view_signal.emit(content)

    def export(self):
        print('exporting ', self.entry_point_item_.callable.name)
        name = QFileDialog.getSaveFileName(self, "Export Diagram",
                                           os.path.join(os.getenv('HOME'), self.entry_point_item_.callable.name),
                                           "{};;{};;{}".format("png", "svg", "uml"))
        if name and name[0]:
            file_name = self._render_diagram(name[1], None, name[0])
            print("Exported to {}".format(file_name))

    def show_preview(self, show):
        if show:
            self.svg_view_.show()
        else:
            self.svg_view_.hide()

    def toggle_layout(self):
        orientation = Qt.Vertical if self.wrapper.orientation() == Qt.Horizontal else Qt.Horizontal
        self.wrapper.setOrientation(orientation)

    def generate_uml(self, content=None):
        if not content:
            if not self.entry_point_item_ or not self.entry_point_item_.callable:
                return
            content = self.entry_point_item_.export()
        if content == self.current_diagram_ or content == '@startuml\n\n\n@enduml':
            return
        self.current_diagram_ = content
        print(content)
        output = self._render_diagram("svg", content)
        return output

    def _render_diagram(self, file_format, content=None, file_name=None):
        if not content:
            content = self.entry_point_item_.export()

        if file_name and not file_name.endswith(file_format):
            file_name += "." + file_format

        # uml format is always offline
        if file_format == "uml":
            if not file_name:
                return content
            file = open(file_name, "w")
            file.write(content)
            file.close()
            return

        if Config().load(Config.LOCAL_ONLY):
            return self._render_diagram_local(file_format, content, file_name)
        else:
            return self._render_diagram_online(file_format, content, file_name)

    def _render_diagram_online(self, file_format, content=None, file_name=None):
        renderer = PlantUML("http://www.plantuml.com/plantuml/{}/".format(file_format))
        try:
            output = renderer.processes(content)
            if not file_name:
                return output
            if file_format == "png":
                img = Image.open(BytesIO(output))
                img.save(file_name)
            else:
                file = open(file_name, "w")
                file.write(output.decode("utf-8"))
                file.close()
        except PlantUMLHTTPError:
            file_name = self._render_diagram_local(file_format, content, file_name)
        return file_name

    def _render_diagram_local(self, file_format, content=None, file_name=None):
        just_content = file_name is None
        if just_content:
            timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
            file_name = os.path.join(self.temp_dir_, timestamp) + ".{}".format(file_format)
        cmd = "echo '{}' | plantuml -pipe > {} -t{}".format(content, file_name, file_format)
        subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()
        if just_content:
            output = open(file_name, "rb").read()
            subprocess.call(["rm", file_name])
            return output
        return file_name

    def load_svg_view(self, content):
        if not content:
            return
        if not isinstance(content, bytes):
            raise TypeError("Excepted type 'bytes', not '{}'".format(type(content)))
        self.svg_view_.load_svg_content(content)
        self.wrapper.setStretchFactor(1, 1)

    def exit(self):
        QApplication.instance().quit()
