from INCode.models import Callable, File, Index
from unittest.mock import MagicMock
import os
import pytest
import tempfile


@pytest.fixture(scope='module')
def two_translation_units():
    with tempfile.TemporaryDirectory('two_translation_units') as directory:
        with open(os.path.join(directory, 'dependency.h'), 'w') as file:
            file.write('#pragma once\nvoid a();\n')
        with open(os.path.join(directory, 'dependency.cpp'), 'w') as file:
            file.write('#include "dependency.h"\nvoid a() {}\n')
        with open(os.path.join(directory, 'cross_tu_referencing_function.cpp'), 'w') as file:
            file.write('#include "dependency.h"\nvoid b() {\n    a();\n}\n')
        yield directory


def test__index__get_callables_for_empty_file__returns_empty_list():
    index = Index()
    file = index.load('empty.cpp', unsaved_files=[('empty.cpp', '\n')])
    assert list(file.get_callables()) == []


def test__index__get_callables_for_file_with_one_function__returns_that_function():
    index = Index()
    file = index.load('one_function.cpp', unsaved_files=[('one_function.cpp', 'void a() {}\n')])
    # TODO(KNR): how to ignore the second parameter when comparing Callables?
    callables = file.get_callables()
    assert len(callables) == 1
    assert callables[0].get_name() == 'void a()'


def test__index__get_callables_for_file_with_two_functions__returns_both_functions():
    index = Index()
    file = index.load('two_functions.cpp',
                      unsaved_files=[('two_functions.cpp', 'void a() {}\nvoid b(const int i) {}\n')])
    # TODO(KNR): how to ignore the second parameter when comparing Callables?
    callables = file.get_callables()
    assert len(callables) == 2
    # TODO(KNR): how to pack comparison into a loop based on given expected names?
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
    # callable = callables[0]
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
    assert index.lookup('c:@F@a#').location.file.name == 'identify_local_function.cpp'
    assert index.lookup('c:@F@b#').location.file.name == 'identify_local_function.cpp'
    assert index.lookup('c:@F@c#').location.file.name == 'identify_local_function.cpp'


def test__index__get_callables_for_function_in_unparsed_tu__registers_callable_in_header(two_translation_units):
    index = Index()
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    dep_header = os.path.join(two_translation_units, 'dependency.h')
    index.load(cross_tu, args=['-I{}'.format(two_translation_units)])
    assert index.lookup('c:@F@a#').location.file.name == dep_header
    assert index.lookup('c:@F@b#').location.file.name == cross_tu


def test__index__get_callables_for_function_in_another_file__registration_not_overwritten(two_translation_units):
    index = Index()
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    dep_tu = os.path.join(two_translation_units, 'dependency.cpp')
    index.load(dep_tu, args=['-I{}'.format(two_translation_units)])
    assert index.lookup('c:@F@a#').location.file.name == dep_tu
    index.load(cross_tu, args=['-I{}'.format(two_translation_units)])
    assert index.lookup('c:@F@a#').location.file.name == dep_tu
    assert index.lookup('c:@F@b#').location.file.name == cross_tu


def test__index__get_callables_for_internal_function_in_unparsed_file__function_is_unknown():
    index = Index()
    with tempfile.TemporaryDirectory('two_translation_units') as directory:
        with open(os.path.join(directory, 'dependency.h'), 'w') as file:
            file.write('#pragma once\nvoid a();\n')
        with open(os.path.join(directory, 'dependency.cpp'), 'w') as file:
            file.write('#include "dependency.h"\nvoid c() {}\nvoid a() {\nc();\n}\n')
        with open(os.path.join(directory, 'cross_tu_referencing_function.cpp'), 'w') as file:
            file.write('#include "dependency.h"\nvoid b() {\n    a();\n}\n')

        cross_tu = os.path.join(directory, 'cross_tu_referencing_function.cpp')
        index.load(cross_tu, args=['-I{}'.format(directory)])
        with pytest.raises(KeyError):
            index.lookup('c:@F@c#')


def test__index__get_callables_for_cross_referencing_function_in_file_parsed_later__get_function():
    index = Index()
    with tempfile.TemporaryDirectory('two_translation_units') as directory:
        with open(os.path.join(directory, 'dependency.h'), 'w') as file:
            file.write('#pragma once\nvoid a();\n')
        with open(os.path.join(directory, 'dependency.cpp'), 'w') as file:
            file.write('#include "dependency.h"\nvoid c() {}\nvoid a() {\nc();\n}\n')
        with open(os.path.join(directory, 'cross_tu_referencing_function.cpp'), 'w') as file:
            file.write('#include "dependency.h"\nvoid b() {\n    a();\n}\n')

        cross_tu = os.path.join(directory, 'cross_tu_referencing_function.cpp')
        dep_tu = os.path.join(directory, 'dependency.cpp')
        index.load(cross_tu, args=['-I{}'.format(directory)])
        with pytest.raises(KeyError):
            index.lookup('c:@F@c#')
        index.load(dep_tu, args=['-I{}'.format(directory)])
        assert index.lookup('c:@F@c#').location.file.name == dep_tu


def test__index__is_known_for_unknown_function__returns_false():
    index = Index()
    assert not index.is_known('foo')


def test__index__is_known_for_known_function__returns_true():
    cursor_mock = MagicMock()
    cursor_mock.get_usr.return_value = 'foo'
    index = Index()
    index.register(cursor_mock)
    assert index.is_known('foo')
