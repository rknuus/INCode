# Copyright (C) 2020 R. Knuus

from clang.cindex import Cursor, CursorKind, Index
from collections import defaultdict
from os import path
import json
import os
import re
import shlex


GLOBAL_COMMON_PATH = ''


def set_global_common_path(path):
    global GLOBAL_COMMON_PATH
    GLOBAL_COMMON_PATH = path


clang_severity_str = {
    0: 'Ignored',
    1: 'Note',
    2: 'Warning',
    3: 'Error',
    4: 'Fatal'
}


def get_file_name(diag_or_ast_node):
    if diag_or_ast_node is None or diag_or_ast_node.location is None or diag_or_ast_node.location.file is None:
        return ''
    return diag_or_ast_node.location.file.name


def get_diagnostic_message(diag):
    file = get_file_name(diag)
    return '{}: {} in file {}, line {}, column {}'.format(
        clang_severity_str[diag.severity], diag.spelling,
        file, diag.location.line, diag.location.column)


def qualify_name(cursor):
    if cursor is None or type(cursor) != Cursor or cursor.kind == CursorKind.TRANSLATION_UNIT:
        return ''
    qualifier = qualify_name(cursor.semantic_parent)
    if qualifier != '':
        qualifier += '::'
    return qualifier + cursor.displayname


class Callable(object):
    def __init__(self, cursor):
        super(Callable, self).__init__()
        self.cursor_ = cursor

    @property
    def name(self):
        return qualify_name(self.cursor_)

    @property
    def file_name(self):
        return get_file_name(self.cursor_)

    @property
    def participant(self):
        if self.cursor_.kind == CursorKind.FUNCTION_DECL:
            return self.cursor_.translation_unit.spelling.replace(GLOBAL_COMMON_PATH, '')
        return qualify_name(self.cursor_.semantic_parent)

    @property
    def callable(self):
        return self.cursor_.displayname

    def get_spelling(self):
        return self.cursor_.spelling

    def is_definition(self):
        return self.cursor_.is_definition()


class ClangCallGraphAccess(object):
    '''Constructs a call tree from given TUs.'''
    def __init__(self):
        super(ClangCallGraphAccess, self).__init__()
        self.calls_of_ = defaultdict(list)
        self.callables_ = dict()

    def parse_tu(self, tu_file_name, compiler_arguments, include_system_headers=False):
        if not path.exists(tu_file_name):
            raise FileNotFoundError(tu_file_name)
        index = Index.create()
        tu = index.parse(tu_file_name, compiler_arguments)
        assert tu

        error_messages = [get_diagnostic_message(d) for d in tu.diagnostics
                          if d.severity in [d.Error, d.Fatal]]
        if len(error_messages) > 0:
            raise SyntaxError('\n'.join(error_messages))

        self.exclude_prefixes_ = []
        if not include_system_headers:
            self.exclude_prefixes_ = self.get_system_header_include_prefixes_(compiler_arguments)

        self.build_tree_(ast_node=tu.cursor, parent_node=None)

    @property
    def callables(self):
        return {name: Callable(callable) for name, callable in self.callables_.items()}

    def get_callable(self, callable_name):
        return Callable(self.callables_[callable_name])

    def get_callables_in(self, file_name):
        return [callable for callable in self.callables.values() if callable.file_name == file_name]

    def get_calls_of(self, callable_name):
        if callable_name not in self.calls_of_:
            return []
        return [Callable(child) for child in self.calls_of_[callable_name]]

    def build_tree_(self, ast_node, parent_node, depth=0):
        if ast_node.kind == CursorKind.FUNCTION_DECL or ast_node.kind == CursorKind.CXX_METHOD:
            name = qualify_name(ast_node)
            self.callables_[name] = ast_node
            parent_node = ast_node
        if ast_node.kind == CursorKind.CALL_EXPR and ast_node.referenced:
            caller_name = qualify_name(parent_node)
            self.calls_of_[caller_name].append(ast_node.referenced)
            callee_name = qualify_name(ast_node.referenced)
            if callee_name not in self.callables_:
                self.callables_[callee_name] = ast_node.referenced
        for child_ast_node in ast_node.get_children():
            self.build_tree_(ast_node=child_ast_node, parent_node=parent_node, depth=depth + 1)

    def get_system_header_include_prefixes_(self, compiler_arguments):
        # -isystem <path>
        exclude_prefixes = []
        for i in range(len(compiler_arguments)-1):
            if compiler_arguments[i] == 'isystem':
                exclude_prefixes.append(compiler_arguments[i + 1])
        return exclude_prefixes

    def should_exclude_(self, file_name):
        for pattern in self.exclude_prefixes_:
            if file_name.startswith(pattern):
                return True
        return False


def filter_redundant_file_name_(file_name, command):
    dash_c_option_pattern = re.compile('(-c\\s+{})'.format(file_name))
    command_string = ' '.join(command)
    match = dash_c_option_pattern.search(command_string)
    if match:
        return shlex.split(command_string.replace(match.group(0), ''))
    return command


class ClangTUAccess(object):
    '''Returns files and their compiler arguments from a compilation database.'''
    def __init__(self, file_name, extra_arguments=None):
        super(ClangTUAccess, self).__init__()
        # TODO(KNR): borked, don't want to perform type-check
        args = extra_arguments
        if isinstance(args, str):  # TODO(KNR): might not work for unicode?!
            args = shlex.split(args)
        elif type(args) == type(None):
            args = []
        else:
            assert hasattr(args, '__iter__')
        self.extra_arguments_ = args
        self.files_ = self.collect_files_(file_name)

    @property
    def files(self):
        return self.files_

    def collect_files_(self, file_name):
        if not path.exists(file_name):
            raise FileNotFoundError(file_name)

        if not file_name.endswith('compile_commands.json'):
            # return {file_name: filter_redundant_file_name_(file_name, ' '.join(self.extra_arguments_))}
            return {file_name: self.extra_arguments_}
        with open(file_name) as compdb:
            db = json.load(compdb)
        extra = self.extra_arguments_ if self.extra_arguments_ else []
        # BORKED(KNR):
        # arbitrarily change to first directory to handle relative paths
        # which only works as long as all directories are identical
        # TODO(KNR): add directory to dict and move chdir call to ClangCallGraphAccess.parse_tu
        if len(db) > 0 and 'directory' in db[0]:
            os.chdir(db[0]['directory'])
        # END BORKED
        return {entry['file']: filter_redundant_file_name_(entry['file'], shlex.split(entry['command']) + extra)
                for entry in db}
