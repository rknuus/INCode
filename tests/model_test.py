# Copyright (C) 2018 R. Knuus

from INCode.models import Callable, File, Index
from unittest.mock import MagicMock
import os
import pytest
import tempfile


def generate_project(directory, files):
    for file, content in files.items():
        generate_file(directory, file, content)
    generate_compilation_database(directory, files.keys())


def generate_file(directory, file, content):
    with open(os.path.join(directory, file), 'w') as file:
        file.write(content)


def generate_compilation_database(directory, source_files):
    entries = []
    for source_file in source_files:
        entry = ('{ "directory": "%(directory)s", "command": "clang++ -o %(source_file)s.o -c %(source_file)s", '
                 '"file": "%(source_file)s" }' % locals())
        entries.append(entry)
    content = '[{}]'.format(','.join(entries))
    generate_file(directory, 'compile_commands.json', content)


@pytest.fixture(scope='module')
def directory():
    with tempfile.TemporaryDirectory() as fixture_directory:
        yield fixture_directory


@pytest.fixture(scope='module')
def two_translation_units():
    with tempfile.TemporaryDirectory('two_translation_units') as directory:
        generate_project(directory, {
            os.path.join(directory, 'dependency.h'): '''
                      #pragma once
                      void a();
                      ''',
            os.path.join(directory, 'dependency.cpp'): '''
                      #include "dependency.h"
                      void a() {}
                      ''',
            os.path.join(directory, 'cross_tu_referencing_function.cpp'): '''
                      #include "dependency.h"
                      void b() {
                          a();
                      }
                      '''
        })
        yield directory


@pytest.fixture(scope='module')
def local_and_xref_dep():
    with tempfile.TemporaryDirectory('local_and_xref_dep') as directory:
        generate_project(directory, {
            os.path.join(directory, 'dependency.h'): '''
                      #pragma once
                      void a();
                      ''',
            os.path.join(directory, 'dependency.cpp'): '''
                      #include "dependency.h"
                      void c() {}
                      void a() {
                          c();
                      }
                      ''',
            os.path.join(directory, 'cross_tu_referencing_function.cpp'): '''
                      #include "dependency.h"
                      void b() {
                          a();
                      }
                      '''
        })
        yield directory


def test__index__add_compilation_database__can_get_list_of_translation_units(directory):
    generate_project(directory, {'foo.cpp': '\n', 'bar.cpp': '\n'})
    index = Index()
    index.add_compilation_database(directory)
    files = index.get_files()
    assert 'foo.cpp' in files
    assert 'bar.cpp' in files


def test__index__get_callables_for_empty_file__returns_empty_list(directory):
    file = os.path.join(directory, 'empty.cpp')
    generate_project(directory, {file: '\n'})
    index = Index()
    index.add_compilation_database(directory)
    file = index.load(file)
    assert list(file.get_callables()) == []


def test__index__get_callables_for_file_with_one_function__returns_that_function(directory):
    file = os.path.join(directory, 'one_function.cpp')
    generate_project(directory, {file: 'void a() {}\n'})
    index = Index()
    index.add_compilation_database(directory)
    file = index.load(file)
    callables = file.get_callables()
    assert len(callables) == 1
    assert callables[0].get_name() == 'void a()'


def test__file__get_callables_for_file_with_two_functions__returns_both_functions(directory):
    file = os.path.join(directory, 'two_functions.cpp')
    generate_project(directory, {file: 'void a() {}\nvoid b(const int i) {}\n'})
    index = Index()
    index.add_compilation_database(directory)
    file = index.load(file)
    callables = file.get_callables()
    assert len(callables) == 2
    assert callables[0].get_name() == 'void a()'
    assert callables[1].get_name() == 'void b(const int)'


def test__file__get_callables_for_declared_and_then_defined_function__returns_only_definition(directory):
    file = os.path.join(directory, 'declare_and_then_define_function.cpp')
    generate_project(directory, {file: 'void a();\nvoid a() {}\n'})
    index = Index()
    index.add_compilation_database(directory)
    file = index.load(file)
    callables = file.get_callables()
    assert len(callables) == 1
    assert callables[0].get_name() == 'void a()'
    assert callables[0].is_definition()


def test__callable__get_referenced_callables_for_empty_function__returns_empty_list(directory):
    file = os.path.join(directory, 'non_referencing_function.cpp')
    generate_project(directory, {file: 'void a() {}\n'})
    index = Index()
    index.add_compilation_database(directory)
    file = index.load(file)
    callable = file.get_callables()[0]
    assert callable.get_referenced_callables() == []


def test__callable__get_referenced_callables_for_function_calling_another_one__returns_that_function(directory):
    file = os.path.join(directory, 'referencing_function.cpp')
    generate_project(directory, {file: 'void a() {}\nvoid b() {\na();\n}\n'})
    index = Index()
    index.add_compilation_database(directory)
    file = index.load(file)
    callables = file.get_callables()
    callable = callables[1]
    referenced_callables = callable.get_referenced_callables()
    assert len(referenced_callables) == 1
    assert referenced_callables[0].get_name() == 'void a()'


def test__callable__get_referenced_callables_for_function_calling_two_others__returns_both_function(directory):
    file = os.path.join(directory, 'double_referencing_function.cpp')
    generate_project(directory, {file: 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n'})
    index = Index()
    index.add_compilation_database(directory)
    file = index.load(file)
    callables = file.get_callables()
    callable = callables[2]
    referenced_callables = callable.get_referenced_callables()
    assert len(referenced_callables) == 2
    assert referenced_callables[0].get_name() == 'void a()'
    assert referenced_callables[1].get_name() == 'void b()'


def test__callable__get_referenced_callables_of_another_file__returns_that_function(two_translation_units):
    index = Index()
    index.add_compilation_database(two_translation_units)
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    from pdb import set_trace
    set_trace()
    file = index.load(cross_tu)
    callables = file.get_callables()
    callable = callables[1]
    referenced_callables = callable.get_referenced_callables()
    assert len(referenced_callables) == 1
    assert referenced_callables[0].get_name() == 'void a()'


def test__callable__get_referenced_callables_for_referenced_function_in_same_file__returns_that_definition(directory):
    file = os.path.join(directory, 'identify_local_function.cpp')
    generate_project(directory, {file: 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n'})
    index = Index()
    index.add_compilation_database(directory)
    file = index.load(file)
    callables = file.get_callables()
    callable = callables[2]
    referenced_callables = callable.get_referenced_callables()
    assert len(referenced_callables) == 2
    assert referenced_callables[0].get_usr() == 'c:@F@a#'
    assert referenced_callables[1].get_usr() == 'c:@F@b#'


def test__callable__get_referenced_callables_for_recursive_function__returns_only_definition(directory):
    file = os.path.join(directory, 'recursive_function.cpp')
    generate_project(directory, {file: 'void a();\nvoid a() {\n  a();\n}\n'})
    index = Index()
    index.add_compilation_database(directory)
    file = index.load(file)
    callables = file.get_callables()
    callable = callables[0]
    referenced_callables = callable.get_referenced_callables()
    nested_referenced_callables = referenced_callables[0].get_referenced_callables()
    assert len(referenced_callables) == 1
    assert referenced_callables[0].get_name() == 'void a()'


def test__index__load_translation_unit__registers_callables_in_index(directory):
    tu = os.path.join(directory, 'identify_local_function.cpp')
    generate_project(directory, {tu: 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n'})
    index = Index()
    index.add_compilation_database(directory)
    index.load(tu)
    assert index.callable_table_['c:@F@a#'].cursor_.location.file.name == tu
    assert index.callable_table_['c:@F@b#'].cursor_.location.file.name == tu
    assert index.callable_table_['c:@F@c#'].cursor_.location.file.name == tu


def test__index__load_tu_referencing_function_in_another_file__registers_callable_in_header(two_translation_units):
    index = Index()
    index.add_compilation_database(two_translation_units)
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    dep_header = os.path.join(two_translation_units, 'dependency.h')
    index.load(cross_tu)
    assert index.callable_table_['c:@F@a#'].cursor_.location.file.name == dep_header
    assert index.callable_table_['c:@F@b#'].cursor_.location.file.name == cross_tu


def test__index__load_tu_referencing_function_in_another_file__registration_not_overwritten(two_translation_units):
    index = Index()
    index.add_compilation_database(two_translation_units)
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    dep_tu = os.path.join(two_translation_units, 'dependency.cpp')
    index.load(dep_tu)
    assert index.callable_table_['c:@F@a#'].cursor_.location.file.name == dep_tu
    index.load(cross_tu)
    assert index.callable_table_['c:@F@a#'].cursor_.location.file.name == dep_tu
    assert index.callable_table_['c:@F@b#'].cursor_.location.file.name == cross_tu


def test__index__load_declaration_first_then_load_definition__get_function(local_and_xref_dep):
    index = Index()
    index.add_compilation_database(local_and_xref_dep)
    cross_tu = os.path.join(local_and_xref_dep, 'cross_tu_referencing_function.cpp')
    index.load(cross_tu)
    with pytest.raises(KeyError):
        index.callable_table_['c:@F@c#']
    dep_tu = os.path.join(local_and_xref_dep, 'dependency.cpp')
    index.load(dep_tu)
    assert index.callable_table_['c:@F@c#'].cursor_.location.file.name == dep_tu


def test__index__lookup_unknown_function__function_is_not_in_index():
    index = Index()
    with pytest.raises(KeyError):
        index.callable_table_['foo']


def test__index__register_function__function_is_in_index():
    cursor_mock = MagicMock()
    cursor_mock.get_usr.return_value = 'foo'
    index = Index()
    index.register(cursor_mock)
    assert index.callable_table_['foo']


def test__index__load_definition_for_function_defined_in_other_file__returns_definition(two_translation_units):
    index = Index()
    index.add_compilation_database(two_translation_units)
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    index.load(cross_tu)
    declaration = index.callable_table_['c:@F@a#']
    definition = index.load_definition(declaration)
    assert not declaration.is_definition()
    assert definition.is_definition()


def test__scenario__select_entry_location_and_follow_references__data_model_is_correct(local_and_xref_dep):
    index = Index()
    index.add_compilation_database(local_and_xref_dep)
    cross_tu = os.path.join(local_and_xref_dep, 'cross_tu_referencing_function.cpp')
    dep_tu = os.path.join(local_and_xref_dep, 'dependency.cpp')
    files = index.get_files()
    assert cross_tu in files
    assert dep_tu in files

    entry_file = index.load(cross_tu)
    callables = entry_file.get_callables()
    assert len(callables) == 2
    assert 'void b()' == callables[1].get_name()

    referenced_callables = callables[1].get_referenced_callables()
    assert len(referenced_callables) == 1
    assert 'void a()' == referenced_callables[0].get_name()
    assert not referenced_callables[0].is_definition()

    cross_definition = index.load_definition(referenced_callables[0])
    assert 'void a()' == cross_definition.get_name()

    local_xref = cross_definition.get_referenced_callables()
    assert len(local_xref) == 1
    assert 'void c()' == local_xref[0].get_name()
    assert local_xref[0].is_definition()

    no_more_xref = local_xref[0].get_referenced_callables()
    assert len(no_more_xref) == 0


def test__callable__check_whether_included__default_is_excluded():
    callable = Callable('foo', MagicMock(), MagicMock())
    assert not callable.is_included()


def test__callable__include_and_check_whether_included__return_included():
    callable = Callable('foo', MagicMock(), MagicMock())
    callable.include()
    assert callable.is_included()


def test__callable__include_then_exclude_and_check_whether_included__return_included():
    callable = Callable('foo', MagicMock(), MagicMock())
    callable.include()
    callable.exclude()
    assert not callable.is_included()


def test__callable__export_included_parent_calling_included_child__export_correct_diagram():
    index = MagicMock()
    parent_cursor = MagicMock()
    parent_cursor.translation_unit.spelling = 'foo.cpp'
    parent = Callable('foo', parent_cursor, index)
    child_cursor = MagicMock()
    child_cursor.translation_unit.spelling = 'bar.cpp'
    child = Callable('baz', child_cursor, index)
    parent.include()
    child.include()
    parent.referenced_usrs_.append(child.get_usr())
    diagram = parent.export()
    expected_diagram = '''@startuml

foo.cpp -> bar.cpp: baz

@enduml'''

    assert diagram == expected_diagram


def test__callable__export_included_parent_calling_excluded_child__export_correct_diagram():
    index = MagicMock()
    parent_cursor = MagicMock()
    parent_cursor.translation_unit.spelling = 'foo.cpp'
    parent = Callable('foo', parent_cursor, index)
    child_cursor = MagicMock()
    child_cursor.translation_unit.spelling = 'bar.cpp'
    child = Callable('baz', child_cursor, index)
    parent.include()
    child.exclude()
    parent.referenced_usrs_.append(child.get_usr())
    diagram = parent.export()
    expected_diagram = '''@startuml


@enduml'''

    assert diagram == expected_diagram


def test__callable__export_excluded_parent_calling_included_child__export_correct_diagram():
    index = MagicMock()
    parent_cursor = MagicMock()
    parent_cursor.translation_unit.spelling = 'foo.cpp'
    parent = Callable('foo', parent_cursor, index)
    child_cursor = MagicMock()
    child_cursor.translation_unit.spelling = 'bar.cpp'
    child = Callable('baz', child_cursor, index)
    parent.exclude()
    child.include()
    parent.referenced_usrs_.append(child.get_usr())
    diagram = parent.export()
    expected_diagram = '''@startuml

 -> bar.cpp: baz

@enduml'''

    assert diagram == expected_diagram


def test__callable__export_two_included_child_levels__export_correct_diagram():
    index = MagicMock()
    grandparent_cursor = MagicMock()
    grandparent_cursor.translation_unit.spelling = 'foo.cpp'
    grandparent = Callable('foo', grandparent_cursor, index)
    parent_cursor = MagicMock()
    parent_cursor.translation_unit.spelling = 'bar.cpp'
    parent = Callable('baz', parent_cursor, index)
    child_cursor = MagicMock()
    child_cursor.translation_unit.spelling = 'bar.cpp'
    child = Callable('bar', child_cursor, index)
    grandparent.include()
    parent.include()
    child.include()
    grandparent.referenced_usrs_.append(parent.get_usr())
    parent.referenced_usrs_.append(child.get_usr())
    diagram = grandparent.export()
    expected_diagram = '''@startuml

foo.cpp -> bar.cpp: baz
bar.cpp -> bar.cpp: bar

@enduml'''

    assert diagram == expected_diagram

# TODO(KNR): simplify diagram tests by factoring out common code


def test__callable__export_grandparent_and_child_but_not_parent__export_correct_diagram():
    index = MagicMock()
    grandparent_cursor = MagicMock()
    grandparent_cursor.translation_unit.spelling = 'foo.cpp'
    grandparent = Callable('foo', grandparent_cursor, index)
    parent_cursor = MagicMock()
    parent_cursor.translation_unit.spelling = 'bar.cpp'
    parent = Callable('baz', parent_cursor, index)
    child_cursor = MagicMock()
    child_cursor.translation_unit.spelling = 'bar.cpp'
    child = Callable('bar', child_cursor, index)
    grandparent.include()
    parent.exclude()
    child.include()
    grandparent.referenced_usrs_.append(parent.get_usr())
    parent.referenced_usrs_.append(child.get_usr())
    diagram = grandparent.export()
    expected_diagram = '''@startuml

foo.cpp -> bar.cpp: bar

@enduml'''

    assert diagram == expected_diagram


def test__callable__export_definition_loaded_over_declaration__export_correct_diagram(two_translation_units):
    index = Index()
    index.add_compilation_database(two_translation_units)
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    dep_tu = os.path.join(two_translation_units, 'dependency.cpp')
    index.load(dep_tu)
    index.load(cross_tu)
    parent = index.lookup('c:@F@b#')
    child = index.lookup('c:@F@a#')
    parent.include()
    child.include()
    diagram = parent.export()
    expected_diagram = '''@startuml

{} -> {}: void a()

@enduml'''.format(cross_tu, dep_tu)

    assert diagram == expected_diagram
