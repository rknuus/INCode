# Copyright (C) 2020 R. Knuus


from INCode.clang_access import ClangCallGraphAccess
from tests.test_environment_generation import generate_file
import pytest


def test__given_function_without_calls__get_empty_calls_list():
    access = ClangCallGraphAccess()
    with generate_file('one-function.cpp', 'void f() {}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
    expected = []
    actual = access.get_calls_of('f()')
    assert expected == actual


def test__given_function_calling_another__parse_tu_contains_call():
    access = ClangCallGraphAccess()
    with generate_file('two-functions.cpp', 'void f() {}\nvoid g() {f();}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
    expected = ['f()']
    actual = access.get_calls_of('g()')
    assert expected == actual


def test__given_recursive_function_call__parse_tu_contains_recursion():
    access = ClangCallGraphAccess()
    with generate_file('two-functions.cpp', 'void f();\nvoid f() {f();}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
    expected = ['f()']
    actual = access.get_calls_of('f()')
    assert expected == actual


def test__given_non_existing_file__parse_tu_throws():
    access = ClangCallGraphAccess()
    with pytest.raises(OSError):
        access.parse_tu(tu_file_name='a-file-that-doesnt-exist', compiler_arguments='')


def test__given_file_with_syntax_error__parse_tu_throws():
    access = ClangCallGraphAccess()
    with generate_file('syntax-error.cpp', 'void f() {') as file_name:
        with pytest.raises(SyntaxError):
            access.parse_tu(tu_file_name=file_name, compiler_arguments='')


def test_given_unknown_entry_point__dump_throws():
    access = ClangCallGraphAccess()
    with generate_file('one-function.cpp', 'void f() {}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
    with pytest.raises(KeyError):
        access.get_calls_of('g()')
