# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'diagramconfiguration.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_DiagramConfiguration(object):
    def setupUi(self, DiagramConfiguration):
        DiagramConfiguration.setObjectName("DiagramConfiguration")
        DiagramConfiguration.resize(573, 468)
        self.centralwidget_ = QtWidgets.QWidget(DiagramConfiguration)
        self.centralwidget_.setObjectName("centralwidget_")
        self.vboxlayout_ = QtWidgets.QVBoxLayout(self.centralwidget_)
        self.vboxlayout_.setContentsMargins(0, 0, 0, 0)
        self.vboxlayout_.setSpacing(0)
        self.vboxlayout_.setObjectName("vboxlayout_")
        self.wrapper = QtWidgets.QSplitter(self.centralwidget_)
        self.wrapper.setOrientation(QtCore.Qt.Vertical)
        self.wrapper.setObjectName("wrapper")
        self.tree_ = QtWidgets.QTreeWidget(self.wrapper)
        self.tree_.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.tree_.setColumnCount(1)
        self.tree_.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tree_.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tree_.setObjectName("tree_")
        self.tree_.headerItem().setText(0, "Name")
        self.tree_.header().setVisible(False)
        self.svg_view_ = SvgView(self.wrapper)
        self.svg_view_.setObjectName("svg_view_")
        self.vboxlayout_.addWidget(self.wrapper)
        DiagramConfiguration.setCentralWidget(self.centralwidget_)
        self.menubar_ = QtWidgets.QMenuBar(DiagramConfiguration)
        self.menubar_.setGeometry(QtCore.QRect(0, 0, 573, 31))
        self.menubar_.setObjectName("menubar_")
        self.fileMenu_ = QtWidgets.QMenu(self.menubar_)
        self.fileMenu_.setObjectName("fileMenu_")
        self.actionsMenu_ = QtWidgets.QMenu(self.menubar_)
        self.actionsMenu_.setObjectName("actionsMenu_")
        DiagramConfiguration.setMenuBar(self.menubar_)
        self.new_action_ = QtWidgets.QAction(DiagramConfiguration)
        self.new_action_.setObjectName("new_action_")
        self.exit_action_ = QtWidgets.QAction(DiagramConfiguration)
        self.exit_action_.setObjectName("exit_action_")
        self.reveal_children_action_ = QtWidgets.QAction(DiagramConfiguration)
        self.reveal_children_action_.setObjectName("reveal_children_action_")
        self.export_action_ = QtWidgets.QAction(DiagramConfiguration)
        self.export_action_.setObjectName("export_action_")
        self.show_preview_action_ = QtWidgets.QAction(DiagramConfiguration)
        self.show_preview_action_.setCheckable(True)
        self.show_preview_action_.setChecked(True)
        self.show_preview_action_.setObjectName("show_preview_action_")
        self.local_only_action_ = QtWidgets.QAction(DiagramConfiguration)
        self.local_only_action_.setCheckable(True)
        self.local_only_action_.setObjectName("local_only_action_")
        self.toggle_orientation_action_ = QtWidgets.QAction(DiagramConfiguration)
        self.toggle_orientation_action_.setObjectName("toggle_orientation_action_")
        self.fileMenu_.addAction(self.new_action_)
        self.fileMenu_.addAction(self.export_action_)
        self.fileMenu_.addSeparator()
        self.fileMenu_.addAction(self.exit_action_)
        self.actionsMenu_.addAction(self.reveal_children_action_)
        self.actionsMenu_.addSeparator()
        self.actionsMenu_.addAction(self.show_preview_action_)
        self.actionsMenu_.addAction(self.local_only_action_)
        self.actionsMenu_.addAction(self.toggle_orientation_action_)
        self.menubar_.addAction(self.fileMenu_.menuAction())
        self.menubar_.addAction(self.actionsMenu_.menuAction())

        self.retranslateUi(DiagramConfiguration)
        self.show_preview_action_.triggered.connect(DiagramConfiguration.show_preview)
        self.local_only_action_.triggered.connect(DiagramConfiguration.toggle_local_only)
        self.toggle_orientation_action_.triggered.connect(DiagramConfiguration.toggle_layout)
        self.reveal_children_action_.triggered.connect(DiagramConfiguration.reveal_children)
        self.export_action_.triggered.connect(DiagramConfiguration.export)
        self.new_action_.triggered.connect(DiagramConfiguration.setup_entry_point)
        self.exit_action_.triggered.connect(DiagramConfiguration.exit)
        QtCore.QMetaObject.connectSlotsByName(DiagramConfiguration)

    def retranslateUi(self, DiagramConfiguration):
        _translate = QtCore.QCoreApplication.translate
        self.fileMenu_.setTitle(_translate("DiagramConfiguration", "&File"))
        self.actionsMenu_.setTitle(_translate("DiagramConfiguration", "&Actions"))
        self.new_action_.setText(_translate("DiagramConfiguration", "New"))
        self.new_action_.setShortcut(_translate("DiagramConfiguration", "Ctrl+N"))
        self.exit_action_.setText(_translate("DiagramConfiguration", "E&xit"))
        self.exit_action_.setShortcut(_translate("DiagramConfiguration", "Ctrl+Q"))
        self.reveal_children_action_.setText(_translate("DiagramConfiguration", "Reveal Children"))
        self.reveal_children_action_.setShortcut(_translate("DiagramConfiguration", "Ctrl+R"))
        self.export_action_.setText(_translate("DiagramConfiguration", "Export"))
        self.export_action_.setShortcut(_translate("DiagramConfiguration", "Ctrl+S"))
        self.show_preview_action_.setText(_translate("DiagramConfiguration", "Show Preview"))
        self.show_preview_action_.setShortcut(_translate("DiagramConfiguration", "Ctrl+T"))
        self.local_only_action_.setText(_translate("DiagramConfiguration", "Local Generation Only"))
        self.toggle_orientation_action_.setText(_translate("DiagramConfiguration", "Toggle Orientation"))
        self.toggle_orientation_action_.setShortcut(_translate("DiagramConfiguration", "Ctrl+E"))


from INCode.widgets import SvgView
