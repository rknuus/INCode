import mock
import pytest
from INCode.controllers import EntryController


def test__on_select_entry_file__invalid_file__aborts():
    entry_controller = EntryController()
    with pytest.raises(ValueError):  # TODO(KNR): use app specific exception
        entry_controller.on_select_entry_file('file-that doesn_t-exist')


@mock.patch('INCode.controllers.EntryView', autospec=True)  # TODO(KNR): somehow this is the wrong mock
def test__on_select_entry_file__func_refs_two_other_funcs__loads_callables(mock_view):
    entry_controller = EntryController()
    entry_controller.view_ = mock_view  # TODO(KNR): how to avoid?
    entry_controller.on_select_entry_file(
        'func_refs_two_other_funcs.cpp',
        unsaved_files=[('func_refs_two_other_funcs.cpp', 'void a() {}\nvoid b(const int i) {}\n')])
    mock_view.load_callables.assert_called_with(['void a()', 'void b(const int)'])

# Test list:
# ==========
# - function pointer as argument
