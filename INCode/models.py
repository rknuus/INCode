# Copyright (C) 2018 R. Knuus

from clang.cindex import CursorKind, TranslationUnitLoadError
from clang import cindex
import re


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

class Index(object):
    '''Represents the index of all callables and processes the compilation database.'''

    def __init__(self, compilation_databases):
        super(Index, self).__init__()
        self.index_ = cindex.Index.create()
        self.callable_table_ = {}
        self.file_table_ = {}
        self.compilation_databases_ = compilation_databases

    def load(self, file):
        # TODO(KNR): assumes that the file name is unique
        if file in self.file_table_:
            return self.file_table_[file]
        command = self.compilation_databases_.get_command(file)
        if not command:
            raise ValueError('No compilation command found for {}'.format(file))
        f = File(file, self, command)
        self.file_table_[file] = f
        return f

    def load_definition(self, declaration):
        translation_units = Index._gen_open(self.compilation_databases_.get_files())
        candidates = Index._gen_search(declaration.get_name(), translation_units)
        for candidate in candidates:
            self.load(candidate)
        if declaration.is_included():
            self.callable_table_[declaration.get_id()].include()
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
        return (cursor.get_usr() not in self.callable_table_ or cursor.is_definition())

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

    def __init__(self, file, index, command):
        super(File, self).__init__()
        self.index_ = index
        self.callable_usrs_ = []
        try:
            self.tu_ = self.index_.get_clang_index().parse(None, command)
            for cursor in self.tu_.cursor.walk_preorder():
                if cursor.location.file is not None and cursor.kind == CursorKind.FUNCTION_DECL:
                    if self.index_.is_interesting(cursor):
                        callable = Callable(_get_function_signature(cursor), cursor, self.index_)
                        if callable.get_id() not in self.callable_usrs_:
                            self.callable_usrs_.append(callable.get_id())
                        self.index_.register(callable)
        except TranslationUnitLoadError:
            raise ValueError('Cannot parse file {}'.format(file))

    def get_callables(self):
        return [self.index_.lookup(usr) for usr in self.callable_usrs_]


class Callable(object):
    '''Represents a callable and provides a list of referenced callables.'''

    def __init__(self, name, cursor, index, initialize=True):
        super(Callable, self).__init__()
        self.name_ = name
        self.cursor_ = cursor
        self.index_ = index
        self.included_ = False
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

    def include(self):
        self.included_ = True

    def exclude(self):
        self.included_ = False

    def is_included(self):
        return self.included_

    def export(self):
        sender = self.get_translation_unit() if self.is_included() else ''
        return '@startuml\n\n{}\n@enduml'.format(self.export_relations_(sender))

    def export_relations_(self, parent_sender):
        diagram = ''
        for usr in self.referenced_usrs_:
            callable = self.index_.lookup(usr)
            sender = self.get_translation_unit() if self.is_included() else parent_sender
            if callable.is_included():
                diagram += '{} -> {}: {}\n'.format(sender, callable.get_translation_unit(), callable.get_name())
            diagram += callable.export_relations_(sender)
        return diagram

    def is_definition(self):
        return self.cursor_.is_definition()

    def get_referenced_callables(self):
        return [self.index_.lookup(usr) for usr in self.referenced_usrs_]

    def initialize(self):
        for cursor in self.cursor_.walk_preorder():
            if cursor.kind == CursorKind.CALL_EXPR:
                if self.index_.is_interesting(cursor):
                    definition = cursor.referenced
                    callable = Callable(_get_function_signature(definition), definition, self.index_, False)
                    if callable.get_id() not in self.referenced_usrs_:
                        self.referenced_usrs_.append(callable.get_id())
                    self.index_.register(callable)
