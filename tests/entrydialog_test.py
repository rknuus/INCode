# Copyright (C) 2018 R. Knuus

try:
    from INCode import entrydialog
    from INCode.models import CompilationDatabases, Index
except:
    import entrydialog
    from models import CompilationDatabases, Index
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QApplication, QFileDialog
from unittest.mock import MagicMock, PropertyMock
import pytest
import sys

COMPILATION_DATABASE_FAKE_PATH = '/some/path/compile_database.json'
APP = QApplication(sys.argv)


@pytest.fixture
def setup_open_file_mock(mocker):
    mocker.patch.object(QFileDialog, 'getOpenFileName', return_value=(COMPILATION_DATABASE_FAKE_PATH, '*.json'))
    mocker.patch.object(CompilationDatabases, 'add_compilation_database')


def setup_open_file_mock_with_parameters(mocker, file_path):
    mocker.patch.object(QFileDialog, 'getOpenFileName', return_value=(file_path, '*.json'))
    mocker.patch.object(CompilationDatabases, 'add_compilation_database')


def test_dialog_initially_all_fields_empty():
    uut = entrydialog.EntryDialog()
    assert not uut.compilation_database_path_.text()
    assert uut.entry_files_.rowCount() == 0
    assert uut.entry_points_.rowCount() == 0


def get_entry_files(uut, expected_files):
    actual_entry_file_count = max(len(expected_files), uut.entry_files_.rowCount())
    actual_entry_files = [uut.entry_files_.item(i).data() for i in range(actual_entry_file_count)]
    return actual_entry_files


def test_dialog_onBrowse__updates_entry_file(mocker, setup_open_file_mock):
    uut = entrydialog.EntryDialog()
    uut.onBrowse()
    assert uut.compilation_database_path_.text() == COMPILATION_DATABASE_FAKE_PATH


def test_dialog_onBrowse__doesnt_crash_when_path_is_empty(mocker):
    setup_open_file_mock_with_parameters(mocker, file_path='')
    uut = entrydialog.EntryDialog()
    uut.onBrowse()
    assert uut.compilation_database_path_.text() == ''


def test_dialog_onBrowse_once__populates_entry_files(mocker, setup_open_file_mock):
    expected_entry_files = ['foo.cpp', 'bar.cpp']
    mocker.patch.object(CompilationDatabases, 'get_files', return_value=expected_entry_files)
    uut = entrydialog.EntryDialog()
    uut.onBrowse()
    actual_entry_files = get_entry_files(uut, expected_entry_files)
    assert actual_entry_files == expected_entry_files


def test_dialog_onBrowse_twice__clears_entry_files_before_populating_again(mocker, setup_open_file_mock):
    expected_entry_files = ['a.cpp']
    initial_entry_files = ['foo.cpp', 'bar.cpp', 'baz.cpp']
    mocker.patch.object(CompilationDatabases, 'get_files', return_value=initial_entry_files)
    uut = entrydialog.EntryDialog()
    uut.onBrowse()
    mocker.patch.object(CompilationDatabases, 'get_files', return_value=expected_entry_files)
    uut.onBrowse()
    actual_entry_files = get_entry_files(uut, expected_entry_files)
    assert actual_entry_files == expected_entry_files


def build_callable_mock(name):
    mock = MagicMock()
    type(mock).name = PropertyMock(return_value=name)
    return mock


def get_entry_points(uut, expected_entry_points):
    actual_entry_point_count = max(len(expected_entry_points), uut.entry_points_.rowCount())
    actual_entry_points = [uut.entry_points_.item(i).text() for i in range(actual_entry_point_count)]
    return actual_entry_points


def setup_entry_files(mocker, uut, expected_entry_points):
    callables = [build_callable_mock(name) for name in expected_entry_points]
    file_mock = MagicMock()
    type(file_mock).callables = PropertyMock(return_value=callables)
    mocker.patch.object(Index, 'load', return_value=file_mock)
    item = QStandardItem('/irrelevant/path')
    uut.entry_files_.appendRow(item)
    uut.entry_file_list_.setModel(uut.entry_files_)


@pytest.fixture
def selected_mock():
    current = MagicMock()
    current.row.return_value = 0
    return current


def test_dialog_onSelectEntryFile_once__populates_entry_points(mocker, selected_mock):
    expected_entry_points = ['void a()', 'void b()']
    uut = entrydialog.EntryDialog()
    setup_entry_files(mocker, uut, expected_entry_points)
    uut.onSelectEntryFile(selected_mock, None)
    actual_entry_points = get_entry_points(uut, expected_entry_points)
    assert actual_entry_points == expected_entry_points


def test_dialog_onSelectEntryFile_twice__clears_entry_points_before_populating_again(mocker, selected_mock):
    expected_entry_points = ['int b()']
    initial_entry_points = ['void a()', 'void b()', 'void c()']
    uut = entrydialog.EntryDialog()
    setup_entry_files(mocker, uut, initial_entry_points)
    uut.onSelectEntryFile(selected_mock, None)
    setup_entry_files(mocker, uut, expected_entry_points)
    uut.onSelectEntryFile(selected_mock, None)
    actual_entry_points = get_entry_points(uut, expected_entry_points)
    assert actual_entry_points == expected_entry_points


def test_dialog_onSelectEntryFile_but_nothing_selected__does_not_populate_entry_points(mocker):
    uut = entrydialog.EntryDialog()
    uut.entry_point_list_ = MagicMock()
    uut.onSelectEntryFile(None, None)
    uut.entry_point_list_.setModel.assert_not_called()


def test_dialog_reject__quits_application(monkeypatch):
    exit_calls = []
    monkeypatch.setattr(QApplication, 'quit', lambda _: exit_calls.append(1))
    uut = entrydialog.EntryDialog()
    uut.reject()
    assert exit_calls == [1]

# Test List
# =========
# - on accept and if entry point selected show diagram configuration uut
# - on accept and if no entry point selected don't show diagram configuration uut
