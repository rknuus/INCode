from clang.cindex import CursorKind, TranslationUnitLoadError
from clang import cindex
import json
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


class Index(object):
    def __init__(self):
        super(Index, self).__init__()
        self.index_ = cindex.Index.create()
        self.callable_table_ = {}
        self.file_table_ = {}
        self.compilation_databases_ = {}

    def add_compilation_database(self, compilation_database):
        with open(compilation_database) as file:
            db = json.load(file)
            self.compilation_databases_[compilation_database] = db

    def get_files(self):
        return [translation_unit['file']
                for values in self.compilation_databases_.values() for translation_unit in values]

    def load(self, file, **kwargs):
        # TODO(KNR): assumes that the file name is unique
        if file in self.file_table_:
            return self.file_table_[file]
        # TODO(KNR): consider to lookup compilation command in compilation database
        f = File(file, self, **kwargs)
        self.file_table_[file] = f
        return f

    def load_definition(self, declaration_cursor, **kwargs):
        translation_units = gen_open(self.get_files())
        candidates = gen_search(declaration_cursor.get_name(), translation_units)
        for candidate in candidates:
            self.load(candidate, **kwargs)
        return self.callable_table_[declaration_cursor.get_usr()]

    def register(self, callable):
        # don't replace with new callable if the old one already is a definition
        if callable.get_usr() in self.callable_table_ and self.callable_table_[callable.get_usr()].is_definition():
            return
        self.callable_table_[callable.get_usr()] = callable

    def lookup(self, usr):
        return self.callable_table_[usr]

    def is_known(self, usr):
        return usr in self.callable_table_

    # TODO(KNR): replace by read-only attribute
    def get_clang_index(self):
        return self.index_


class File(object):
    '''Represents a file and provides a list of callables.'''

    def __init__(self, file, index, **kwargs):
        super(File, self).__init__()
        self.index_ = index
        try:
            self.tu_ = self.index_.get_clang_index().parse(file, **kwargs)
            self._initialize_callables()
        except TranslationUnitLoadError:
            raise ValueError('Cannot parse file {}'.format(file))

    def get_callables(self):
        return self.callables_

    def _initialize_callables(self):
        self.callables_ = []
        for cursor in self.tu_.cursor.walk_preorder():
            if cursor.location.file is not None and cursor.kind == CursorKind.FUNCTION_DECL:
                self.callables_.append(Callable(_get_function_signature(cursor), cursor, self.index_))


class Callable(object):
    '''Represents a Callable and provides a list of callables used by this callable.'''

    def __init__(self, name, cursor, index):
        super(Callable, self).__init__()
        self.name_ = name
        self.cursor_ = cursor
        self.index_ = index
        self._initialize_referenced_callables()
        self.index_.register(self)

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
                self.referenced_callables_.append(Callable(_get_function_signature(definition), definition,
                                                           self.index_))
