# Copyright (C) 2020 R. Knuus

from INCode.call_tree_manager import CallTreeManager
from tests.test_environment_generation import generate_file
import pytest


def test_given_call_tree_depth_of_two__dump_returns_extected_output():
    manager = CallTreeManager()
    excepted = 'f()\n  g()\n'
    with generate_file('two-functions.cpp', 'void g() {}\nvoid f() {g();}') as file_name:
        actual = manager.dump(file_name, 'f()')
    assert actual == excepted


def test_given_source_file__open_returns_tu_list_with_one_item():
    manager = CallTreeManager()
    with generate_file('file.cpp', '') as file_name:
        tu_list = manager.open(file_name)
    assert len(tu_list) == 1


def test_given_tu_with_one_function__select_tu_returns_list_with_one_item():
    manager = CallTreeManager()
    with generate_file('file.cpp', 'void f();') as file_name:
        manager.open(file_name)
        callable_list = manager.select_tu(file_name)
    assert len(callable_list) == 1


def test_given_werror_extra_argument_and_tu_with_unused_parameter__select_tu_fails():
    manager = CallTreeManager()
    manager.set_extra_arguments('-Werror -Wunused-parameter')
    with generate_file('file.cpp', 'void f(int i) {}') as file_name:
        with pytest.raises(SyntaxError):
            manager.open(file_name)
            manager.select_tu(file_name)


def test_given_tu_with_include__select_tu_returns_only_callables_in_main_file():
    manager = CallTreeManager()
    with generate_file('include.h', 'void f() {}') as include_file_name:
        with generate_file('main_file.cpp', '#include "{}"\nvoid g();'.format(include_file_name)) as main_file_name:
            manager.open(main_file_name)
            callable_list = manager.select_tu(main_file_name)
    assert len(callable_list) == 1
