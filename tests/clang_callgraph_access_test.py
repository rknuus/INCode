# Copyright (C) 2020 R. Knuus


from INCode.clang_access import ClangCallGraphAccess
from tests.test_environment_generation import generate_file
import pytest


def get_names_of_calls(calls):
    return [callable.name for callable in calls]


def test__given_function_without_calls__get_empty_calls_list():
    access = ClangCallGraphAccess()
    with generate_file('one-function.cpp', 'void f() {}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
    expected = []
    actual = access.get_calls_of('f()')
    assert expected == actual


def test_given_unknown_entry_point__get_empty_calls_list():
    access = ClangCallGraphAccess()
    with generate_file('one-function.cpp', 'void f() {}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
    expected = []
    actual = access.get_calls_of('g()')
    assert expected == actual


def test__given_function_calling_another__parse_tu_contains_call():
    access = ClangCallGraphAccess()
    with generate_file('two-functions.cpp', 'void f() {}\nvoid g() {f();}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
    expected = ['f()']
    actual = get_names_of_calls(access.get_calls_of('g()'))
    assert expected == actual


def test__given_recursive_function_call__parse_tu_contains_recursion():
    access = ClangCallGraphAccess()
    with generate_file('two-functions.cpp', 'void f();\nvoid f() {f();}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
    expected = ['f()']
    actual = get_names_of_calls(access.get_calls_of('f()'))
    assert expected == actual


def test__given_non_existing_file__parse_tu_throws():
    access = ClangCallGraphAccess()
    with pytest.raises(FileNotFoundError):
        access.parse_tu(tu_file_name='a-file-that-doesnt-exist', compiler_arguments='')


def test__given_file_with_syntax_error__parse_tu_throws():
    access = ClangCallGraphAccess()
    with generate_file('syntax-error.cpp', 'void f() {') as file_name:
        with pytest.raises(SyntaxError):
            access.parse_tu(tu_file_name=file_name, compiler_arguments='')


def test__given_parsed_tu_with_one_function__callables_contains_one_item():
    access = ClangCallGraphAccess()
    with generate_file('syntax-error.cpp', 'void f() {}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
    callables = access.callables
    assert len(callables) == 1


def test__given_parsed_tu_with_one_function__get_callables_in_returns_one_callable():
    access = ClangCallGraphAccess()
    with generate_file('one-function.cpp', 'void f() {}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
        callables = access.get_callables_in(file_name)
    assert len(callables) == 1


def test__given_parsed_tu_with_one_function__get_callable_returns_callable_with_expected_name():
    access = ClangCallGraphAccess()
    with generate_file('one-function.cpp', 'void f() {}') as file_name:
        access.parse_tu(tu_file_name=file_name, compiler_arguments='')
        callable = access.get_callable('f()')
    expected = 'f()'
    actual = callable.name
    assert expected == actual
