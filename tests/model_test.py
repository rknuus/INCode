from INCode.models import Callable, File


def test__file__get_callables_for_empty_file__returns_empty_list():
    file = File('empty.cpp', unsaved_files=[('empty.cpp', '\n')])
    assert list(file.get_callables()) == []


def test__file__get_callables_for_file_with_one_function__returns_that_function():
    file = File('one_function.cpp', unsaved_files=[('one_function.cpp', 'void a() {}\n')])
    # TODO(KNR): how to ignore the second parameter when comparing Callables?
    callables = list(file.get_callables())
    assert len(callables) == 1
    assert callables[0].get_name() == 'void a()'


def test__file__get_callables_for_file_with_two_functions__returns_both_functions():
    file = File('two_functions.cpp', unsaved_files=[('two_functions.cpp', 'void a() {}\nvoid b(const int i) {}\n')])
    # TODO(KNR): how to ignore the second parameter when comparing Callables?
    callables = list(file.get_callables())
    assert len(callables) == 2
    # TODO(KNR): how to pack comparison into a loop based on given expected names?
    assert callables[0].get_name() == 'void a()'
    assert callables[1].get_name() == 'void b(const int)'


def test__file__get_referenced_callables_for_empty_function__returns_empty_list():
    file = File('non_referencing_function.cpp', unsaved_files=[('non_referencing_function.cpp', 'void a() {}\n')])
    callable = next(file.get_callables())
    assert list(callable.get_referenced_callables()) == []


def test__file__get_referenced_callables_for_function_calling_another_one__returns_that_function():
    file = File('referencing_function.cpp',
                unsaved_files=[('referencing_function.cpp', 'void a() {}\nvoid b() {\na();\n}\n')])
    callables = list(file.get_callables())
    callable = callables[1]
    referenced_callables = list(callable.get_referenced_callables())
    assert len(referenced_callables) == 1
    assert referenced_callables[0].get_name() == 'void a()'


def test__file__get_referenced_callables_for_function_calling_two_others__returns_both_function():
    file = File('referencing_function.cpp',
                unsaved_files=[('referencing_function.cpp', 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')])
    callables = list(file.get_callables())
    callable = callables[2]
    referenced_callables = list(callable.get_referenced_callables())
    assert len(referenced_callables) == 2
    assert referenced_callables[0].get_name() == 'void a()'
    assert referenced_callables[1].get_name() == 'void b()'


def test__file__get_referenced_callables_for_referenced_function_in_another_file__returns_that_function():
    # TODO(KNR): don't know how to use unsaved_files for multiple files...
    # file = File(
    #     'cross_tu_referencing_function.cpp',
    #     args=['-I./'],
    #     unsaved_files=[('cross_tu_referencing_function.cpp', '#include "dependency.h"\nvoid b() {\na();\n}\n'), (
    #         'dependency.h', '#pragma once\nvoid a();\n'), ('dependency.cpp', '#include "dependency.h"\nvoid a() {}\n')
    #                    ])
    file = File('trials/cross_tu_referencing_function.cpp', args=['-I./trials'])
    callables = list(file.get_callables())
    # callable = callables[0]
    callable = callables[1]
    referenced_callables = list(callable.get_referenced_callables())
    assert len(referenced_callables) == 1
    assert referenced_callables[0].get_name() == 'void a()'


def test__file__identify_definition_for_referenced_function_in_same_file__returns_that_definition():
    file = File(
        'identify_local_function.cpp',
        unsaved_files=[('identify_local_function.cpp', 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')])
    callables = list(file.get_callables())
    callable = callables[2]
    referenced_callables = list(callable.get_referenced_callables())
    assert len(referenced_callables) == 2
    assert referenced_callables[0].get_usr() == 'c:@F@a#'
    assert referenced_callables[1].get_usr() == 'c:@F@b#'


def test__file__identify_definition_for_referenced_function_in_another_file__returns_that_definition():
    file = File('trials/cross_tu_referencing_function.cpp', args=['-I./trials'])
    callables = list(file.get_callables())
    callable = callables[1]
    referenced_callables = list(callable.get_referenced_callables())
    assert referenced_callables[0].get_usr() == 'c:@F@a#'
