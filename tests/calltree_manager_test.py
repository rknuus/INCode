# Copyright (C) 2020 R. Knuus

from INCode.call_tree_manager import CallTreeManager
from tests.test_environment_generation import generate_file


def test_given_call_tree_depth_of_two__dump_returns_extected_output():
    manager = CallTreeManager()
    excepted = 'f()\n  g()\n'
    with generate_file('two-functions.cpp', 'void g() {}\nvoid f() {g();}') as file_name:
        actual = manager.dump(file_name, 'f()')
    assert actual == excepted
