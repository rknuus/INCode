# Copyright (C) 2020 R. Knuus

from INCode.call_tree_manager import CallTreeManager
from tests.test_environment_generation import generate_file


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
        callable_list = manager.select_tu(file_name)
    assert len(callable_list) == 1
