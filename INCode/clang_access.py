# Copyright (C) 2020 R. Knuus

from clang.cindex import CursorKind, Index
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


class ClangCalltreeAccess(object):
    '''Constructs a call tree from given TUs.'''
    def __init__(self):
        super(ClangCalltreeAccess, self).__init__()
        self.call_tree_ = []

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

        self.parse_(tu.cursor)

    @property
    def call_tree(self):
        return self.call_tree_

    def parse_(self, node):
        if node.kind == CursorKind.FUNCTION_DECL:
            self.call_tree_.append(node.displayname)
        for child in node.get_children():
            self.parse_(child)


class ClangTUAccess(object):
    '''Returns files and their compiler arguments from a compilation database.'''
    def __init__(self, filename, extra_arguments=None):
        super(ClangTUAccess, self).__init__()
        self.extra_arguments_ = extra_arguments or ''
        self.files_ = self.collect_files_(filename)

    @property
    def files(self):
        return self.files_

    def collect_files_(self, filename):
        if not filename.endswith('compile_commands.json'):
            return {filename: self.extra_arguments_}
        with open(filename) as compdb:
            db = json.load(compdb)
        return {entry['file']: entry['command'] for entry in db}
