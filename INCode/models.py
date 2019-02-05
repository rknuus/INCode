# Copyright (C) 2018 R. Knuus

from clang.cindex import CursorKind, TranslationUnitLoadError
from clang import cindex
import re


def _get_method_signature(cursor):
    return '{} {}::{}'.format(cursor.result_type.spelling, cursor.semantic_parent.displayname, cursor.displayname)


def _get_function_signature(cursor):
    return '{} {}'.format(cursor.result_type.spelling, cursor.displayname)


class CompilationDatabases(object):
    '''Represents a compilation database.'''

    def __init__(self):
        super(CompilationDatabases, self).__init__()
        self.compilation_databases_ = {}

    def add_compilation_database(self, compilation_database_directory):
        db = cindex.CompilationDatabase.fromDirectory(compilation_database_directory)
        self.compilation_databases_[compilation_database_directory] = db

    def get_files(self):
        return [compile_command.filename for compilation_database in self.compilation_databases_.values() for
                compile_command in compilation_database.getAllCompileCommands()]

    def get_command(self, file):
        for db in self.compilation_databases_.values():
            # try:
            commands = db.getCompileCommands(file)
            # TODO(KNR): WTF? why do I have to fumble around with the CompileCommands internals?
            if commands:
                assert len(commands) >= 1
                command = commands[0]
                return list(command.arguments)
            # except CompilationDatabaseError:
            #     pass  # TODO(KNR): ??
        return None


class Borg:
    __shared_state = {}

    def __init__(self):
        self.__dict__ = self.__shared_state


class Index(Borg):
    '''Represents the index of all callables and processes the compilation database as a singleton.'''

    def __init__(self, compilation_databases=None):
        Borg.__init__(self)
        if compilation_databases is not None:
            self.index_ = cindex.Index.create()
            self.callable_table_ = {}
            self.file_table_ = {}
            self.compilation_databases_ = compilation_databases
            self.common_path_ = ''

    def load(self, file):
        # TODO(KNR): assumes that the file name is unique
        if file in self.file_table_:
            return self.file_table_[file]
        command = self.compilation_databases_.get_command(file)
        if not command:
            raise ValueError('No compilation command found for {}'.format(file))
        f = File(file, command)
        self.file_table_[file] = f
        return f

    def load_definition(self, declaration):
        translation_units = Index._gen_open(self.compilation_databases_.get_files())
        candidates = Index._gen_search(declaration.cursor_.spelling, translation_units)
        for candidate in candidates:
            self.load(candidate)
        return self.callable_table_[declaration.get_id()]

    def register(self, callable):
        # don't replace with new callable if the old one already is a definition
        if not self.is_interesting(callable.cursor_):
            return
        self.callable_table_[callable.get_id()] = callable

    def lookup(self, usr):
        if usr not in self.callable_table_:
            return None
        return self.callable_table_[usr]

    def is_interesting(self, cursor):
        return ((cursor.get_usr() not in self.callable_table_ or
                 (cursor.is_definition() and len(self.callable_table_[cursor.get_usr()].referenced_usrs_) == 0))
                and cursor.kind != CursorKind.CONSTRUCTOR)

    def set_common_path(self, path):
        if path is None:
            path = ''
        self.common_path_ = path

    def get_common_path(self):
        return self.common_path_

    # TODO(KNR): replace by read-only attribute
    def get_clang_index(self):
        return self.index_

    @staticmethod
    def _gen_open(files):
        for file in files:
            yield open(file)

    @staticmethod
    def _gen_search(pattern_text, files):
        pattern = re.compile(pattern_text)
        for file in files:
            filename = file.name
            for line in file:
                if pattern.search(line):
                    yield filename
                    break


class File(object):
    '''Represents a file and provides a list of callables.'''

    def __init__(self, file, command):
        super(File, self).__init__()
        self.callable_usrs_ = []
        try:
            index = Index()
            self.tu_ = index.get_clang_index().parse(None, command)

            for cursor in self.tu_.cursor.walk_preorder():
                if (cursor.location.file is not None and cursor.location.file.name == file
                        and Callable._is_a_callable(cursor) and index.is_interesting(cursor)):
                    callable = Callable(cursor)
                    if callable.get_id() not in self.callable_usrs_:
                        self.callable_usrs_.append(callable.get_id())
                    index.register(callable)
        except TranslationUnitLoadError:
            raise ValueError('Cannot parse file {}'.format(file))

    def get_callables(self):
        return [Index().lookup(usr) for usr in self.callable_usrs_]


class Callable(object):
    '''Represents a callable and provides a list of referenced callables.'''

    def __init__(self, cursor, initialize=True):
        super(Callable, self).__init__()
        self.cursor_ = cursor
        self.name_ = self._get_name()
        self.sender_ = self._get_sender()
        self.referenced_usrs_ = []
        if initialize:
            self.initialize()

    # TODO(KNR): replace by read-only attribute
    def get_name(self):
        return self.name_

    def get_id(self):
        return self.cursor_.get_usr()

    def get_translation_unit(self):
        return self.cursor_.translation_unit.spelling

    def is_definition(self):
        return self.cursor_.is_definition()

    def get_referenced_callables(self):
        return [Index().lookup(usr) for usr in self.referenced_usrs_]

    def initialize(self):
        for cursor in self.cursor_.walk_preorder():
            if Callable._is_a_call(cursor) and Index().is_interesting(cursor):
                definition = cursor.referenced
                callable = Callable(definition, False)
                if callable.get_id() not in self.referenced_usrs_ and definition.kind != CursorKind.CONSTRUCTOR:
                    self.referenced_usrs_.append(callable.get_id())
                Index().register(callable)

    @staticmethod
    def _is_a_call(cursor):
        return cursor.kind == CursorKind.CALL_EXPR

    @staticmethod
    def _is_a_callable(cursor):
        return cursor.kind == CursorKind.FUNCTION_DECL or cursor.kind == CursorKind.CXX_METHOD

    def _get_class(self):
        if self.cursor_.kind == CursorKind.CXX_METHOD:
            return self.cursor_.semantic_parent.displayname
        return '{} is not supported'.format(self.cursor_.kind)

    def _get_name(self):
        if self.cursor_.kind == CursorKind.FUNCTION_DECL:
            return _get_function_signature(self.cursor_)
        elif self.cursor_.kind == CursorKind.CXX_METHOD:
            return _get_method_signature(self.cursor_)
        return '{} is not supported'.format(self.cursor_.kind)

    def _get_diagram_name(self):
        if self.cursor_.kind == CursorKind.FUNCTION_DECL or self.cursor_.kind == CursorKind.CXX_METHOD:
            return _get_function_signature(self.cursor_)
        return '{} is not supported'.format(self.cursor_.kind)

    def _get_sender(self):
        if self.cursor_.kind == CursorKind.FUNCTION_DECL:
            return '"' + self.get_translation_unit().replace(Index().get_common_path(), '') + '"'
        elif self.cursor_.kind == CursorKind.CXX_METHOD:
            return self._get_class()
        return '{} is not supported'.format(self.cursor_.kind)
