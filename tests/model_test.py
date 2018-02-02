from INCode.models import File


def test__file__get_callables_for_empty_file__returns_empty_list():
    file = File('empty.cpp', unsaved_files=[('empty.cpp', '\n')])
    assert file.get_callables() == []
