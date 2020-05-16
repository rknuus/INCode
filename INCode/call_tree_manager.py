# Copyright (C) 2020 R. Knuus

from INCode.clang_access import ClangCallGraphAccess, ClangTUAccess


class CallTreeManager(object):
    ''' Manages call-tree related use cases '''
    def __init__(self):
        super(CallTreeManager, self).__init__()

    def dump(self, file_name, entry_point):
        tu_access = ClangTUAccess(file_name=file_name)
        call_graph_access = ClangCallGraphAccess()
        for file, compiler_arguments in tu_access.files.items():
            call_graph_access.parse_tu(tu=file, compiler_arguments=compiler_arguments)
        call_tree = '{}\n'.format(entry_point)
        for call in call_graph_access.get_calls_of(entry_point):
            call_tree += '  {}\n'.format(call)
        return call_tree
