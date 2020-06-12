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


def test_given_tu_with_two_functions__get_calls_of_returns_one_callable():
    manager = CallTreeManager()
    with generate_file('file.cpp', 'void f();\nvoid g() { f(); }') as file_name:
        manager.open(file_name)
        manager.select_tu(file_name)
    unexpected_children = manager.get_calls_of('f()')
    expected_children = manager.get_calls_of('g()')
    assert len(unexpected_children) == 0
    assert len(expected_children) == 1


def test_given_tu_with_tree_three_functions_deep__tree_of_select_root_on_middle_function_has_depth_two():
    manager = CallTreeManager()
    content = 'void f();\nvoid g() { f(); }\nvoid h() { g(); }\n'
    with generate_file('file.cpp', content) as file_name:
        manager.open(file_name)
        manager.select_tu(file_name)
        root = manager.select_root('g()')
    children = manager.get_calls_of(root.name)
    assert len(children) == 1
    grand_children = manager.get_calls_of(children[0].name)
    assert len(grand_children) == 0


def test_given_tu_referencing_function_in_other_tu__load_definition_grows_call_tree():
    manager = CallTreeManager()
    with generate_file('g.cpp', 'extern void f();\nvoid g() { f(); }') as file_name:
        manager.open(file_name)
        manager.select_tu(file_name)
        root = manager.select_root('g()')
    with generate_file('f.cpp', 'void f() { f(); }\n') as file_name:
        manager.open(file_name)  # TODO(KNR): a hack, use a compilation DB instead
        manager.load_definition('f()')
    children = manager.get_calls_of(root.name)
    grand_children = manager.get_calls_of(children[0].name)
    assert len(grand_children) == 1


def test_given_no_callable_included__export_returns_empty_diagram():
    manager = CallTreeManager()
    with generate_file('file.cpp', 'void f();\nvoid g() { f(); }') as file_name:
        manager.open(file_name)
        manager.select_tu(file_name)
    manager.select_root('g()')
    expected = '@startuml\n\n\n@enduml'
    actual = manager.export()
    assert actual == expected


def test_given_two_functions_included__export_returns_diagram_with_call():
    manager = CallTreeManager()
    with generate_file('file.cpp', 'void f();\nvoid g() { f(); }') as file_name:
        manager.open(file_name)
        manager.select_tu(file_name)
    manager.select_root('g()')
    manager.include('g()')
    manager.include('f()')
    expected = '@startuml\n\n -> "file.cpp": "g()"\n"file.cpp" -> "file.cpp": "f()"\n\n@enduml'
    actual = manager.export()
    assert actual == expected


def test_given_included_function_excluded_again__export_returns_diagram_with_call():
    manager = CallTreeManager()
    with generate_file('file.cpp', 'void f();\nvoid g() { f(); }') as file_name:
        manager.open(file_name)
        manager.select_tu(file_name)
    manager.select_root('g()')
    manager.include('g()')
    manager.include('f()')
    manager.exclude('g()')
    expected = '@startuml\n\n -> "file.cpp": "f()"\n\n@enduml'
    actual = manager.export()
    assert actual == expected


def test_given_call_graph_of_depth_two__functions_exported_depth_first():
    manager = CallTreeManager()
    with generate_file('file.cpp', 'void i();\nvoid h();\nvoid g() { h(); }\nvoid f() { g();\ni(); }') as file_name:
        manager.open(file_name)
        manager.select_tu(file_name)
    manager.select_root('f()')
    manager.include('f()')
    manager.include('g()')
    manager.include('h()')
    manager.include('i()')
    expected = '@startuml\n\n -> "file.cpp": "f()"\n"file.cpp" -> "file.cpp": "g()"\n"file.cpp" -> "file.cpp": "h()"\n"file.cpp" -> "file.cpp": "i()"\n\n@enduml'
    actual = manager.export()
    assert actual == expected


def test_given_methods_of_same_class__use_class_as_participant():
    manager = CallTreeManager()
    with generate_file('file.cpp', 'class Foo {\nvoid bar();\nvoid baz() { bar(); }\n};') as file_name:
        manager.open(file_name)
        manager.select_tu(file_name)
    manager.select_root('Foo::baz()')
    manager.include('Foo::baz()')
    manager.include('Foo::bar()')
    expected = '@startuml\n\n -> "Foo": "baz()"\n"Foo" -> "Foo": "bar()"\n\n@enduml'
    actual = manager.export()
    assert actual == expected
