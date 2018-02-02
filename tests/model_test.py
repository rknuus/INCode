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
