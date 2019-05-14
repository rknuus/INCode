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
        self.exitAction_ = QtWidgets.QAction(DiagramConfiguration)
        self.exitAction_.setObjectName("exitAction_")
        self.revealChildrenAction_ = QtWidgets.QAction(DiagramConfiguration)
        self.revealChildrenAction_.setObjectName("revealChildrenAction_")
        self.exportAction_ = QtWidgets.QAction(DiagramConfiguration)
        self.exportAction_.setObjectName("exportAction_")
        self.showPreviewAction_ = QtWidgets.QAction(DiagramConfiguration)
        self.showPreviewAction_.setCheckable(True)
        self.showPreviewAction_.setChecked(True)
        self.showPreviewAction_.setObjectName("showPreviewAction_")
        self.toggleOrientationAction_ = QtWidgets.QAction(DiagramConfiguration)
        self.toggleOrientationAction_.setObjectName("toggleOrientationAction_")
        self.fileMenu_.addAction(self.exitAction_)
        self.actionsMenu_.addAction(self.revealChildrenAction_)
        self.actionsMenu_.addSeparator()
        self.actionsMenu_.addAction(self.exportAction_)
        self.actionsMenu_.addSeparator()
        self.actionsMenu_.addAction(self.showPreviewAction_)
        self.actionsMenu_.addAction(self.toggleOrientationAction_)
        self.menubar_.addAction(self.fileMenu_.menuAction())
        self.menubar_.addAction(self.actionsMenu_.menuAction())

        self.retranslateUi(DiagramConfiguration)
        self.showPreviewAction_.triggered.connect(DiagramConfiguration.show_preview)
        self.toggleOrientationAction_.triggered.connect(DiagramConfiguration.toggle_layout)
        self.revealChildrenAction_.triggered.connect(DiagramConfiguration.reveal_children)
        self.exportAction_.triggered.connect(DiagramConfiguration.export)
        self.exitAction_.triggered.connect(DiagramConfiguration.exit)
        QtCore.QMetaObject.connectSlotsByName(DiagramConfiguration)

    def retranslateUi(self, DiagramConfiguration):
        _translate = QtCore.QCoreApplication.translate
        self.fileMenu_.setTitle(_translate("DiagramConfiguration", "&File"))
        self.actionsMenu_.setTitle(_translate("DiagramConfiguration", "&Actions"))
        self.exitAction_.setText(_translate("DiagramConfiguration", "E&xit"))
        self.exitAction_.setShortcut(_translate("DiagramConfiguration", "Ctrl+Q"))
        self.revealChildrenAction_.setText(_translate("DiagramConfiguration", "Reveal Children"))
        self.revealChildrenAction_.setShortcut(_translate("DiagramConfiguration", "Ctrl+R"))
        self.exportAction_.setText(_translate("DiagramConfiguration", "Export"))
        self.exportAction_.setShortcut(_translate("DiagramConfiguration", "Ctrl+S"))
        self.showPreviewAction_.setText(_translate("DiagramConfiguration", "Show Preview"))
        self.showPreviewAction_.setShortcut(_translate("DiagramConfiguration", "Ctrl+T"))
        self.toggleOrientationAction_.setText(_translate("DiagramConfiguration", "Toggle Orientation"))
        self.toggleOrientationAction_.setShortcut(_translate("DiagramConfiguration", "Ctrl+E"))


from INCode.widgets import SvgView
