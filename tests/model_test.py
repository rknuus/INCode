# Copyright (C) 2018 R. Knuus

from clang.cindex import CursorKind
from INCode.models import Callable, CompilationDatabases, File, Index
from unittest.mock import MagicMock
from test_environment_generation import *
import os.path


def get_callable_names(callables):
    return [callable.get_name() for callable in callables]


def test__compilation_database__add_compilation_database__can_get_list_of_translation_units(directory):
    generate_project(directory, {'foo.cpp': '\n', 'bar.cpp': '\n'})
    db = CompilationDatabases()
    db.add_compilation_database(directory)
    files = db.get_files()
    assert 'foo.cpp' in files
    assert 'bar.cpp' in files


def test__file__get_callables_for_empty_file__returns_empty_list(directory):
    _, file = build_index_with_file(directory, 'empty.cpp', '\n')
    assert list(file.get_callables()) == []


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


def map_callables(callables):
    return [callable.get_name() for callable in callables]


def map_referenced_callables(callables):
    return {callable.get_name(): map_callables(callable.get_referenced_callables()) for callable in callables}


def test__callable__get_referenced_callables_for_empty_function__returns_empty_list(directory):
    _, file = build_index_with_file(directory, 'non_referencing_function.cpp', 'void a() {}\n')
    actual = map_referenced_callables(file.get_callables())
    expected = {'void a()': []}
    assert actual == expected


def test__callable__get_referenced_callables_for_function_calling_another_one__returns_that_function(directory):
    _, file = build_index_with_file(directory, 'referencing_function.cpp', 'void a() {}\nvoid b() {\na();\n}\n')
    actual = map_referenced_callables(file.get_callables())
    expected = {'void a()': [], 'void b()': ['void a()']}
    assert actual == expected


def test__callable__get_referenced_callables_for_function_calling_two_others__returns_both_function(directory):
    _, file = build_index_with_file(directory, 'double_referencing_function.cpp',
                                    'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')
    actual = map_referenced_callables(file.get_callables())
    expected = {'void a()': [], 'void b()': [], 'void c()': ['void a()', 'void b()']}
    assert actual == expected


def test__callable__get_referenced_callables_for_function_calling_one_overloaded_function__returns_that_function(
    directory):
    _, file = build_index_with_file(directory, 'referencing_one_overloaded_function.cpp',
                                    'void a() {}\nvoid a(int i) {}\nvoid b() {\na();\n}\n')
    actual = map_referenced_callables(file.get_callables())
    expected = {'void a()': [], 'void a(int)': [], 'void b()': ['void a()']}
    assert actual == expected


def test__callable__get_referenced_callables_for_function_calling_all_overloaded_functions__returns_all_functions(
    directory):
    _, file = build_index_with_file(directory, 'referencing_all_overloaded_function.cpp',
                                    'void a() {}\nvoid a(int i) {}\nvoid b() {\na();\na(1);\n}\n')
    actual = map_referenced_callables(file.get_callables())
    expected = {'void a()': [], 'void a(int)': [], 'void b()': ['void a()', 'void a(int)']}
    assert actual == expected


def test__callable__get_referenced_callables_for_overloaded_function_calling_other_one__returns_that_functions(
    directory):
    _, file = build_index_with_file(directory, 'overloaded_referencing_other_function.cpp',
                                    'void a() {}\nvoid a(int i) {\na();\n}\n')
    actual = map_referenced_callables(file.get_callables())
    expected = {'void a()': [], 'void a(int)': ['void a()']}
    assert actual == expected


def test__callable__get_referenced_callables_for_method_calling_method__returns_method(directory):
    _, file = build_index_with_file(directory, 'method_referencing_method.cpp',
                                    'class C {\npublic:\nvoid a(); void b() { a(); }\n};\n')
    actual = map_referenced_callables(file.get_callables())
    expected = {'void a()': [], 'void b()': ['void a()']}
    assert actual == expected


def test__callable__get_referenced_callables_for_overloaded_method_calling_method__returns_method(directory):
    _, file = build_index_with_file(directory, 'overloaded_method_referencing_method.cpp',
                                    'class C {\npublic:\nvoid a() {}\nvoid a(int i) { b(); }\nvoid b() {}\n};\n')
    actual = map_referenced_callables(file.get_callables())
    expected = {'void a()': [], 'void a(int)': ['void b()'], 'void b()': []}
    assert actual == expected


def test__index__ensure_registered_callable_with_references_not_overwritten(directory):
    _, file = build_index_with_file(directory, 'bug.cpp', '''
class B {
public:
    void m() {
        p();
    }
    void m(int i) {
        m();
    }
    void p() {}
};
''')
    actual = map_referenced_callables(file.get_callables())
    assert actual['void m()'] == ['void p()']
    assert actual['void m(int)'] == ['void m()']
    assert actual['void p()'] == []
    expected = {'void m()': ['void p()'], 'void m(int)': ['void m()'], 'void p()': []}
    assert actual == expected


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


def test__callable__for_member_method__sender_is_class(directory):
    _, file = build_index_with_file(directory, 'identify_local_function.cpp', '''
class B {
public:
    void m() {
        p();
    }

private:
    void p() {}
};
''')
    callables = file.get_callables()
    for callable in callables:
        assert callable.sender_ == 'B'
