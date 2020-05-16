# Copyright (C) 2020 R. Knuus

from clang.cindex import CursorKind, Index
from collections import defaultdict
from os import path
import json


clang_severity_str = {
    0: 'Ignored',
    1: 'Note',
    2: 'Warning',
    3: 'Error',
    4: 'Fatal'
}


def get_diagnostic_message(diag):
    return '{}: {} in file {}, line {}, column {}'.format(
        clang_severity_str[diag.severity], diag.spelling,
        diag.location.file.name, diag.location.line, diag.location.column)


class ClangCallGraphAccess(object):
    '''Constructs a call tree from given TUs.'''
    def __init__(self):
        super(ClangCallGraphAccess, self).__init__()
        self.calls_of_ = defaultdict(list)

    def parse_tu(self, tu, compiler_arguments):
        if not path.exists(tu):
            raise FileNotFoundError(tu)
        index = Index.create()
        tu = index.parse(tu, compiler_arguments)
        assert tu

        error_messages = [get_diagnostic_message(d) for d in tu.diagnostics
                          if d.severity in [d.Error, d.Fatal]]
        if len(error_messages) > 0:
            raise SyntaxError('\n'.join(error_messages))

        self.build_tree_(ast_node=tu.cursor, parent_node='')

    def get_calls_of(self, callable):
        return self.calls_of_[callable]

    def build_tree_(self, ast_node, parent_node):
        # NOTE(KNR): Creating Nodes for function declarations creates redundant
        #            Nodes. Either delay Node creation or prune the tree afterwards.
        if ast_node.kind == CursorKind.FUNCTION_DECL:
            parent_node = ast_node.displayname
        if ast_node.kind == CursorKind.CALL_EXPR:
            self.calls_of_[parent_node].append(ast_node.referenced.displayname)
        for child_ast_node in ast_node.get_children():
            self.build_tree_(ast_node=child_ast_node, parent_node=parent_node)


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
            return {file_name: self.extra_arguments_}
        with open(file_name) as compdb:
            db = json.load(compdb)
        return {entry['file']: entry['command'] for entry in db}