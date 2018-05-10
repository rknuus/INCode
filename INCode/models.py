# Copyright (C) 2018 R. Knuus

from clang.cindex import CursorKind, TranslationUnitLoadError
from clang import cindex
import re


def _get_function_signature(cursor):
    return '{} {}'.format(cursor.result_type.spelling, cursor.displayname)


def gen_open(files):
    for file in files:
        yield open(file)


def gen_search(pattern_text, files):
    pattern = re.compile(pattern_text)
    for file in files:
        filename = file.name
        for line in file:
            if pattern.search(line):
                yield filename
                break


def append_or_update(callable, list):
    # intentionally not performance-optimized
    for i, c in enumerate(list):
        if c.get_usr() == callable.get_usr():
            list[i] = callable
            break
    else:
        list.append(callable)


class Index(object):
    def __init__(self):
        super(Index, self).__init__()
        self.index_ = cindex.Index.create()
        self.callable_table_ = {}
        self.file_table_ = {}
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

    def load(self, file):
        # TODO(KNR): assumes that the file name is unique
        if file in self.file_table_:
            return self.file_table_[file]
        command = self.get_command(file)
        if not command:
            raise ValueError('No compilation command found for {}'.format(file))
        f = File(file, self, command)
        self.file_table_[file] = f
        return f

    # TODO(KNR): is kwargs still required/useful?
    def load_definition(self, declaration_cursor, **kwargs):
        translation_units = gen_open(self.get_files())
        candidates = gen_search(declaration_cursor.get_name(), translation_units)
        for candidate in candidates:
            self.load(candidate, **kwargs)
        return self.callable_table_[declaration_cursor.get_usr()]

    def register(self, callable):
        # don't replace with new callable if the old one already is a definition
        if not self.is_interesting(callable):
            return
        self.callable_table_[callable.get_usr()] = callable

    def is_interesting(self, callable):
        return (callable.get_usr() not in self.callable_table_ or callable.is_definition())

    # TODO(KNR): replace by read-only attribute
    def get_clang_index(self):
        return self.index_


class File(object):
    '''Represents a file and provides a list of callables.'''

    def __init__(self, file, index, command):
        super(File, self).__init__()
        self.index_ = index
        try:
            self.tu_ = self.index_.get_clang_index().parse(None, command)
            self._initialize_callables()
        except TranslationUnitLoadError:
            raise ValueError('Cannot parse file {}'.format(file))

    def get_callables(self):
        return self.callables_

    def _initialize_callables(self):
        self.callables_ = []
        for cursor in self.tu_.cursor.walk_preorder():
            if cursor.location.file is not None and cursor.kind == CursorKind.FUNCTION_DECL:
                callable = Callable(_get_function_signature(cursor), cursor, self.index_)
                if self.index_.is_interesting(callable):
                    append_or_update(callable, self.callables_)
                    self.index_.register(callable)


class Callable(object):
    '''Represents a Callable and provides a list of callables used by this callable.'''

    def __init__(self, name, cursor, index, initialize=True):
        super(Callable, self).__init__()
        self.name_ = name
        self.cursor_ = cursor
        self.index_ = index
        if initialize:
            self._initialize_referenced_callables()

    # TODO(KNR): replace by read-only attribute
    def get_name(self):
        return self.name_

    def get_usr(self):
        return self.cursor_.get_usr()

    def is_definition(self):
        return self.cursor_.is_definition()

    def get_referenced_callables(self):
        return self.referenced_callables_

    def _initialize_referenced_callables(self):
        self.referenced_callables_ = []
        for cursor in self.cursor_.walk_preorder():
            if cursor.kind == CursorKind.CALL_EXPR:
                definition = cursor.referenced
                callable = Callable(_get_function_signature(definition), definition, self.index_, False)
                if self.index_.is_interesting(callable):
                    append_or_update(callable, self.referenced_callables_)
                    callable._initialize_referenced_callables()
                    self.index_.register(callable)
                else:
                    # TODO(KNR): provide proper method to get the original callable
                    self.referenced_callables_.append(self.index_.callable_table_[callable.get_usr()])
