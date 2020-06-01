# Copyright (C) 2020 R. Knuus

from INCode.clang_access import ClangCallGraphAccess, ClangTUAccess


class CallTreeManager(object):
    ''' Manages call-tree related use cases '''
    def __init__(self):
        super(CallTreeManager, self).__init__()
        self.extra_arguments_ = ''
        self.tu_access_ = None

    def open(self, file_name):
        self.tu_access_ = ClangTUAccess(file_name=file_name, extra_arguments=self.extra_arguments_)
        return self.tu_access_.files.keys()

    def set_extra_arguments(self, extra_arguments):
        # TODO(KNR): ensure that open is not yet called
        self.extra_arguments_ = extra_arguments

    def select_tu(self, file_name, include_system_headers=False):
        # TODO(KNR): handle error if self.tu_access_ is None (i.e. open was not yet called)
        if file_name not in self.tu_access_.files:
            # TODO(KNR): handle error
            pass
        compiler_arguments = self.tu_access_.files[file_name]
        call_graph_access = ClangCallGraphAccess()
        call_graph_access.parse_tu(tu_file_name=file_name, compiler_arguments=compiler_arguments,
                                   include_system_headers=include_system_headers)
        return call_graph_access.callables

    def dump(self, file_name, entry_point, include_system_headers=False, extra_arguments=None):
        tu_access = ClangTUAccess(file_name=file_name, extra_arguments=extra_arguments)
        call_graph_access = ClangCallGraphAccess()
        for file, compiler_arguments in tu_access.files.items():
            print('parsing {} with compiler arguments {}'.format(file, compiler_arguments))
            call_graph_access.parse_tu(tu_file_name=file, compiler_arguments=compiler_arguments,
                                       include_system_headers=include_system_headers)
        return self.dump_callable_(entry_point, 0, call_graph_access)

    def dump_callable_(self, callable, level, call_graph_access):
        indentation = level * '  '
        call_tree = '{}{}\n'.format(indentation, callable)
        for call in call_graph_access.get_calls_of(callable):
            call_tree += self.dump_callable_(call, level + 1, call_graph_access)
        return call_tree
