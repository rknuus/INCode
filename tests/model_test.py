# Copyright (C) 2018 R. Knuus

from clang.cindex import CursorKind
from INCode.models import Callable, CompilationDatabases, File, Index
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


def test__compilation_database__add_compilation_database__can_get_list_of_translation_units(directory):
    generate_project(directory, {'foo.cpp': '\n', 'bar.cpp': '\n'})
    db = CompilationDatabases()
    db.add_compilation_database(directory)
    files = db.get_files()
    assert 'foo.cpp' in files
    assert 'bar.cpp' in files


def build_index_with_file(directory, file_name, file_content):
    file_path = os.path.join(directory, 'empty.cpp')
    generate_project(directory, {file_path: file_content})
    db = CompilationDatabases()
    db.add_compilation_database(directory)
    index = Index(db)
    file = index.load(file_path)
    return index, file


def test__file__get_callables_for_empty_file__returns_empty_list(directory):
    _, file = build_index_with_file(directory, 'empty.cpp', '\n')
    assert list(file.get_callables()) == []


def get_callable_names(callables):
    return [callable.get_name() for callable in callables]


def test__file__get_callables_for_file_with_one_function__returns_that_function(directory):
    _, file = build_index_with_file(directory, 'one_function.cpp', 'void a() {}\n')
    callables = file.get_callables()
    assert get_callable_names(callables) == ['void a()']


def test__file__get_callables_for_file_with_two_functions__returns_both_functions(directory):
    _, file = build_index_with_file(directory, 'two_functions.cpp', 'void a() {}\nvoid b(const int i) {}\n')
    callables = file.get_callables()
    assert get_callable_names(callables) == ['void a()', 'void b(const int)']


def test__file__get_callables_for_declared_and_then_defined_function__returns_only_definition(directory):
    _, file = build_index_with_file(directory, 'declare_and_then_define_function.cpp', 'void a();\nvoid a() {}\n')
    callables = file.get_callables()
    assert get_callable_names(callables) == ['void a()']
    assert [callable.is_definition() for callable in callables] == [True]


def test__callable__get_referenced_callables_for_empty_function__returns_empty_list(directory):
    _, file = build_index_with_file(directory, 'non_referencing_function.cpp', 'void a() {}\n')
    callable = file.get_callables()[0]
    assert callable.get_referenced_callables() == []


def test__callable__get_referenced_callables_for_function_calling_another_one__returns_that_function(directory):
    _, file = build_index_with_file(directory, 'referencing_function.cpp', 'void a() {}\nvoid b() {\na();\n}\n')
    callable = file.get_callables()[1]
    referenced_callables = callable.get_referenced_callables()
    assert get_callable_names(referenced_callables) == ['void a()']


def test__callable__get_referenced_callables_for_function_calling_two_others__returns_both_function(directory):
    _, file = build_index_with_file(directory, 'double_referencing_function.cpp',
                                    'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')
    callable = file.get_callables()[2]
    referenced_callables = callable.get_referenced_callables()
    assert get_callable_names(referenced_callables) == ['void a()', 'void b()']


def test__callable__get_referenced_callables_of_another_file__returns_that_function(two_translation_units):
    db = CompilationDatabases()
    db.add_compilation_database(two_translation_units)
    index = Index(db)
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    file = index.load(cross_tu)
    callable = file.get_callables()[1]
    referenced_callables = callable.get_referenced_callables()
    assert get_callable_names(referenced_callables) == ['void a()']


def test__callable__get_referenced_callables_for_referenced_function_in_same_file__returns_that_definition(directory):
    _, file = build_index_with_file(directory, 'identify_local_function.cpp',
                                    'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')
    callable = file.get_callables()[2]
    referenced_callables = callable.get_referenced_callables()
    assert get_callable_names(referenced_callables) == ['void a()', 'void b()']


def test__callable__get_referenced_callables_for_recursive_function__returns_only_definition(directory):
    _, file = build_index_with_file(directory, 'recursive_function.cpp', 'void a();\nvoid a() {\n  a();\n}\n')
    callable = file.get_callables()[0]
    referenced_callables = callable.get_referenced_callables()
    assert get_callable_names(referenced_callables) == ['void a()']


def test__index__lookup_unknown_function__function_is_not_in_index():
    index = Index(None)
    assert index.lookup('foo') is None


def test__index__load_translation_unit__registers_callables_in_index(directory):
    index, _ = build_index_with_file(directory, 'identify_local_function.cpp',
                                     'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')
    assert index.lookup('c:@F@a#') is not None
    assert index.lookup('c:@F@b#') is not None
    assert index.lookup('c:@F@c#') is not None


def test__index__load_tu_referencing_function_in_another_file__registers_callable_in_header(two_translation_units):
    db = CompilationDatabases()
    db.add_compilation_database(two_translation_units)
    index = Index(db)
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    dep_header = os.path.join(two_translation_units, 'dependency.h')
    index.load(cross_tu)
    assert index.callable_table_['c:@F@a#'].cursor_.location.file.name == dep_header
    assert index.callable_table_['c:@F@b#'].cursor_.location.file.name == cross_tu


def test__index__load_tu_referencing_function_in_another_file__registration_not_overwritten(two_translation_units):
    db = CompilationDatabases()
    db.add_compilation_database(two_translation_units)
    index = Index(db)
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    dep_tu = os.path.join(two_translation_units, 'dependency.cpp')
    index.load(dep_tu)
    assert index.callable_table_['c:@F@a#'].cursor_.location.file.name == dep_tu
    index.load(cross_tu)
    assert index.callable_table_['c:@F@a#'].cursor_.location.file.name == dep_tu
    assert index.callable_table_['c:@F@b#'].cursor_.location.file.name == cross_tu


def test__index__load_declaration_first_then_load_definition__get_function(local_and_xref_dep):
    db = CompilationDatabases()
    db.add_compilation_database(local_and_xref_dep)
    index = Index(db)
    cross_tu = os.path.join(local_and_xref_dep, 'cross_tu_referencing_function.cpp')
    index.load(cross_tu)
    assert index.lookup('c:@F@c#') is None
    dep_tu = os.path.join(local_and_xref_dep, 'dependency.cpp')
    index.load(dep_tu)
    assert index.lookup('c:@F@c#') is not None


def test__index__register_function__function_is_in_index():
    cursor_mock = MagicMock()
    cursor_mock.get_id.return_value = 'foo'
    index = Index(None)
    index.register(cursor_mock)
    assert index.lookup('foo') is not None


def test__index__load_definition_for_function_defined_in_other_file__returns_definition(two_translation_units):
    db = CompilationDatabases()
    db.add_compilation_database(two_translation_units)
    index = Index(db)
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    index.load(cross_tu)
    declaration = index.callable_table_['c:@F@a#']
    definition = index.load_definition(declaration)
    assert not declaration.is_definition()
    assert definition.is_definition()


def test__scenario__select_entry_location_and_follow_references__data_model_is_correct(local_and_xref_dep):
    db = CompilationDatabases()
    db.add_compilation_database(local_and_xref_dep)
    files = db.get_files()
    cross_tu = os.path.join(local_and_xref_dep, 'cross_tu_referencing_function.cpp')
    dep_tu = os.path.join(local_and_xref_dep, 'dependency.cpp')
    assert cross_tu in files
    assert dep_tu in files

    index = Index(db)
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


def build_callable():
    return Callable(MagicMock(), MagicMock())


def test__callable__check_whether_included__default_is_excluded():
    callable = build_callable()
    assert not callable.is_included()


def test__callable__include_and_check_whether_included__return_included():
    callable = build_callable()
    callable.include()
    assert callable.is_included()


def test__callable__include_then_exclude_and_check_whether_included__return_included():
    callable = build_callable()
    callable.include()
    callable.exclude()
    assert not callable.is_included()


def build_cursor(file, return_value, signature, kind):
    cursor = MagicMock()
    cursor.translation_unit.spelling = file
    cursor.result_type.spelling = return_value
    cursor.displayname = signature
    cursor.kind = kind
    return cursor


def test__callable__export_included_parent_calling_included_child__export_correct_diagram():
    index = MagicMock()
    parent = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    child = Callable(build_cursor('bar.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL), index)
    parent.referenced_usrs_.append(child.get_id())
    index.lookup.return_value = child
    parent.include()
    child.include()
    diagram = parent.export()
    expected_diagram = '''@startuml

foo.cpp -> bar.cpp: void baz()

@enduml'''

    assert diagram == expected_diagram


def test__callable__export_included_parent_calling_excluded_child__export_correct_diagram():
    index = MagicMock()
    parent = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    child = Callable(build_cursor('bar.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL), index)
    parent.referenced_usrs_.append(child.get_id())
    index.lookup.return_value = child
    parent.include()
    child.exclude()
    diagram = parent.export()
    expected_diagram = '''@startuml


@enduml'''

    assert diagram == expected_diagram


def test__callable__export_excluded_parent_calling_included_child__export_correct_diagram():
    index = MagicMock()
    parent = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    child = Callable(build_cursor('bar.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL), index)
    parent.referenced_usrs_.append(child.get_id())
    index.lookup.return_value = child
    parent.exclude()
    child.include()
    diagram = parent.export()
    expected_diagram = '''@startuml

 -> bar.cpp: void baz()

@enduml'''

    assert diagram == expected_diagram


def test__callable__export_two_included_child_levels__export_correct_diagram():
    index = MagicMock()
    grandparent = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    parent = Callable(build_cursor('bar.cpp', 'void', 'bar()', CursorKind.FUNCTION_DECL), index)
    child = Callable(build_cursor('baz.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL), index)
    grandparent.referenced_usrs_.append(parent.get_id())
    parent.referenced_usrs_.append(child.get_id())
    index.lookup.side_effect = [parent, child]
    grandparent.include()
    parent.include()
    child.include()
    diagram = grandparent.export()
    expected_diagram = '''@startuml

foo.cpp -> bar.cpp: void bar()
bar.cpp -> baz.cpp: void baz()

@enduml'''

    assert diagram == expected_diagram

# # TODO(KNR): simplify diagram tests by factoring out common code


def test__callable__export_grandparent_and_child_but_not_parent__export_correct_diagram():
    index = MagicMock()
    grandparent = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    parent = Callable(build_cursor('bar.cpp', 'void', 'bar()', CursorKind.FUNCTION_DECL), index)
    child = Callable(build_cursor('baz.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL), index)
    grandparent.referenced_usrs_.append(parent.get_id())
    parent.referenced_usrs_.append(child.get_id())
    index.lookup.side_effect = [parent, child]
    grandparent.include()
    parent.exclude()
    child.include()
    diagram = grandparent.export()
    expected_diagram = '''@startuml

foo.cpp -> baz.cpp: void baz()

@enduml'''

    assert diagram == expected_diagram


def test__callable__export_definition_loaded_over_declaration__export_correct_diagram(two_translation_units):
    compilation_databases = CompilationDatabases()
    index = Index(compilation_databases)
    compilation_databases.add_compilation_database(two_translation_units)
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
