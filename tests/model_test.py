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
