# Copyright (C) 2020 R. Knuus

from INCode.clang_access import ClangTUAccess
from tests.test_environment_generation import generate_file
import pytest


def test__given_file_without_compiler_arguments__return_file():
    with generate_file('file.cpp', '') as file_name:
        access = ClangTUAccess(file_name=file_name)
        expected = {file_name: ''}
    actual = access.files
    assert actual == expected


def test__given_file_with_extra_compiler_arguments__return_file_and_args():
    with generate_file('file.cpp', '') as file_name:
        access = ClangTUAccess(file_name=file_name, extra_arguments='-std=c++11')
        expected = {file_name: '-std=c++11'}
    actual = access.files
    assert actual == expected


def test__given_empty_compilation_database__return_empty_dic():
    with generate_file('compile_commands.json', '[]') as file_name:
        access = ClangTUAccess(file_name=file_name)
    expected = {}
    actual = access.files
    assert actual == expected


def test__given_compilation_database_with_one_file__return_file_and_args():
    content = '[{ "command": "-I/usr/include", "file": "file.cpp" }]'
    with generate_file('compile_commands.json', content) as file_name:
        access = ClangTUAccess(file_name=file_name)
    expected = {'file.cpp': ['-I/usr/include']}
    actual = access.files
    assert actual == expected


def test__given_non_existing_file__parse_tu_throws():
    with pytest.raises(FileNotFoundError):
        ClangTUAccess(file_name='a-file-that-doesnt-exist')
