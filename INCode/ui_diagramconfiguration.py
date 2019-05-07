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
        DiagramConfiguration.setStyleSheet("\n"
"     QSplitter::handle::horizontal, QSplitter::handle::vertical { width: 6px; background-color: #666; }\n"
"   ")
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
        self.tree_.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        self.tree_.setObjectName("tree_")
        self.tree_.headerItem().setText(0, "1")
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
        self.statusbar_ = QtWidgets.QStatusBar(DiagramConfiguration)
        self.statusbar_.setObjectName("statusbar_")
        DiagramConfiguration.setStatusBar(self.statusbar_)
        self.exitAction_ = QtWidgets.QAction(DiagramConfiguration)
        self.exitAction_.setObjectName("exitAction_")
        self.revealChildrenAction_ = QtWidgets.QAction(DiagramConfiguration)
        self.revealChildrenAction_.setObjectName("revealChildrenAction_")
        self.exportAction_ = QtWidgets.QAction(DiagramConfiguration)
        self.exportAction_.setObjectName("exportAction_")
        self.togglePreviewAction_ = QtWidgets.QAction(DiagramConfiguration)
        self.togglePreviewAction_.setObjectName("togglePreviewAction_")
        self.toggleLayoutAction_ = QtWidgets.QAction(DiagramConfiguration)
        self.toggleLayoutAction_.setObjectName("toggleLayoutAction_")
        self.fileMenu_.addAction(self.exitAction_)
        self.actionsMenu_.addAction(self.revealChildrenAction_)
        self.actionsMenu_.addSeparator()
        self.actionsMenu_.addAction(self.exportAction_)
        self.actionsMenu_.addSeparator()
        self.actionsMenu_.addAction(self.togglePreviewAction_)
        self.actionsMenu_.addAction(self.toggleLayoutAction_)
        self.menubar_.addAction(self.fileMenu_.menuAction())
        self.menubar_.addAction(self.actionsMenu_.menuAction())

        self.retranslateUi(DiagramConfiguration)
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
        self.togglePreviewAction_.setText(_translate("DiagramConfiguration", "Toggle UML"))
        self.togglePreviewAction_.setShortcut(_translate("DiagramConfiguration", "Ctrl+T"))
        self.toggleLayoutAction_.setText(_translate("DiagramConfiguration", "Toggle Preview"))
        self.toggleLayoutAction_.setShortcut(_translate("DiagramConfiguration", "Ctrl+E"))


from INCode.widgets import SvgView
