# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'INCode/entrydialog.ui'
#
# Created by: PyQt5 UI code generator 5.14.2
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_EntryDialog(object):
    def setupUi(self, EntryDialog):
        EntryDialog.setObjectName("EntryDialog")
        EntryDialog.resize(849, 589)
        self.form_layout_ = QtWidgets.QFormLayout(EntryDialog)
        self.form_layout_.setObjectName("form_layout_")
        self.extra_args_box_ = QtWidgets.QHBoxLayout()
        self.extra_args_box_.setSizeConstraint(QtWidgets.QLayout.SetDefaultConstraint)
        self.extra_args_box_.setObjectName("extra_args_box_")
        self.extra_arguments_label_ = QtWidgets.QLabel(EntryDialog)
        self.extra_arguments_label_.setObjectName("extra_arguments_label_")
        self.extra_args_box_.addWidget(self.extra_arguments_label_)
        self.extra_arguments_ = QtWidgets.QLineEdit(EntryDialog)
        self.extra_arguments_.setObjectName("extra_arguments_")
        self.extra_args_box_.addWidget(self.extra_arguments_)
        self.form_layout_.setLayout(0, QtWidgets.QFormLayout.SpanningRole, self.extra_args_box_)
        self.db_box_ = QtWidgets.QHBoxLayout()
        self.db_box_.setObjectName("db_box_")
        self.compilation_database_label_ = QtWidgets.QLabel(EntryDialog)
        self.compilation_database_label_.setObjectName("compilation_database_label_")
        self.db_box_.addWidget(self.compilation_database_label_)
        self.compilation_database_path_ = QtWidgets.QLineEdit(EntryDialog)
        self.compilation_database_path_.setObjectName("compilation_database_path_")
        self.db_box_.addWidget(self.compilation_database_path_)
        self.browse_compilation_database_button_ = QtWidgets.QPushButton(EntryDialog)
        self.browse_compilation_database_button_.setObjectName("browse_compilation_database_button_")
        self.db_box_.addWidget(self.browse_compilation_database_button_)
        self.form_layout_.setLayout(1, QtWidgets.QFormLayout.SpanningRole, self.db_box_)
        spacerItem = QtWidgets.QSpacerItem(20, 4, QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        self.form_layout_.setItem(2, QtWidgets.QFormLayout.LabelRole, spacerItem)
        self.entry_file_label_ = QtWidgets.QLabel(EntryDialog)
        self.entry_file_label_.setObjectName("entry_file_label_")
        self.form_layout_.setWidget(3, QtWidgets.QFormLayout.LabelRole, self.entry_file_label_)
        self.entry_file_list_ = QtWidgets.QListView(EntryDialog)
        self.entry_file_list_.setObjectName("entry_file_list_")
        self.form_layout_.setWidget(4, QtWidgets.QFormLayout.SpanningRole, self.entry_file_list_)
        self.entry_point_label_ = QtWidgets.QLabel(EntryDialog)
        self.entry_point_label_.setObjectName("entry_point_label_")
        self.form_layout_.setWidget(5, QtWidgets.QFormLayout.LabelRole, self.entry_point_label_)
        self.entry_point_list_ = QtWidgets.QListView(EntryDialog)
        self.entry_point_list_.setObjectName("entry_point_list_")
        self.form_layout_.setWidget(6, QtWidgets.QFormLayout.SpanningRole, self.entry_point_list_)
        self.outer_button_box_ = QtWidgets.QHBoxLayout()
        self.outer_button_box_.setSizeConstraint(QtWidgets.QLayout.SetFixedSize)
        self.outer_button_box_.setObjectName("outer_button_box_")
        spacerItem1 = QtWidgets.QSpacerItem(640, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.outer_button_box_.addItem(spacerItem1)
        self.button_box_ = QtWidgets.QDialogButtonBox(EntryDialog)
        self.button_box_.setOrientation(QtCore.Qt.Horizontal)
        self.button_box_.setStandardButtons(QtWidgets.QDialogButtonBox.Cancel|QtWidgets.QDialogButtonBox.Ok)
        self.button_box_.setCenterButtons(False)
        self.button_box_.setObjectName("button_box_")
        self.outer_button_box_.addWidget(self.button_box_)
        self.form_layout_.setLayout(7, QtWidgets.QFormLayout.SpanningRole, self.outer_button_box_)

        self.retranslateUi(EntryDialog)
        self.button_box_.accepted.connect(EntryDialog.accept)
        self.button_box_.rejected.connect(EntryDialog.reject)
        QtCore.QMetaObject.connectSlotsByName(EntryDialog)

    def retranslateUi(self, EntryDialog):
        _translate = QtCore.QCoreApplication.translate
        EntryDialog.setWindowTitle(_translate("EntryDialog", "Entry Dialog"))
        self.extra_arguments_label_.setText(_translate("EntryDialog", "Extra arguments"))
        self.compilation_database_label_.setText(_translate("EntryDialog", "Compilation database"))
        self.browse_compilation_database_button_.setText(_translate("EntryDialog", "Browse..."))
        self.entry_file_label_.setText(_translate("EntryDialog", "Entry file"))
        self.entry_point_label_.setText(_translate("EntryDialog", "Entry point"))
