# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'INCode/diagramconfiguration.ui'
#
# Created by: PyQt5 UI code generator 5.10
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
        self.tree_ = QtWidgets.QTreeWidget(self.centralwidget_)
        self.tree_.setObjectName("tree_")
        self.vboxlayout_.addWidget(self.tree_)
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
        self.fileMenu_.addAction(self.exitAction_)
        self.actionsMenu_.addAction(self.revealChildrenAction_)
        self.actionsMenu_.addSeparator()
        self.actionsMenu_.addAction(self.exportAction_)
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

