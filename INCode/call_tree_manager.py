# Copyright (C) 2020 R. Knuus

from INCode.clang_access import ClangCallGraphAccess, ClangTUAccess, set_global_common_path
from pubsub import pub
import os


def find_text_in_file_(file_name, text):
    with open(file_name) as file:
        for line in file:
            if text in line:
                return True
    return False


def rate_path_commonality_(reference_name, other_name):
    return len(os.path.commonpath([os.path.abspath(reference_name), os.path.abspath(other_name)]))


def find_common_path(paths):
    assert len(paths) > 0
    if len(paths) == 1:
        common_path = os.path.dirname(paths[0]) + '/'
    else:
        common_path = os.path.commonpath(os.path.abspath(p) for p in paths)
    return common_path


def quote(text):
    if not text:
        return text
    return '"{}"'.format(text)


class CallTreeManager(object):
    ''' Manages call-tree related use cases '''
    def __init__(self):
        super(CallTreeManager, self).__init__()
        self.extra_arguments_ = ''
        self.tu_access_ = None
        self.call_graph_access_ = None
        self.include_system_headers_ = False
        self.loaded_files_ = set()
        self.included_ = set()
        self.root_ = None

    def set_extra_arguments(self, extra_arguments):
        # TODO(KNR): ensure that open is not yet called
        self.extra_arguments_ = extra_arguments

    def open(self, file_name):
        self.tu_access_ = ClangTUAccess(file_name=file_name, extra_arguments=self.extra_arguments_)
        set_global_common_path(find_common_path(list(self.tu_access_.files)))
        return self.tu_access_.files.keys()

    def select_tu(self, file_name, include_system_headers=False):
        # TODO(KNR): handle error if self.tu_access_ is None (i.e. open was not yet called)
        if file_name not in self.tu_access_.files:
            # TODO(KNR): handle error
            pass
        compiler_arguments = self.tu_access_.files[file_name]
        self.include_system_headers_ = include_system_headers
        self.call_graph_access_ = ClangCallGraphAccess()
        self.call_graph_access_.parse_tu(tu_file_name=file_name, compiler_arguments=compiler_arguments,
                                         include_system_headers=include_system_headers)
        self.loaded_files_.add(file_name)
        return self.call_graph_access_.get_callables_in(file_name)

    def select_root(self, callable_name):
        self.root_ = self.call_graph_access_.get_callable(callable_name)
        return self.root_

    def load_definition(self, callable_name):
        # TODO(KNR): store include_system_headers passed to select_tu or pass it otherwise
        # (e.g. to set_extra_arguments or as separate method)
        for file_name, compiler_arguments in self.list_tu_candidates_(callable_name).items():
            if file_name not in self.loaded_files_:
                self.call_graph_access_.parse_tu(tu_file_name=file_name, compiler_arguments=compiler_arguments,
                                                 include_system_headers=self.include_system_headers_)
                self.loaded_files_.add(file_name)
                callable = self.call_graph_access_.get_callable(callable_name)
                if callable and callable.is_definition():
                    pub.sendMessage('update_node_data', new_data=callable)
                    return callable  # TODO(KNR): by returning the new callable there is no need for sending a message

    def get_calls_of(self, callable_name):
        return self.call_graph_access_.get_calls_of(callable_name)

    def include(self, callable_name):
        self.included_.add(callable_name)
        pub.sendMessage('node_included', node_name=callable_name)

    def exclude(self, callable_name):
        if callable_name in self.included_:
            self.included_.remove(callable_name)
        pub.sendMessage('node_excluded', node_name=callable_name)

    def export(self):
        # TODO(KNR): not sure whether it works for included-root at lower level
        call_tree = ''
        if self.root_.name in self.included_:
            call_tree = ' -> ' + quote(self.root_.participant) + ': ' + self.root_.callable + '\n'
        call_tree += self.export_calls_(parent=self.root_, included_parent_name='')
        return '@startuml\n\n{}\n@enduml'.format(call_tree)

    def export_calls_(self, parent, included_parent_name):
        call_tree = ''
        if parent is None:
            return call_tree
        parent_name = included_parent_name
        if parent.name in self.included_:
            parent_name = parent.participant
        for call in self.call_graph_access_.get_calls_of(parent.name):
            if call.name in self.included_:
                call_tree += quote(parent_name) + ' -> ' + quote(call.participant) + ': ' + call.callable + '\n'
            call_tree += self.export_calls_(parent=call, included_parent_name=parent_name)
        return call_tree

    def dump(self, file_name, entry_point, include_system_headers=False, extra_arguments=None):
        tu_access = ClangTUAccess(file_name=file_name, extra_arguments=extra_arguments)
        self.call_graph_access_ = ClangCallGraphAccess()
        for file_name, compiler_arguments in tu_access.files.items():
            self.call_graph_access_.parse_tu(tu_file_name=file_name, compiler_arguments=compiler_arguments,
                                             include_system_headers=include_system_headers)
        root = self.call_graph_access_.get_callable(entry_point)
        return self.dump_callable_(root, 0)

    def list_tu_candidates_(self, callable_name):
        callable = self.call_graph_access_.get_callable(callable_name)
        assert callable  # TODO(KNR): be nicer
        if callable.is_definition():  # TODO(KNR): not sure whether required
            return

        search_key = callable.get_spelling()
        tu_candidates = {file_name: compiler_arguments
                         for file_name, compiler_arguments in self.tu_access_.files.items()
                         if find_text_in_file_(file_name=file_name, text=search_key)}
        used_in_file_name = callable.cursor_.translation_unit.spelling  # TODO(KNR): replace shortcut
        # TODO(KNR): figure out how to avoid Decorate-Sort-Undecorate idiom
        decorated = [(rate_path_commonality_(used_in_file_name, file_name), file_name, compiler_arguments)
                     for file_name, compiler_arguments in tu_candidates.items()]
        decorated.sort(reverse=True)
        tu_candidates = {file_name: compiler_arguments for _, file_name, compiler_arguments in decorated}
        return tu_candidates

    def dump_callable_(self, callable, level):
        indentation = level * '  '
        call_tree = '{}{}\n'.format(indentation, callable.name)
        for call in self.call_graph_access_.get_calls_of(callable.name):
            call_tree += self.dump_callable_(call, level + 1)
        return call_tree
