from PyQt5.QtWidgets import QDialog, QFileDialog, QApplication, QMessageBox
from INCode.entrydialog import EntryDialog
from INCode.models import Callable, CompilationDatabases, Index
from INCode.diagramconfiguration import DiagramConfiguration, CallableTreeItem
from tests.test_environment_generation import build_index_with_file, directory, \
    generate_project, local_and_xref_dep, two_translation_units, two_files_with_classes, build_index
from clang.cindex import CursorKind
from unittest.mock import MagicMock, PropertyMock, patch
import os.path

def build_callable_tree_item():
    cursor = MagicMock()
    cursor.kind = CursorKind.FUNCTION_DECL
    return CallableTreeItem(Callable(cursor))


def test__callable_tree_item__check_whether_included__default_is_excluded():
    build_index()
    callable_tree_item = build_callable_tree_item()
    assert not callable_tree_item.is_included()


def test__callable_tree_item__include_and_check_whether_included__return_included():
    build_index()
    callable_tree_item = build_callable_tree_item()
    callable_tree_item.include()
    assert callable_tree_item.is_included()


def test__callable_tree_item__include_then_exclude_and_check_whether_included__return_included():
    build_index()
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
    index = build_index()
    parent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL))
    index.register(parent_callable)
    parent = CallableTreeItem(parent_callable)
    child_callable = Callable(build_cursor('bar.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL))
    index.register(child_callable)
    child = CallableTreeItem(child_callable, parent)
    parent.include()
    child.include()
    diagram = parent.export()
    expected_diagram = '''@startuml

"foo.cpp" -> "bar.cpp": void baz()

@enduml'''

    assert diagram == expected_diagram


def test__callable_tree_item__export_included_parent_calling_excluded_child__export_correct_diagram():
    index = build_index()
    parent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL))
    index.register(parent_callable)
    parent = CallableTreeItem(parent_callable)
    child_callable = Callable(build_cursor('bar.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL))
    index.register(child_callable)
    child = CallableTreeItem(child_callable, parent)
    parent.include()
    child.exclude()
    diagram = parent.export()
    expected_diagram = '''@startuml


@enduml'''

    assert diagram == expected_diagram


def test__callable_tree_item__export_excluded_parent_calling_included_child__export_correct_diagram():
    index = build_index()
    parent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL))
    index.register(parent_callable)
    parent = CallableTreeItem(parent_callable)
    child_callable = Callable(build_cursor('bar.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL))
    index.register(child_callable)
    child = CallableTreeItem(child_callable, parent)
    parent.exclude()
    child.include()
    diagram = parent.export()
    expected_diagram = '''@startuml

"-" -> "bar.cpp": void baz()

@enduml'''

    assert diagram == expected_diagram


def test__callable_tree_item__export_two_included_child_levels__export_correct_diagram():
    index = build_index()
    grandparent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL))
    index.register(grandparent_callable)
    grandparent = CallableTreeItem(grandparent_callable)
    parent_callable = Callable(build_cursor('bar.cpp', 'void', 'bar()', CursorKind.FUNCTION_DECL))
    index.register(parent_callable)
    parent = CallableTreeItem(parent_callable, grandparent)
    child_callable = Callable(build_cursor('baz.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL))
    index.register(child_callable)
    child = CallableTreeItem(child_callable, parent)

    grandparent.include()
    parent.include()
    child.include()
    diagram = grandparent.export()
    expected_diagram = '''@startuml

"foo.cpp" -> "bar.cpp": void bar()
"bar.cpp" -> "baz.cpp": void baz()

@enduml'''

    assert diagram == expected_diagram


# # TODO(KNR): simplify diagram tests by factoring out common code


def test__callable_tree_item__export_grandparent_and_child_but_not_parent__export_correct_diagram():
    index = build_index()
    grandparent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL))
    index.register(grandparent_callable)
    grandparent = CallableTreeItem(grandparent_callable)
    parent_callable = Callable(build_cursor('foo.cpp', 'void', 'foo()', CursorKind.FUNCTION_DECL))
    index.register(parent_callable)
    parent = CallableTreeItem(parent_callable, grandparent)
    child_callable = Callable(build_cursor('baz.cpp', 'void', 'baz()', CursorKind.FUNCTION_DECL))
    index.register(child_callable)

    child = CallableTreeItem(child_callable, parent)
    grandparent.include()
    parent.exclude()
    child.include()
    diagram = grandparent.export()
    expected_diagram = '''@startuml

"foo.cpp" -> "baz.cpp": void baz()

@enduml'''

    assert diagram == expected_diagram


def test__callable_tree_item__export_function_definition_loaded_over_declaration__export_correct_diagram(
        two_translation_units):
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

"{}" -> "{}": void a()

@enduml'''.format(cross_tu, dep_tu)

    assert diagram == expected_diagram


def test__callable_tree_item__export_method_definition_loaded_over_declaration__export_correct_diagram(
        two_files_with_classes):
    compilation_databases = CompilationDatabases()
    index = Index(compilation_databases)
    compilation_databases.add_compilation_database(two_files_with_classes)
    a_tu = os.path.join(two_files_with_classes, 'a.cpp')
    b_tu = os.path.join(two_files_with_classes, 'b.cpp')
    index.load(a_tu)
    index.load(b_tu)
    parent_callable = index.lookup('c:@S@A@F@a#')
    child_callable = index.lookup('c:@S@B@F@b#')

    parent = CallableTreeItem(parent_callable)
    child = CallableTreeItem(child_callable, parent)
    parent.include()
    child.include()

    diagram = parent.export()
    expected_diagram = '''@startuml

"A" -> "B": void b()

@enduml'''

    assert diagram == expected_diagram


def test__callable__export_of_recursive_method__export_correct_diagram(directory):
    file = build_index_with_file(directory, 'identify_local_function.cpp', '''
class B {
public:
    void m() {
        p();
    }
    void m(int i) {
        m();
    }

private:
    void p() {
        p();
    }
};
''')
    callables = file.callables
    for callable in callables:
        if 'p' not in callable.name:
            assert len(callable.referenced_callables) > 0

    export_callable = callables[2]
    assert export_callable.name == "void B::p()"
    export_callable_tree_item = CallableTreeItem(export_callable)
    export_callable_tree_item.include()

    for callable in export_callable.referenced_callables:
        callable_tree_item = CallableTreeItem(callable, export_callable_tree_item)
        callable_tree_item.include()
        for child_callable in callable.referenced_callables:
            child_callable_tree_item = CallableTreeItem(child_callable, callable_tree_item)
            child_callable_tree_item.include()

    diagram = export_callable_tree_item.export()
    expected_diagram = '''@startuml

"B" -> "B": void p()
"B" -> "B": void p()

@enduml'''

    assert diagram == expected_diagram


def test__callable__export_of_function_call_in_parameter__sort_correct(directory):
    file = build_index_with_file(directory, 'identify_local_function.cpp', '''
class B {
public:
    void d(int val) {
        p();
    }
    
    int m() {
        return 34;
    }

private:
    void p() {
        d(m());
    }
};
''')
    callables = file.callables
    export_callable = callables[2]
    export_callable_tree_item = CallableTreeItem(export_callable)
    export_callable_tree_item.include()

    for callable in export_callable.referenced_callables:
        print(vars(callable))
        callable_tree_item = CallableTreeItem(callable, export_callable_tree_item)
        callable_tree_item.include()

    diagram = export_callable_tree_item.export()
    expected_diagram = '''@startuml

"B" -> "B": int m()
"B" -> "B": void d(int)

@enduml'''

    assert diagram == expected_diagram


def test__callable__export_of_member_method_and_function__export_correct_diagram(directory):
    file_name = 'identify_local_function.cpp'
    file = build_index_with_file(directory, file_name, '''
void func();
    
class B {
public:
    void m() {
        p();
        func();
    }
    void m(int i) {
        m();
    }

private:
    void p() {}
};

void func() {
    B b;
    b.m();
}
''')

    callables = file.callables

    export_callable = callables[0]
    assert export_callable.name == "void func()"
    export_callable_tree_item = CallableTreeItem(export_callable)
    export_callable_tree_item.include()

    for callable in export_callable.referenced_callables:
        callable_tree_item = CallableTreeItem(callable, export_callable_tree_item)
        callable_tree_item.include()
        for child_callable in callable.referenced_callables:
            child_callable_tree_item = CallableTreeItem(child_callable, callable_tree_item)
            child_callable_tree_item.include()

    diagram = export_callable_tree_item.export()
    expected_diagram = '''@startuml

"{0}" -> "B": void B()
"{0}" -> "B": void m()
"B" -> "B": void p()
"B" -> "{0}": void func()

@enduml'''.format(file_name)

    assert diagram == expected_diagram


def setup_diagram_configuration(directory, mocker, code='''
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
'''):
    file = build_index_with_file(directory, 'identify_local_function.cpp', code)
    export_callable = callable_by_name("a", file.callables)
    entry_point = MagicMock(return_value=export_callable)

    mocker.patch.object(EntryDialog, "exec", return_value=None)
    mocker.patch.object(EntryDialog, "result", return_value=QDialog.Accepted)
    mocker.patch.object(EntryDialog, "get_entry_point", entry_point)

    return DiagramConfiguration()


def callable_by_name(name, callables):
    return list(filter(lambda c: name in c.name, callables))[0]


def test__diagram_configuration__reveal_children_of_item_without_references__has_no_children_after_reveal(directory, mocker):
    diagram_configuration = setup_diagram_configuration(directory, mocker, '''
class B {
public:
    void a() {}
};
''')

    diagram_configuration.tree_.setCurrentItem(diagram_configuration.entry_point_item_)

    diagram_configuration.reveal_children()
    assert diagram_configuration.entry_point_item_.childCount() == 0


def test__diagram_configuration__reveal_children__has_children_after_reveal(directory, mocker):
    diagram_configuration = setup_diagram_configuration(directory, mocker)

    child_tree_item = diagram_configuration.entry_point_item_.referenced_items_[0]
    diagram_configuration.tree_.setCurrentItem(child_tree_item)

    diagram_configuration.reveal_children()
    assert child_tree_item.childCount() > 0


def test__diagram_configuration__reveal_children__no_duplicates_after_multiple_reveal(directory, mocker):
    diagram_configuration = setup_diagram_configuration(directory, mocker)

    child_tree_item = diagram_configuration.entry_point_item_.referenced_items_[0]
    diagram_configuration.tree_.setCurrentItem(child_tree_item)

    diagram_configuration.reveal_children()
    count = child_tree_item.childCount()
    diagram_configuration.reveal_children()

    assert child_tree_item.childCount() == count


def test__diagram_configuration__reveal_if_no_item_selected__no_action(directory, mocker):
    diagram_configuration = setup_diagram_configuration(directory, mocker)
    diagram_configuration.reveal_children()

    child_items = diagram_configuration.entry_point_item_.referenced_items_
    for child_item in child_items:
        assert len(child_item.referenced_items_) == 0


def test__diagram_configuration__reveal_children__check_if_tree_expands(directory, mocker):
    diagram_configuration = setup_diagram_configuration(directory, mocker)

    child_tree_item = diagram_configuration.entry_point_item_.referenced_items_[0]
    diagram_configuration.tree_.setCurrentItem(child_tree_item)
    diagram_configuration.reveal_children()

    for child_child_tree_item in child_tree_item.referenced_items_:
        assert child_child_tree_item.isExpanded()

def test__callable_tree_item__export_project_with_constructor__export_correct_diagram(directory):
    file_name = "function_with_constructor.cpp"
    file = build_index_with_file(directory, file_name, '''
    void bar();
    
    class A {
        A() {}
        
        void foo() {}
    }
    
    void bar() {
        A a;
        a.foo();
    }
    ''')

    callable = callable_by_name("bar", file.callables)
    callable_tree_item = CallableTreeItem(callable)
    callable_tree_item.include()

    for child_callable in callable.referenced_callables:
        child_callable_tree_item = CallableTreeItem(child_callable, callable_tree_item)
        child_callable_tree_item.include()

    diagram = callable_tree_item.export()
    expected_diagram = '''@startuml

"{0}" -> "A": void A()
"{0}" -> "A": void foo()

@enduml'''.format(file_name)

    assert diagram == expected_diagram


def test__callable_tree_item__export_project_with_destructor__export_correct_diagram(directory):
    file_name = "function_with_constructor.cpp"
    file = build_index_with_file(directory, file_name, '''
    void bar();

    class A {
        A() {}

        void foo() {}
    }

    void bar() {
        A a;
        a.~A();
    }
    ''')

    callable = callable_by_name("bar", file.callables)
    callable_tree_item = CallableTreeItem(callable)
    callable_tree_item.include()

    for child_callable in callable.referenced_callables:
        child_callable_tree_item = CallableTreeItem(child_callable, callable_tree_item)
        child_callable_tree_item.include()

    diagram = callable_tree_item.export()
    expected_diagram = '''@startuml

"{0}" -> "A": void A()
"{0}" -> "A": void ~A()

@enduml'''.format(file_name)

    assert diagram == expected_diagram


def test__callable_tree_item__export_project_with_function_pointer__export_correct_diagram(directory):
    file_name = "function_with_function_pointer.cpp"
    file = build_index_with_file(directory, file_name, '''
    void (*foo)(int);
    void bar();
    void baz();

    void bar() {
        foo(5);
    }
    
    void baz() {
        foo = &baz;
        bar();
    }
    ''')

    callable = callable_by_name("baz", file.callables)
    callable_tree_item = CallableTreeItem(callable)
    callable_tree_item.include()

    for child_callable in callable.referenced_callables:
        child_callable_tree_item = CallableTreeItem(child_callable, callable_tree_item)
        child_callable_tree_item.include()
        for child_child_callable in child_callable.referenced_callables:
            child_child_callable_tree_item = CallableTreeItem(child_child_callable, child_callable_tree_item)
            child_child_callable_tree_item.include()

    diagram = callable_tree_item.export()
    expected_diagram = '''@startuml

"{0}" -> "{0}": void bar()
"{0}" -> "{0}": void (* foo)(int)

@enduml'''.format(file_name)

    assert diagram == expected_diagram


def test__callable_tree_item__export_project_with_class_compound_operator__export_correct_diagram(directory):
    file_name = "function_with_function_pointer.cpp"
    file = build_index_with_file(directory, file_name, '''
class X {
public:
  X& operator -=(X x) {
    return *x;
  }
};

void foo() {
    X x;
    x -= x;
}
    ''')

    callable = callable_by_name("foo", file.callables)
    callable_tree_item = CallableTreeItem(callable)
    callable_tree_item.include()

    for child_callable in callable.referenced_callables:
        child_callable_tree_item = CallableTreeItem(child_callable, callable_tree_item)
        child_callable_tree_item.include()

    diagram = callable_tree_item.export()
    expected_diagram = '''@startuml

"{0}" -> "X": void X()
"{0}" -> "X": void X(const X &)
"{0}" -> "X": X & operator-=(X)

@enduml'''.format(file_name)

    assert diagram == expected_diagram


def test__callable_tree_item__export_project_with_class_operator__export_correct_diagram(directory):
    file_name = "function_with_function_pointer.cpp"
    file = build_index_with_file(directory, file_name, '''
class X {
public:
  X &operator -(X x) {
    return *x;
  }
};

void foo() {
    X x;
    x = x - x;
}
    ''')

    callable = callable_by_name("foo", file.callables)
    callable_tree_item = CallableTreeItem(callable)
    callable_tree_item.include()

    for child_callable in callable.referenced_callables:
        child_callable_tree_item = CallableTreeItem(child_callable, callable_tree_item)
        child_callable_tree_item.include()

    diagram = callable_tree_item.export()
    expected_diagram = '''@startuml

"{0}" -> "X": void X()
"{0}" -> "X": void X(const X &)
"{0}" -> "X": X & operator-(X)
"{0}" -> "X": X & operator=(const X &)

@enduml'''.format(file_name)

    assert diagram == expected_diagram


def test__callable_tree_item__export_project_with_conversion_function__export_correct_diagram(directory):
    file_name = "function_with_function_pointer.cpp"
    file = build_index_with_file(directory, file_name, '''
class X {
public:
  operator int() {
    return 0;
  }
};

void foo() {
    X x;
    int i = int(x);
}
    ''')

    callable = callable_by_name("foo", file.callables)
    callable_tree_item = CallableTreeItem(callable)
    callable_tree_item.include()

    for child_callable in callable.referenced_callables:
        child_callable_tree_item = CallableTreeItem(child_callable, callable_tree_item)
        child_callable_tree_item.include()

    diagram = callable_tree_item.export()
    expected_diagram = '''@startuml

"{0}" -> "X": void X()
"{0}" -> "X": operator int()

@enduml'''.format(file_name)

    assert diagram == expected_diagram


def test__callable_tree_item__export_project_with_std_function__export_correct_diagram(directory):
    file_name = "function_with_function_pointer.cpp"
    file = build_index_with_file(directory, file_name, '''
#include <functional>


void foo(int i) {}

void bar() {
  std::function<void()> f_display_42 = []() { foo(42); };
  f_display_42();
}
    ''')

    callable = callable_by_name("bar", file.callables)
    callable_tree_item = CallableTreeItem(callable)
    callable_tree_item.include()

    for child_callable in callable.referenced_callables:
        child_callable_tree_item = CallableTreeItem(child_callable, callable_tree_item)
        child_callable_tree_item.include()

    diagram = callable_tree_item.export()
    expected_diagram = '''@startuml

"{0}" -> "function<void ()>": void function<>((lambda at {1}/function_with_function_pointer.cpp:8:40))
"{0}" -> "function<void ()>": void operator()()

@enduml'''.format(file_name, directory)
    print(diagram)
    assert diagram == expected_diagram


def test__generate_uml__diagram_preview__generate_if_view_is_visible(directory, mocker):
    diagram_configuration = setup_diagram_configuration(directory, mocker)

    with patch.object(diagram_configuration.svg_view_, 'isVisible') as mock:
        mock.return_value = False
        diagram_configuration.entry_point_item_.include()
        for child_tree_item in diagram_configuration.entry_point_item_.referenced_items_:
            child_tree_item.include()
        diagram_configuration.update_preview()
        assert diagram_configuration.current_diagram_ is None

        mock.return_value = True
        diagram_configuration.update_preview()
        assert diagram_configuration.current_diagram_ == diagram_configuration.entry_point_item_.export()
        assert len(diagram_configuration.svg_view_.items()) == 1


def test__diagram_configuration__export_calls_entry_point_export__export_as_png(directory, mocker):
    diagram_configuration = setup_diagram_configuration(directory, mocker)
    diagram_configuration.entry_point_item_.include()

    child_items = diagram_configuration.entry_point_item_.referenced_items_
    for child_item in child_items:
        child_item.include()

    export_file_name = "exported_image"
    file_path = os.path.join(directory, export_file_name)

    mocker.patch.object(QFileDialog, 'getSaveFileName', return_value=(file_path, 'png'))

    with patch.object(diagram_configuration.entry_point_item_, 'export') as mock:
        mock.return_value = "@startuml\n\n@enduml"
        diagram_configuration.export()

    assert os.path.exists(file_path + ".png")
    mock.assert_called_once_with()


def test__diagram_configuration__export_calls_entry_point_export__export_as_uml(directory, mocker):
    diagram_configuration = setup_diagram_configuration(directory, mocker)
    diagram_configuration.entry_point_item_.include()

    child_items = diagram_configuration.entry_point_item_.referenced_items_
    for child_item in child_items:
        child_item.include()

    export_file_name = "exported_image"
    file_path = os.path.join(directory, export_file_name)

    mocker.patch.object(QFileDialog, 'getSaveFileName', return_value=(file_path, 'uml'))
    diagram = "@startuml\n\n@enduml"
    with patch.object(diagram_configuration.entry_point_item_, 'export') as mock:
        mock.return_value = diagram
        diagram_configuration.export()
    file_path += ".uml"

    mock.assert_called_once_with()
    assert os.path.exists(file_path)
    assert open(file_path, "r").read() == diagram


def test__change_entry_point__decline_message_box_warning__entry_point_item_has_changed(directory, mocker):
    diagram_configuration = setup_diagram_configuration(directory, mocker)
    mocker.patch.object(QMessageBox, "question", return_value=QMessageBox.Yes)
    new_entry_point_item = MagicMock()
    new_entry_point_item.id = "123456"
    new_entry_point_item.name = "test"
    mocker.patch.object(EntryDialog, "get_entry_point", MagicMock(return_value=new_entry_point_item))
    result = diagram_configuration.setup_entry_point()
    assert result
    assert new_entry_point_item.id == diagram_configuration.entry_point_item_.callable_id_


def test__change_entry_point__decline_message_box_warning__cancel_change(directory, mocker):
    diagram_configuration = setup_diagram_configuration(directory, mocker)
    entry_point_item = diagram_configuration.entry_point_item_
    mocker.patch.object(QMessageBox, "question", return_value=QMessageBox.No)
    result = diagram_configuration.setup_entry_point()

    assert entry_point_item == diagram_configuration.entry_point_item_
    assert not result


def test__dialog_reject__quit_application(mocker):
    called = []
    mocker.patch.object(EntryDialog, "exec", return_value=None)
    mocker.patch.object(EntryDialog, "result", return_value=QDialog.Rejected)
    mocker.patch.object(QApplication, "quit", lambda _: called.append(1))
    DiagramConfiguration()
    assert called == [1]

