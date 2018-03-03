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


class Index(object):
    def __init__(self):
        super(Index, self).__init__()
        self.index_ = cindex.Index.create()
        self.cursor_table_ = {}
        self.file_table_ = {}

    def load(self, file, **kwargs):
        if file in self.file_table_:
            return self.file_table_[file]
        f = File(file, self, **kwargs)
        self.file_table_[file] = f
        return f

    def load_definition(self, declaration_cursor, files, **kwargs):
        # TODO(KNR): method has too many responsibilities
        translation_units = gen_open(files)
        candidates = gen_search(declaration_cursor.displayname, translation_units)
        for candidate in candidates:
            self.load(candidate, **kwargs)
        return self.cursor_table_[declaration_cursor.get_usr()]

    def register(self, cursor):
        # don't replace with new cursor if the old one already is a definition
        if cursor.get_usr() in self.cursor_table_ and self.cursor_table_[cursor.get_usr()].is_definition():
            return
        self.cursor_table_[cursor.get_usr()] = cursor

    def lookup(self, usr):
        return self.cursor_table_[usr]

    def is_known(self, usr):
        return usr in self.cursor_table_

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
        self.index_.register(cursor)
        self._initialize_referenced_callables()

    # TODO(KNR): replace by read-only attribute
    def get_name(self):
        return self.name_

    def get_usr(self):
        return self.cursor_.get_usr()

    def get_referenced_callables(self):
        return self.referenced_callables_

    def _initialize_referenced_callables(self):
        self.referenced_callables_ = []
        for cursor in self.cursor_.walk_preorder():
            if cursor.kind == CursorKind.CALL_EXPR:
                # TODO(KNR): what's the point of `get_definition()` in list_references_of_func.py?
                definition = cursor.referenced
                self.referenced_callables_.append(Callable(_get_function_signature(definition), definition,
                                                           self.index_))
