from INCode.models import Callable, File, Index


def test__file__get_callables_for_empty_file__returns_empty_list():
    index = Index()
    file = File('empty.cpp', index, unsaved_files=[('empty.cpp', '\n')])
    assert list(file.get_callables()) == []


def test__file__get_callables_for_file_with_one_function__returns_that_function():
    index = Index()
    file = File('one_function.cpp', index, unsaved_files=[('one_function.cpp', 'void a() {}\n')])
    # TODO(KNR): how to ignore the second parameter when comparing Callables?
    callables = list(file.get_callables())
    assert len(callables) == 1
    assert callables[0].get_name() == 'void a()'


def test__file__get_callables_for_file_with_two_functions__returns_both_functions():
    index = Index()
    file = File('two_functions.cpp', index,
                unsaved_files=[('two_functions.cpp', 'void a() {}\nvoid b(const int i) {}\n')])
    # TODO(KNR): how to ignore the second parameter when comparing Callables?
    callables = list(file.get_callables())
    assert len(callables) == 2
    # TODO(KNR): how to pack comparison into a loop based on given expected names?
    assert callables[0].get_name() == 'void a()'
    assert callables[1].get_name() == 'void b(const int)'


def test__file__get_referenced_callables_for_empty_function__returns_empty_list():
    index = Index()
    file = File('non_referencing_function.cpp', index,
                unsaved_files=[('non_referencing_function.cpp', 'void a() {}\n')])
    callable = next(file.get_callables())
    assert list(callable.get_referenced_callables()) == []


def test__file__get_referenced_callables_for_function_calling_another_one__returns_that_function():
    index = Index()
    file = File('referencing_function.cpp', index,
                unsaved_files=[('referencing_function.cpp', 'void a() {}\nvoid b() {\na();\n}\n')])
    callables = list(file.get_callables())
    callable = callables[1]
    referenced_callables = list(callable.get_referenced_callables())
    assert len(referenced_callables) == 1
    assert referenced_callables[0].get_name() == 'void a()'


def test__file__get_referenced_callables_for_function_calling_two_others__returns_both_function():
    index = Index()
    file = File('referencing_function.cpp', index,
                unsaved_files=[('referencing_function.cpp', 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')])
    callables = list(file.get_callables())
    callable = callables[2]
    referenced_callables = list(callable.get_referenced_callables())
    assert len(referenced_callables) == 2
    assert referenced_callables[0].get_name() == 'void a()'
    assert referenced_callables[1].get_name() == 'void b()'


def test__file__get_referenced_callables_for_referenced_function_in_another_file__returns_that_function():
    index = Index()
    # TODO(KNR): don't know how to use unsaved_files for multiple files...
    # file = File(
    #     'cross_tu_referencing_function.cpp', index,
    #     args=['-I./'],
    #     unsaved_files=[('cross_tu_referencing_function.cpp', '#include "dependency.h"\nvoid b() {\na();\n}\n'), (
    #         'dependency.h', '#pragma once\nvoid a();\n'), ('dependency.cpp', '#include "dependency.h"\nvoid a() {}\n')
    #                    ])
    # TODO(KNR): generate bloody source files in a temporary directory
    file = File('trials/cross_tu_referencing_function.cpp', index, args=['-I./trials'])
    callables = list(file.get_callables())
    # callable = callables[0]
    callable = callables[1]
    referenced_callables = list(callable.get_referenced_callables())
    assert len(referenced_callables) == 1
    assert referenced_callables[0].get_name() == 'void a()'


def test__file__identify_definition_for_referenced_function_in_same_file__returns_that_definition():
    index = Index()
    file = File(
        'identify_local_function.cpp', index,
        unsaved_files=[('identify_local_function.cpp', 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')])
    callables = list(file.get_callables())
    callable = callables[2]
    referenced_callables = list(callable.get_referenced_callables())
    assert len(referenced_callables) == 2
    assert referenced_callables[0].get_usr() == 'c:@F@a#'
    assert referenced_callables[1].get_usr() == 'c:@F@b#'


def test__file__identify_definition_for_referenced_function_in_another_file__returns_that_definition():
    index = Index()
    file = File('trials/cross_tu_referencing_function.cpp', index, args=['-I./trials'])
    callables = list(file.get_callables())
    callable = callables[1]
    referenced_callables = list(callable.get_referenced_callables())
    assert referenced_callables[0].get_usr() == 'c:@F@a#'


def test__file__get_callables_for_local_functions__registers_callables_in_index():
    index = Index()
    file = File(
        'identify_local_function.cpp', index,
        unsaved_files=[('identify_local_function.cpp', 'void a() {}\nvoid b() {}\nvoid c() {\na();\nb();\n}\n')])
    list(file.get_callables())
    index.lookup('c:@F@a#').location.file.name == 'identify_local_function.cpp'
    index.lookup('c:@F@b#').location.file.name == 'identify_local_function.cpp'
    index.lookup('c:@F@c#').location.file.name == 'identify_local_function.cpp'


def test__file__get_callables_for_function_in_another_file__registers_callables_in_index():
    index = Index()
    dependency_file = File('trials/dependency.cpp', index, args=['-I./trials'])
    list(dependency_file.get_callables())
    file = File('trials/cross_tu_referencing_function.cpp', index, args=['-I./trials'])
    list(file.get_callables())
    index.lookup('c:@F@a#').location.file.name == './trials/dependency.cpp'
    index.lookup('c:@F@b#').location.file.name == 'trials/cross_tu_referencing_function.cpp'
