# Copyright (C) 2018 R. Knuus

from clang.cindex import CursorKind, TranslationUnitLoadError, Cursor
from clang import cindex
from abc import ABC, abstractmethod
import os
import re


def _get_method_signature(cursor):
    return '{} {}::{}'.format(cursor.result_type.spelling, cursor.semantic_parent.displayname, cursor.displayname)


def _get_function_signature(cursor):
    return '{} {}'.format(cursor.result_type.spelling, cursor.displayname)


def _get_function_pointer_signature(cursor):
    return '{} {}'.format(cursor.type.spelling, cursor.displayname)


def _get_function_sender(cursor):
    return cursor.translation_unit.spelling.replace(Index().common_path, '')


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
        print("Loading {}...".format(file))
        f = File(file, command)
        self.file_table_[file] = f
        return f

    def load_definition(self, declaration):
        file_path = os.path.abspath(declaration.cursor_.location.file.name)
        if file_path.startswith("/usr/include/"):
            return declaration

        translation_units = list(Index._gen_open(self.compilation_databases_.get_files()))
        candidates = list(Index._gen_search(declaration.cursor_.spelling, translation_units))

        file_name = os.path.basename(file_path).rsplit(".", 1)  # Extract filename from path
        file_name = (".".join(file_name[:-1]) if len(file_name) > 1 else file_name[0]).lower()  # Remove Extension

        print("Searching {}".format(file_path))
        files_with_equal_name = list(filter(lambda f: file_name in os.path.basename(f), candidates))
        if self._load_and_check(files_with_equal_name, declaration.id):
            return self.callable_table_[declaration.id]

        candidates = list(filter(lambda c: c not in files_with_equal_name, candidates))
        original_file_path = file_path
        count = len(candidates)
        if count <= 3:
            if self._load_and_check(candidates, declaration.id):
                return self.callable_table_[declaration.id]
        else:
            definition = self._search_definition_in_directory(candidates, declaration.id, file_path)
            if definition:
                return definition
        print("Couldn't find definition for {} ({}) Found files: {}"
              .format(declaration.name, original_file_path, count))
        return declaration

    def _search_definition_in_directory(self, files, declaration_id, file_path):
        file_path = "/".join(file_path.rsplit("/", 1)[:-1])
        if file_path:
            candidates = list(filter(lambda f: file_path == "/".join(f.rsplit("/", 1)[:-1]), files))
            if self._load_and_check(candidates, declaration_id):
                return self.callable_table_[declaration_id]
            candidates = list(filter(lambda c: c not in candidates, files))
            return self._search_definition_in_directory(candidates, declaration_id, file_path)
        return None

    def _load_and_check(self, files, declaration_id):
        for file in files:
            self.load(file)
        return self.callable_table_[declaration_id].is_definition()

    def register(self, callable):
        # don't replace with new callable if the old one already is a definition
        if not self.is_interesting(callable.cursor_):
            return
        self.callable_table_[callable.id] = callable

    def lookup(self, usr):
        if usr not in self.callable_table_:
            return None
        return self.callable_table_[usr]

    def is_interesting(self, cursor):
        return (cursor.get_usr() not in self.callable_table_ or
                (cursor.is_definition() and len(self.callable_table_[cursor.get_usr()].referenced_usrs_) == 0))

    @property
    def common_path(self):
        return self.common_path_

    @common_path.setter
    def common_path(self, path):
        if path is None:
            path = ''
        self.common_path_ = path

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
        self.file_name_ = file
        try:
            index = Index()
            self.tu_ = index.get_clang_index().parse(None, command)

            self._load_cursors(self.tu_.cursor.get_children())
        except TranslationUnitLoadError:
            raise ValueError('Cannot parse file {}'.format(file))

    def _load_cursors(self, cursors):
        for cursor in cursors:
            if cursor.location.file is not None and cursor.location.file.name == self.file_name_:
                if Callable._is_a_callable(cursor) and Index().is_interesting(cursor) and Caller.is_supported(cursor):
                    callable = Callable(cursor)
                    if callable.id not in self.callable_usrs_:
                        self.callable_usrs_.append(callable.id)
                    Index().register(callable)
                self._load_cursors(cursor.get_children())

    @property
    def callables(self):
        return [Index().lookup(usr) for usr in self.callable_usrs_]


class Callable(object):
    '''Represents a callable and provides a list of referenced callables.'''

    def __init__(self, cursor, initialize=True):
        super(Callable, self).__init__()
        self.cursor_ = cursor
        self.caller_ = caller_factory(self.cursor_)
        self.referenced_usrs_ = []
        if initialize:
            self.initialize()

    @property
    def name(self):
        return self.caller.get_name()

    @property
    def sender(self):
        return self.caller.get_sender()

    @property
    def id(self):
        return self.cursor_.get_usr()

    def get_translation_unit(self):
        return self.cursor_.translation_unit.spelling

    def is_definition(self):
        return self.cursor_.is_definition()

    @property
    def referenced_callables(self):
        return [Index().lookup(usr) for usr in self.referenced_usrs_]

    @property
    def caller(self):
        return self.caller_

    def initialize(self):
        self._load_cursors(self.cursor_.get_children())

    def _load_cursors(self, cursors):
        for cursor in cursors:
            if cursor.kind != CursorKind.LAMBDA_EXPR:
                self._load_cursors(cursor.get_children())
            if Callable._is_a_call(cursor) and Index().is_interesting(cursor):
                definition = cursor.referenced if cursor.referenced else cursor
                if Caller.is_supported(definition) and definition.get_usr():
                    callable = Callable(definition, False)
                    if callable.id not in self.referenced_usrs_:
                        self.referenced_usrs_.append(callable.id)
                    Index().register(callable)

    @staticmethod
    def _is_a_call(cursor):
        return cursor.kind in [CursorKind.CALL_EXPR]

    @staticmethod
    def _is_a_callable(cursor):
        return cursor.kind  in [CursorKind.FUNCTION_DECL, CursorKind.CXX_METHOD, CursorKind.CONVERSION_FUNCTION]


class Caller(ABC):
    '''Represents a caller and provides an abstract class for different types of callers.'''

    def __init__(self, cursor):
        super(Caller, self).__init__()
        self.cursor_ = cursor

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_diagram_name(self):
        pass

    @abstractmethod
    def get_sender(self):
        pass

    @staticmethod
    def is_supported(cursor):
        return caller_factory(cursor) is not None


class Function(Caller):
    def __init__(self, cursor):
        super(Function, self).__init__(cursor)

    def get_name(self):
        return _get_function_signature(self.cursor_)

    def get_diagram_name(self):
        return _get_function_signature(self.cursor_)

    def get_sender(self):
        return _get_function_sender(self.cursor_)


class Method(Caller):
    def __init__(self, cursor):
        super(Method, self).__init__(cursor)

    def get_name(self):
        return _get_method_signature(self.cursor_)

    def get_diagram_name(self):
        return _get_function_signature(self.cursor_)

    def get_sender(self):
        return self.cursor_.semantic_parent.displayname


class Constructor(Caller):
    def __init__(self, cursor):
        super(Constructor, self).__init__(cursor)

    def get_name(self):
        return _get_method_signature(self.cursor_)

    def get_diagram_name(self):
        return _get_function_signature(self.cursor_)

    def get_sender(self):
        return self.cursor_.semantic_parent.displayname


class Destructor(Caller):
    def __init__(self, cursor):
        super(Destructor, self).__init__(cursor)

    def get_name(self):
        return _get_method_signature(self.cursor_)

    def get_diagram_name(self):
        return _get_function_signature(self.cursor_)

    def get_sender(self):
        return self.cursor_.semantic_parent.displayname


class FunctionPointer(Caller):
    def __init__(self, cursor):
        super(FunctionPointer, self).__init__(cursor)

    def get_name(self):
        return _get_function_pointer_signature(self.cursor_)

    def get_diagram_name(self):
        return '{}'.format(self.cursor_.type.spelling).replace("(*)", "(* {})".format(self.cursor_.displayname))

    def get_sender(self):
        return _get_function_sender(self.cursor_)


class Conversion(Caller):
    def __init__(self, cursor):
        super(Conversion, self).__init__(cursor)

    def get_name(self):
        return '{}::{}'.format(self.get_sender(), self.cursor_.displayname)

    def get_diagram_name(self):
        return self.cursor_.displayname

    def get_sender(self):
        return self.cursor_.semantic_parent.displayname


def caller_factory(cursor):
    if not cursor:
        return
    switcher = {
        CursorKind.FUNCTION_DECL: Function(cursor),
        CursorKind.CXX_METHOD: Method(cursor),
        CursorKind.CONSTRUCTOR: Constructor(cursor),
        CursorKind.DESTRUCTOR: Destructor(cursor),
        CursorKind.VAR_DECL: FunctionPointer(cursor),
        CursorKind.CONVERSION_FUNCTION: Conversion(cursor)
    }
    return switcher.get(cursor.kind)
