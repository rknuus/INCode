from INCode.models import Callable, File, Index
from string import Template
from unittest.mock import MagicMock
import os
import pytest
import tempfile


def generate_file(directory, file, content):
    with open(os.path.join(directory, file), 'w') as file:
        file.write(content)


@pytest.fixture(scope='module')
def two_translation_units():
    with tempfile.TemporaryDirectory('two_translation_units') as directory:
        generate_file(directory, 'dependency.h', '''
                      #pragma once
                      void a();
                      ''')
        generate_file(directory, 'dependency.cpp', '''
                      #include "dependency.h"
                      void a() {}
                      ''')
        generate_file(directory, 'cross_tu_referencing_function.cpp', '''
                      #include "dependency.h"
                      void b() {
                          a();
                      }
                      ''')
        template = Template('''
                            [{ "directory": "${directory}",
                               "command": "compiler -SOME -FLAGS ${directory}/dependency.cpp",
                               "file": "${directory}/dependency.cpp"
                             },
                             { "directory": "${directory}",
                               "command": "compiler -SOME -FLAGS ${directory}/cross_tu_referencing_function.cpp",
                               "file": "${directory}/cross_tu_referencing_function.cpp"
                             }]
                            ''')
        generate_file(directory, 'compile_commands.json', template.substitute({'directory': directory}))
        yield directory


@pytest.fixture(scope='module')
def local_and_xref_dep():
    with tempfile.TemporaryDirectory('local_and_xref_dep') as directory:
        generate_file(directory, 'dependency.h', '''
                      #pragma once
                      void a();
                      ''')
        generate_file(directory, 'dependency.cpp', '''
                      #include "dependency.h"
                      void c() {}
                      void a() {
                          c();
                      }
                      ''')
        generate_file(directory, 'cross_tu_referencing_function.cpp', '''
                      #include "dependency.h"
                      void b() {
                          a();
                      }
                      ''')
        template = Template('''
                            [{ "directory": "${directory}",
                               "command": "compiler -SOME -FLAGS ${directory}/dependency.cpp",
                               "file": "${directory}/dependency.cpp"
                             },
                             { "directory": "${directory}",
                               "command": "compiler -SOME -FLAGS ${directory}/cross_tu_referencing_function.cpp",
                               "file": "${directory}/cross_tu_referencing_function.cpp"
                             }]
                            ''')
        generate_file(directory, 'compile_commands.json', template.substitute({'directory': directory}))
        yield directory


def test__index__get_callables_for_empty_file__returns_empty_list():
    index = Index()
    file = index.load('empty.cpp', unsaved_files=[('empty.cpp', '\n')])
    assert list(file.get_callables()) == []


def test__index__get_callables_for_file_with_one_function__returns_that_function():
    index = Index()
    file = index.load('one_function.cpp', unsaved_files=[('one_function.cpp', 'void a() {}\n')])
    callables = file.get_callables()
    assert len(callables) == 1
    assert callables[0].get_name() == 'void a()'


def test__index__get_callables_for_file_with_two_functions__returns_both_functions():
    index = Index()
    file = index.load('two_functions.cpp',
                      unsaved_files=[('two_functions.cpp', 'void a() {}\nvoid b(const int i) {}\n')])
    callables = file.get_callables()
    assert len(callables) == 2
    assert callables[0].get_name() == 'void a()'
    assert callables[1].get_name() == 'void b(const int)'


def test__index__get_referenced_callables_for_empty_function__returns_empty_list():
    index = Index()
    file = index.load('non_referencing_function.cpp',
                      unsaved_files=[('non_referencing_function.cpp', 'void a() {}\n')])
    callable = file.get_callables()[0]
    assert callable.get_referenced_callables() == []


def test__index__get_referenced_callables_for_function_calling_another_one__returns_that_function():
    index = Index()
    file = index.load('referencing_function.cpp',
                      unsaved_files=[('referencing_function.cpp', 'void a() {}\nvoid b() {\na();\n}\n')])
    callables = file.get_callables()
    callable = callables[1]
    referenced_callables = callable.get_referenced_callables()
    assert len(referenced_callables) == 1
    assert referenced_callables[0].get_name() == 'void a()'


def test__index__get_referenced_callables_for_function_calling_two_others__returns_both_function():
    index = Index()
    file = index.load(
        'referencing_function.cpp',
        unsaved_files=[('referencing_function.cpp', 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')])
    callables = file.get_callables()
    callable = callables[2]
    referenced_callables = callable.get_referenced_callables()
    assert len(referenced_callables) == 2
    assert referenced_callables[0].get_name() == 'void a()'
    assert referenced_callables[1].get_name() == 'void b()'


def test__index__get_referenced_callables_of_another_file__returns_that_function(two_translation_units):
    index = Index()
    # TODO(KNR): don't know how to use unsaved_files for multiple files...
    # file = File(
    #     'cross_tu_referencing_function.cpp', index,
    #     args=['-I./'],
    #     unsaved_files=[('cross_tu_referencing_function.cpp', '#include "dependency.h"\nvoid b() {\na();\n}\n'), (
    #         'dependency.h', '#pragma once\nvoid a();\n'), ('dependency.cpp', '#include "dependency.h"\nvoid a() {}\n')
    #                    ])
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    file = index.load(cross_tu, args=['-I./trials'])
    callables = file.get_callables()
    callable = callables[1]
    referenced_callables = callable.get_referenced_callables()
    assert len(referenced_callables) == 1
    assert referenced_callables[0].get_name() == 'void a()'


def test__index__get_referenced_callables_for_referenced_function_in_same_file__returns_that_definition():
    index = Index()
    file = index.load(
        'identify_local_function.cpp',
        unsaved_files=[('identify_local_function.cpp', 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')])
    callables = file.get_callables()
    callable = callables[2]
    referenced_callables = callable.get_referenced_callables()
    assert len(referenced_callables) == 2
    assert referenced_callables[0].get_usr() == 'c:@F@a#'
    assert referenced_callables[1].get_usr() == 'c:@F@b#'


def test__index__get_callables_for_local_functions__registers_callables_in_index():
    index = Index()
    index.load(
        'identify_local_function.cpp',
        unsaved_files=[('identify_local_function.cpp', 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')])
    assert index.lookup('c:@F@a#').cursor_.location.file.name == 'identify_local_function.cpp'
    assert index.lookup('c:@F@b#').cursor_.location.file.name == 'identify_local_function.cpp'
    assert index.lookup('c:@F@c#').cursor_.location.file.name == 'identify_local_function.cpp'


def test__index__get_callables_for_function_in_unparsed_tu__registers_callable_in_header(two_translation_units):
    index = Index()
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    dep_header = os.path.join(two_translation_units, 'dependency.h')
    index.load(cross_tu, args=['-I{}'.format(two_translation_units)])
    assert index.lookup('c:@F@a#').cursor_.location.file.name == dep_header
    assert index.lookup('c:@F@b#').cursor_.location.file.name == cross_tu


def test__index__get_callables_for_function_in_another_file__registration_not_overwritten(two_translation_units):
    index = Index()
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    dep_tu = os.path.join(two_translation_units, 'dependency.cpp')
    index.load(dep_tu, args=['-I{}'.format(two_translation_units)])
    assert index.lookup('c:@F@a#').cursor_.location.file.name == dep_tu
    index.load(cross_tu, args=['-I{}'.format(two_translation_units)])
    assert index.lookup('c:@F@a#').cursor_.location.file.name == dep_tu
    assert index.lookup('c:@F@b#').cursor_.location.file.name == cross_tu


def test__index__get_callables_for_internal_function_in_unparsed_file__function_is_unknown(local_and_xref_dep):
    index = Index()
    cross_tu = os.path.join(local_and_xref_dep, 'cross_tu_referencing_function.cpp')
    index.load(cross_tu, args=['-I{}'.format(local_and_xref_dep)])
    with pytest.raises(KeyError):
        index.lookup('c:@F@c#')


def test__index__get_callables_for_cross_referencing_function_in_file_parsed_later__get_function(local_and_xref_dep):
    index = Index()
    cross_tu = os.path.join(local_and_xref_dep, 'cross_tu_referencing_function.cpp')
    dep_tu = os.path.join(local_and_xref_dep, 'dependency.cpp')
    index.load(cross_tu, args=['-I{}'.format(local_and_xref_dep)])
    with pytest.raises(KeyError):
        index.lookup('c:@F@c#')
    index.load(dep_tu, args=['-I{}'.format(local_and_xref_dep)])
    assert index.lookup('c:@F@c#').cursor_.location.file.name == dep_tu


def test__index__is_known_for_unknown_function__returns_false():
    index = Index()
    assert not index.is_known('foo')


def test__index__is_known_for_known_function__returns_true():
    cursor_mock = MagicMock()
    cursor_mock.get_usr.return_value = 'foo'
    index = Index()
    index.register(cursor_mock)
    assert index.is_known('foo')


def test__index__load_definition_for_function_defined_in_other_file__returns_definition(two_translation_units):
    index = Index()
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    index.add_compilation_database(os.path.join(two_translation_units, 'compile_commands.json'))
    index.load(cross_tu, args=['-I{}'.format(two_translation_units)])
    declaration = index.lookup('c:@F@a#')
    definition = index.load_definition(declaration)
    assert not declaration.is_definition()
    assert definition.is_definition()


def test__index__add_compilation_database__can_get_list_of_translation_units():
    with tempfile.TemporaryDirectory('compilation_database') as directory:
        database = os.path.join(directory, 'compile_commands.json')
        with open(database, 'w') as file:
            file.write(
                '[{\n"directory": "/foo",\n"command": "compiler -SOME -FLAGS /foo/bar.cpp",\n"file": "/foo/bar.cpp"},\n'
                '{\n"directory": "/foo/bar",\n"command": "compiler -SOME -FLAGS /foo/bar/baz.cpp",\n"file": "/foo/bar/baz.cpp"}]')
        index = Index()
        index.add_compilation_database(database)
        files = index.get_files()
        assert '/foo/bar.cpp' in files
        assert '/foo/bar/baz.cpp' in files


def test__scenario__select_entry_location_and_follow_references__data_model_is_correct(local_and_xref_dep):
    index = Index()
    database = os.path.join(local_and_xref_dep, 'compile_commands.json')
    index.add_compilation_database(database)
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
