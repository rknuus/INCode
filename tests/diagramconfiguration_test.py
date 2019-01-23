from INCode.models import CompilationDatabases, Index, Callable
from INCode.diagramconfiguration import DiagramConfiguration, CallableTreeItem
from test_environment_generation import *
from clang.cindex import CursorKind
from unittest.mock import MagicMock, patch
import os.path


def build_callable_tree_item(index = MagicMock()):
    return CallableTreeItem(Callable(MagicMock(), MagicMock()))


def test__callable_tree_item__check_whether_included__default_is_excluded():
    callable_tree_item = build_callable_tree_item()
    assert not callable_tree_item.is_included()


def test__callable_tree_item__include_and_check_whether_included__return_included():
    callable_tree_item = build_callable_tree_item()
    callable_tree_item.include()
    assert callable_tree_item.is_included()


def test__callable_tree_item__include_then_exclude_and_check_whether_included__return_included():
    callable_tree_item = build_callable_tree_item()
    callable_tree_item.include()
    callable_tree_item.exclude()
    assert not callable_tree_item.is_included()


def build_cursor(file, return_value, signature, kind):
    cursor = MagicMock()
    cursor.translation_unit.spelling = file
    cursor.result_type.spelling = return_value
    cursor.displayname = signature
    cursor.kind = kind
    return cursor


def test__callable_tree_item__export_included_parent_calling_included_child__export_correct_diagram():
    index = MagicMock()
    parent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    parent = CallableTreeItem(parent_callable)
    child_callable = Callable(build_cursor('bar.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL), index)
    child = CallableTreeItem(child_callable, parent)
    index.lookup.return_value = child_callable
    parent.include()
    child.include()
    diagram = parent.export()
    expected_diagram = '''@startuml

foo.cpp -> bar.cpp: void baz()

@enduml'''

    assert diagram == expected_diagram


def test__callable_tree_item__export_included_parent_calling_excluded_child__export_correct_diagram():
    index = MagicMock()
    parent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    parent = CallableTreeItem(parent_callable)
    child_callable = Callable(build_cursor('bar.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL), index)
    child = CallableTreeItem(child_callable, parent)
    index.lookup.return_value = child_callable
    parent.include()
    child.exclude()
    diagram = parent.export()
    expected_diagram = '''@startuml


@enduml'''

    assert diagram == expected_diagram


def test__callable_tree_item__export_excluded_parent_calling_included_child__export_correct_diagram():
    index = MagicMock()
    parent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    parent = CallableTreeItem(parent_callable)
    child_callable = Callable(build_cursor('bar.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL), index)
    child = CallableTreeItem(child_callable, parent)
    index.lookup.return_value = child_callable
    parent.exclude()
    child.include()
    diagram = parent.export()
    expected_diagram = '''@startuml

 -> bar.cpp: void baz()

@enduml'''

    assert diagram == expected_diagram


def test__callable_tree_item__export_two_included_child_levels__export_correct_diagram():
    index = MagicMock()
    grandparent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    grandparent = CallableTreeItem(grandparent_callable)
    parent_callable = Callable(build_cursor('bar.cpp', 'void', 'bar()', CursorKind.FUNCTION_DECL), index)
    parent = CallableTreeItem(parent_callable, grandparent)
    child_callable = Callable(build_cursor('baz.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL), index)
    child = CallableTreeItem(child_callable, parent)
    index.lookup.side_effect = [grandparent_callable ,parent_callable, child_callable]
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


def test__callable_tree_item__export_grandparent_and_child_but_not_parent__export_correct_diagram():
    index = MagicMock()
    grandparent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    grandparent = CallableTreeItem(grandparent_callable)
    parent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL), index)
    parent = CallableTreeItem(parent_callable, grandparent)
    child_callable = Callable(build_cursor('baz.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL), index)
    child = CallableTreeItem(child_callable, parent)
    index.lookup.side_effect = [grandparent_callable, parent_callable, child_callable]
    grandparent.include()
    parent.exclude()
    child.include()
    diagram = grandparent.export()
    expected_diagram = '''@startuml

foo.cpp -> baz.cpp: void baz()

@enduml'''

    assert diagram == expected_diagram


def test__callable_tree_item__export_definition_loaded_over_declaration__export_correct_diagram(two_translation_units):
    compilation_databases = CompilationDatabases()
    index = Index(compilation_databases)
    compilation_databases.add_compilation_database(two_translation_units)
    cross_tu = os.path.join(two_translation_units, 'cross_tu_referencing_function.cpp')
    dep_tu = os.path.join(two_translation_units, 'dependency.cpp')
    index.load(dep_tu)
    index.load(cross_tu)
    parent_callable = index.lookup('c:@F@b#')
    child_callable = index.lookup('c:@F@a#')

    parent = CallableTreeItem(parent_callable)
    child = CallableTreeItem(child_callable, parent)
    parent.include()
    child.include()

    diagram = parent.export()
    expected_diagram = '''@startuml

{} -> {}: void a()

@enduml'''.format(cross_tu, dep_tu)

    assert diagram == expected_diagram



def test__callable__export_of_overloaded_member_method__sender_is_class(directory):
    index, file = build_index_with_file(directory, 'identify_local_function.cpp', '''
class B {
public:
    void m() {
        p();
    }
    void m(int i) {
        m();
    }

private:
    void p() {}
};
''')
    callables = file.get_callables()
    for callable in callables:
        if 'p' not in callable.get_name():
            referenced_callables = callable.get_referenced_callables()
            assert len(referenced_callables) > 0

    export_callable = callables[0]
    export_callable_tree_item = CallableTreeItem(export_callable)
    export_callable_tree_item.include()

    for callable in export_callable.get_referenced_callables():
        callable_tree_item = CallableTreeItem(callable, export_callable_tree_item)
        callable_tree_item.include()

    diagram = export_callable_tree_item.export()
    expected_diagram = '''@startuml

B -> B: void p()

@enduml'''

    assert diagram == expected_diagram

def setup_diagram_configuration(directory):
    index, file = build_index_with_file(directory, 'identify_local_function.cpp', '''
class B {
public:
    void a() {
        b();
    }

    void b() {
        c();
        d();
    }

    void c() {}
    void d() {}
};
''')
    export_callable = file.get_callables()[0]
    entry_point = MagicMock()
    entry_point.get_callable.return_value = export_callable

    return DiagramConfiguration(entry_point)

def test__reveal_children__has_children_after_reveal(directory):
    diagram_configuration = setup_diagram_configuration(directory)

    child_tree_item = diagram_configuration.entry_point_item_.referenced_items_[0]
    diagram_configuration.tree_.setCurrentItem(child_tree_item)

    diagram_configuration.revealChildren()
    assert child_tree_item.childCount() > 0


def test__reveal_children__no_duplicates_after_multiple_reveal(directory):
    diagram_configuration = setup_diagram_configuration(directory)

    child_tree_item = diagram_configuration.entry_point_item_.referenced_items_[0]
    diagram_configuration.tree_.setCurrentItem(child_tree_item)

    diagram_configuration.revealChildren()
    count = child_tree_item.childCount()
    diagram_configuration.revealChildren()

    assert child_tree_item.childCount() == count

def test__reveal_children__check_if_reveals__current_item_is_null(directory):
    diagram_configuration = setup_diagram_configuration(directory)
    diagram_configuration.revealChildren()

    child_items = diagram_configuration.entry_point_item_.referenced_items_
    for child_item in child_items:
        assert len(child_item.referenced_items_) == 0

def test__reveal_children__check_if_reveals__current_item_has_children(directory):
    diagram_configuration = setup_diagram_configuration(directory)

    entry_point_item = diagram_configuration.entry_point_item_
    diagram_configuration.tree_.setCurrentItem(entry_point_item)

    with patch.object(entry_point_item, 'get_callable') as mock:
        diagram_configuration.revealChildren()

    mock.assert_not_called()

def test__diagram_configuration__export_calls_entry_point_export(directory):
    diagram_configuration = setup_diagram_configuration(directory)
    diagram_configuration.entry_point_item_.include()

    child_items = diagram_configuration.entry_point_item_.referenced_items_
    for child_item in child_items:
        child_item.include()

    with patch.object(diagram_configuration.entry_point_item_, 'export') as mock:
        diagram_configuration.export()

    mock.assert_called_once_with()
