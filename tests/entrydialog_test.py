# Copyright (C) 2018 R. Knuus

try:
    from INCode import entrydialog
    from INCode.models import Index
except:
    import entrydialog
    from models import Index
from PyQt5.QtGui import QStandardItem
from PyQt5.QtWidgets import QApplication, QFileDialog
from unittest.mock import MagicMock
import pytest
import sys

COMPILATION_DATABASE_FAKE_PATH = '/some/path/compile_database.json'
APP = QApplication(sys.argv)


@pytest.fixture
def uut():
    return entrydialog.EntryDialog()


@pytest.fixture
def setup_open_file_mock(mock, file_path=COMPILATION_DATABASE_FAKE_PATH):
    mock.patch.object(QFileDialog, 'getOpenFileName', return_value=(file_path, '*.json'))
    mock.patch.object(Index, 'add_compilation_database')


def test_dialog_initially_all_fields_empty(uut):
    assert not uut.compilation_database_path_.text()
    assert uut.entry_files_.rowCount() == 0
    assert uut.entry_points_.rowCount() == 0


def get_entry_files(uut, expected_files):
    actual_entry_file_count = max(len(expected_files), uut.entry_files_.rowCount())
    actual_entry_files = [uut.entry_files_.item(i).text() for i in range(actual_entry_file_count)]
    return actual_entry_files


def test_dialog_onBrowse__updates_entry_file(mock, uut):
    setup_open_file_mock(mock, file_path=COMPILATION_DATABASE_FAKE_PATH)
    uut.onBrowse()
    assert uut.compilation_database_path_.text() == COMPILATION_DATABASE_FAKE_PATH


def test_dialog_onBrowse_once__populates_entry_files(mock, setup_open_file_mock, uut):
    expected_entry_files = ['foo.cpp', 'bar.cpp']
    mock.patch.object(Index, 'get_files', return_value=expected_entry_files)
    uut.onBrowse()
    actual_entry_files = get_entry_files(uut, expected_entry_files)
    assert actual_entry_files == expected_entry_files


def test_dialog_onBrowse_twice__clears_entry_files_before_populating_again(mock, setup_open_file_mock, uut):
    expected_entry_files = ['a.cpp']
    initial_entry_files = ['foo.cpp', 'bar.cpp', 'baz.cpp']
    mock.patch.object(Index, 'get_files', return_value=initial_entry_files)
    uut.onBrowse()
    mock.patch.object(Index, 'get_files', return_value=expected_entry_files)
    uut.onBrowse()
    actual_entry_files = get_entry_files(uut, expected_entry_files)
    assert actual_entry_files == expected_entry_files


def build_callable_mock(name):
    mock = MagicMock()
    mock.get_name.return_value = name
    return mock


def get_entry_points(uut, expected_entry_points):
    actual_entry_point_count = max(len(expected_entry_points), uut.entry_points_.rowCount())
    actual_entry_points = [uut.entry_points_.item(i).text() for i in range(actual_entry_point_count)]
    return actual_entry_points


def setup_entry_files(mock, uut, expected_entry_points):
    callables = [build_callable_mock(name) for name in expected_entry_points]
    file_mock = MagicMock()
    file_mock.get_callables.return_value = callables
    mock.patch.object(Index, 'load', return_value=file_mock)
    item = QStandardItem('/irrelevant/path')
    uut.entry_files_.appendRow(item)
    uut.entry_file_list_.setModel(uut.entry_files_)


@pytest.fixture
def selected_mock():
    current = MagicMock()
    current.row.return_value = 0
    return current


def test_dialog_onSelectEntryFile_once__populates_entry_points(mock, selected_mock, uut):
    expected_entry_points = ['void a()', 'void b()']
    setup_entry_files(mock, uut, expected_entry_points)
    uut.onSelectEntryFile(selected_mock, None)
    actual_entry_points = get_entry_points(uut, expected_entry_points)
    assert actual_entry_points == expected_entry_points


def test_dialog_onSelectEntryFile_twice__clears_entry_points_before_populating_again(mock, selected_mock, uut):
    expected_entry_points = ['int b()']
    initial_entry_points = ['void a()', 'void b()', 'void c()']
    setup_entry_files(mock, uut, initial_entry_points)
    uut.onSelectEntryFile(selected_mock, None)
    setup_entry_files(mock, uut, expected_entry_points)
    uut.onSelectEntryFile(selected_mock, None)
    actual_entry_points = get_entry_points(uut, expected_entry_points)
    assert actual_entry_points == expected_entry_points


def test_dialog_onSelectEntryFile_but_nothing_selected__does_not_populate_entry_points(mock, uut):
    uut.entry_point_list_ = MagicMock()
    uut.onSelectEntryFile(None, None)
    uut.entry_point_list_.setModel.assert_not_called()


def test_dialog_reject__quits_application(monkeypatch, uut):
    exit_calls = []
    monkeypatch.setattr(QApplication, 'quit', lambda _: exit_calls.append(1))
    uut.reject()
    assert exit_calls == [1]

# Test List
# =========
# - on accept and if entry point selected show diagram configuration uut
# - on accept and if no entry point selected don't show diagram configuration uut
