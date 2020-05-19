# Copyright (C) 2020 R. Knuus

from clang.cindex import Cursor, CursorKind, Index
from collections import defaultdict
from os import path
import json
import os
import re
import shlex


clang_severity_str = {
    0: 'Ignored',
    1: 'Note',
    2: 'Warning',
    3: 'Error',
    4: 'Fatal'
}


def get_diagnostic_message(diag):
    file = diag.location.file.name if diag.location.file else ''
    return '{}: {} in file {}, line {}, column {}'.format(
        clang_severity_str[diag.severity], diag.spelling,
        file, diag.location.line, diag.location.column)


class ClangCallGraphAccess(object):
    '''Constructs a call tree from given TUs.'''
    def __init__(self):
        super(ClangCallGraphAccess, self).__init__()
        self.calls_of_ = defaultdict(list)
        self.callables_ = set()

    def parse_tu(self, tu_file_name, compiler_arguments, exclude_system_headers=False):
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
        if exclude_system_headers:
            self.exclude_prefixes_ = self.get_system_header_include_prefixes_(compiler_arguments)

        self.build_tree_(ast_node=tu.cursor, parent_node=None)

    def get_calls_of(self, callable):
        if callable not in self.callables_ or callable not in self.calls_of_:
            return []
        return self.calls_of_[callable]

    def build_tree_(self, ast_node, parent_node):
        if self.should_exclude_(ast_node.location.file):
            return
        if ast_node.kind == CursorKind.FUNCTION_DECL or ast_node.kind == CursorKind.CXX_METHOD:
            name = self.qualify_name(ast_node)
            self.callables_.add(name)
            parent_node = ast_node
        if ast_node.kind == CursorKind.CALL_EXPR and ast_node.referenced:
            caller_name = self.qualify_name(parent_node)
            callee_name = self.qualify_name(ast_node.referenced)
            self.calls_of_[caller_name].append(callee_name)
        for child_ast_node in ast_node.get_children():
            self.build_tree_(ast_node=child_ast_node, parent_node=parent_node)

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

    def qualify_name(self, ast_node):
        if ast_node is None or type(ast_node) != Cursor or ast_node.kind == CursorKind.TRANSLATION_UNIT:
            return ''
        qualifier = self.qualify_name(ast_node.semantic_parent)
        if qualifier != '':
            qualifier += '::'
        return qualifier + ast_node.displayname


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
        self.extra_arguments_ = extra_arguments or ''
        self.files_ = self.collect_files_(file_name)

    @property
    def files(self):
        return self.files_

    def collect_files_(self, file_name):
        if not file_name.endswith('compile_commands.json'):
            # return {file_name: filter_redundant_file_name_(file_name, ' '.join(self.extra_arguments_))}
            return {file_name: self.extra_arguments_}
        with open(file_name) as compdb:
            db = json.load(compdb)
        extra = self.extra_arguments_ if self.extra_arguments_ else []
        # BORKED(KNR):
        # arbitrarily change to first directory to handle relative paths
        # which only works as long as all directories are identical
        if len(db) > 0 and 'directory' in db[0]:
            os.chdir(db[0]['directory'])
        # END BORKED
        return {entry['file']: filter_redundant_file_name_(entry['file'], shlex.split(entry['command']) + extra)
                for entry in db}
