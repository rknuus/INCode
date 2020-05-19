# Copyright (C) 2020 R. Knuus

from INCode.clang_access import ClangCallGraphAccess, ClangTUAccess


class CallTreeManager(object):
    ''' Manages call-tree related use cases '''
    def __init__(self):
        super(CallTreeManager, self).__init__()

    def dump(self, file_name, entry_point, exclude_system_headers=False, extra_arguments=None):
        tu_access = ClangTUAccess(file_name=file_name, extra_arguments=extra_arguments)
        call_graph_access = ClangCallGraphAccess()
        for file, compiler_arguments in tu_access.files.items():
            print('parsing {} with compiler arguments {}'.format(file, compiler_arguments))
            call_graph_access.parse_tu(tu_file_name=file, compiler_arguments=compiler_arguments,
                                       exclude_system_headers=exclude_system_headers)
        return self.dump_callable_(entry_point, 0, call_graph_access)

    def dump_callable_(self, callable, level, call_graph_access):
        indentation = level * '  '
        call_tree = '{}{}\n'.format(indentation, callable)
        for call in call_graph_access.get_calls_of(callable):
            call_tree += self.dump_callable_(call, level + 1, call_graph_access)
        return call_tree
