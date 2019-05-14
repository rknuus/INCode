# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'entrydialog.ui'
#
# Created by: PyQt5 UI code generator 5.12.1
#
# WARNING! All changes made in this file will be lost!

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_EntryDialog(object):
    def setupUi(self, EntryDialog):
        EntryDialog.setObjectName("EntryDialog")
        EntryDialog.resize(745, 498)
        self.formLayout_ = QtWidgets.QFormLayout(EntryDialog)
        self.formLayout_.setObjectName("formLayout_")
        self.horizontalLayout_ = QtWidgets.QHBoxLayout()
        self.horizontalLayout_.setObjectName("horizontalLayout_")
        self.compilation_database_label_ = QtWidgets.QLabel(EntryDialog)
        self.compilation_database_label_.setObjectName("compilation_database_label_")
        self.horizontalLayout_.addWidget(self.compilation_database_label_)
        self.compilation_database_path_ = QtWidgets.QLineEdit(EntryDialog)
        self.compilation_database_path_.setObjectName("compilation_database_path_")
        self.horizontalLayout_.addWidget(self.compilation_database_path_)
        self.browse_compilation_database_button_ = QtWidgets.QPushButton(EntryDialog)
        self.browse_compilation_database_button_.setObjectName("browse_compilation_database_button_")
        self.horizontalLayout_.addWidget(self.browse_compilation_database_button_)
        self.formLayout_.setLayout(0, QtWidgets.QFormLayout.SpanningRole, self.horizontalLayout_)
        self.entry_file_label_ = QtWidgets.QLabel(EntryDialog)
        self.entry_file_label_.setObjectName("entry_file_label_")
        self.formLayout_.setWidget(1, QtWidgets.QFormLayout.LabelRole, self.entry_file_label_)
        self.entry_file_list_ = QtWidgets.QListView(EntryDialog)
        self.entry_file_list_.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.entry_file_list_.setObjectName("entry_file_list_")
        self.formLayout_.setWidget(2, QtWidgets.QFormLayout.SpanningRole, self.entry_file_list_)
        self.entry_point_label_ = QtWidgets.QLabel(EntryDialog)
        self.entry_point_label_.setObjectName("entry_point_label_")
        self.formLayout_.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.entry_point_label_)
        self.entry_point_list_ = QtWidgets.QListView(EntryDialog)
        self.entry_point_list_.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.entry_point_list_.setObjectName("entry_point_list_")
        self.formLayout_.setWidget(4, QtWidgets.QFormLayout.SpanningRole, self.entry_point_list_)
        self.buttonBox_ = QtWidgets.QDialogButtonBox(EntryDialog)
        self.buttonBox_.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox_.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.buttonBox_.setObjectName("buttonBox_")
        self.formLayout_.setWidget(5, QtWidgets.QFormLayout.FieldRole, self.buttonBox_)

        self.retranslateUi(EntryDialog)
        self.buttonBox_.accepted.connect(EntryDialog.accept)
        self.buttonBox_.rejected.connect(EntryDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(EntryDialog)

    def retranslateUi(self, EntryDialog):
        _translate = QtCore.QCoreApplication.translate
        EntryDialog.setWindowTitle(_translate("EntryDialog", "Entry Dialog"))
        self.compilation_database_label_.setText(_translate("EntryDialog", "Compilation database"))
        self.browse_compilation_database_button_.setText(_translate("EntryDialog", "Browse..."))
        self.entry_file_label_.setText(_translate("EntryDialog", "Entry file"))
        self.entry_point_label_.setText(_translate("EntryDialog", "Entry point"))


