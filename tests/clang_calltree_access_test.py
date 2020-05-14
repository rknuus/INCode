# Copyright (C) 2020 R. Knuus


from INCode.clang_calltree_access import ClangCalltreeAccess
from tests.test_environment_generation import generate_tu
import pytest


def test__given_one_function__parse_tree_with_one_element():
    engine = ClangCalltreeAccess()
    with generate_tu('one-function.cpp', 'void f() {}') as file_name:
        engine.parse_tu(tu=file_name, compiler_arguments='')
    assert len(engine.call_tree) == 1


def test__given_two_functions__parse_tree_with_two_elements():
    engine = ClangCalltreeAccess()
    with generate_tu('two-functions.cpp', 'void f() {}\nvoid g() {}') as file_name:
        engine.parse_tu(tu=file_name, compiler_arguments='')
    assert len(engine.call_tree) == 2


def test__given_a_function__parse_tree_containts_function_name():
    engine = ClangCalltreeAccess()
    with generate_tu('two-functions.cpp', 'void f() {}') as file_name:
        engine.parse_tu(tu=file_name, compiler_arguments='')
    expected = ['f()']
    actual = engine.call_tree
    assert expected == actual


def test__given_non_existing_file__parse_tree_throws():
    engine = ClangCalltreeAccess()
    with pytest.raises(OSError):
        engine.parse_tu(tu='a-file-that-doesnt-exist', compiler_arguments='')


def test__given_file_with_syntax_error__parse_tree_throws():
    engine = ClangCalltreeAccess()
    with generate_tu('syntax-error.cpp', 'void f() {') as file_name:
        with pytest.raises(SyntaxError):
            engine.parse_tu(tu=file_name, compiler_arguments='')
