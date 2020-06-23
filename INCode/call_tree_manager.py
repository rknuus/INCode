# Copyright (C) 2020 R. Knuus

from enum import Enum
from INCode.clang_access import ClangCallGraphAccess, ClangTUAccess, set_global_common_path
import os
import warnings


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


class CallTreeManagerState(Enum):
    INITIALIZED = 1
    EXTRA_ARGUMENTS_INITIALIZED = 2
    READY_TO_SELECT_TU = 3
    READY_TO_SELECT_ROOT = 4
    READY_FOR_INTERACTIONS = 5


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
        self.state_ = CallTreeManagerState.INITIALIZED

    def set_extra_arguments(self, extra_arguments):
        if self.state_ not in [CallTreeManagerState.INITIALIZED,
                               CallTreeManagerState.EXTRA_ARGUMENTS_INITIALIZED]:
            warnings.warn('Unsupported state transition from {} to {}'.format(
                self.state_, CallTreeManagerState.EXTRA_ARGUMENTS_INITIALIZED))
            return
        self.extra_arguments_ = extra_arguments
        self.state_ = CallTreeManagerState.EXTRA_ARGUMENTS_INITIALIZED

    def open(self, file_name):
        if self.state_ not in [CallTreeManagerState.INITIALIZED,
                               CallTreeManagerState.EXTRA_ARGUMENTS_INITIALIZED,
                               CallTreeManagerState.READY_TO_SELECT_TU]:
            warnings.warn('Unsupported state transition from {} to {}'.format(
                self.state_, CallTreeManagerState.READY_TO_SELECT_TU))
            return
        self.tu_access_ = ClangTUAccess(file_name=file_name, extra_arguments=self.extra_arguments_)
        set_global_common_path(find_common_path(list(self.tu_access_.files)))
        self.state_ = CallTreeManagerState.READY_TO_SELECT_TU
        return self.tu_access_.files.keys()

    def select_tu(self, file_name, include_system_headers=False):
        if self.state_ not in [CallTreeManagerState.READY_TO_SELECT_TU,
                               CallTreeManagerState.READY_TO_SELECT_ROOT]:
            warnings.warn('Unsupported state transition from {} to {}'.format(
                self.state_, CallTreeManagerState.READY_TO_SELECT_ROOT))
            return
        if file_name not in self.tu_access_.files:
            warnings.warn('File {} not found in compilation database'.format(file_name))
            return
        compiler_arguments = self.tu_access_.files[file_name]
        self.include_system_headers_ = include_system_headers
        self.call_graph_access_ = ClangCallGraphAccess()
        self.call_graph_access_.parse_tu(tu_file_name=file_name, compiler_arguments=compiler_arguments,
                                         include_system_headers=include_system_headers)
        self.loaded_files_.add(file_name)
        self.state_ = CallTreeManagerState.READY_TO_SELECT_ROOT
        return self.call_graph_access_.get_callables_in(file_name)

    def select_root(self, callable_name):
        if self.state_ not in [CallTreeManagerState.READY_TO_SELECT_ROOT,
                               CallTreeManagerState.READY_FOR_INTERACTIONS]:
            warnings.warn('Unsupported state transition from {} to {}'.format(
                self.state_, CallTreeManagerState.READY_FOR_INTERACTIONS))
            return
        self.root_ = self.call_graph_access_.get_callable(callable_name)
        self.state_ = CallTreeManagerState.READY_FOR_INTERACTIONS
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
                    return callable

    def get_calls_of(self, callable_name):
        return self.call_graph_access_.get_calls_of(callable_name)

    def include(self, callable_name):
        self.included_.add(callable_name)

    def exclude(self, callable_name):
        if callable_name in self.included_:
            self.included_.remove(callable_name)

    def export(self):
        # TODO(KNR): not sure whether it works for included-root at lower level
        call_tree = ''
        if self.root_.name in self.included_:
            call_tree = ' -> ' + quote(self.root_.participant) + ': ' + self.root_.callable + '\n'
            call_tree += 'activate {}\n'.format(quote(self.root_.participant))
        call_tree += self.export_calls_(parent=self.root_, included_parent_name='')
        if self.root_.name in self.included_:
            call_tree += 'deactivate {}\n'.format(quote(self.root_.participant))
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
                # TODO(KNR): avoid redundant activations
                call_tree += 'activate {}\n'.format(quote(call.participant))
            call_tree += self.export_calls_(parent=call, included_parent_name=parent_name)
            if call.name in self.included_:
                call_tree += 'deactivate {}\n'.format(quote(call.participant))
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
