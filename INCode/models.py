from clang.cindex import CursorKind, TranslationUnitLoadError
from clang import cindex


def _get_function_signature(cursor):
    return '{} {}'.format(cursor.result_type.spelling, cursor.displayname)


class Index(object):
    def __init__(self):
        super(Index, self).__init__()
        self.index_ = cindex.Index.create()
        self.table_ = {}

    def load(self, file, **kwargs):
        return File(file, self, **kwargs)

    def register(self, cursor):
        # don't replace with new cursor if the old one already is a definition
        if cursor.get_usr() in self.table_ and self.table_[cursor.get_usr()].is_definition():
            return
        self.table_[cursor.get_usr()] = cursor

    def lookup(self, usr):
        return self.table_[usr]

    def is_known(self, usr):
        return usr in self.table_

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
        except TranslationUnitLoadError:
            raise ValueError('Cannot parse file {}'.format(file))

    def get_callables(self):
        for cursor in self.tu_.cursor.walk_preorder():
            if cursor.location.file is not None and cursor.kind == CursorKind.FUNCTION_DECL:
                yield Callable(_get_function_signature(cursor), cursor, self.index_)


class Callable(object):
    '''Represents a Callable and provides a list of callables used by this callable.'''

    def __init__(self, name, cursor, index):
        super(Callable, self).__init__()
        self.name_ = name
        self.cursor_ = cursor
        self.index_ = index
        self.index_.register(cursor)

    # TODO(KNR): replace by read-only attribute
    def get_name(self):
        return self.name_

    def get_usr(self):
        return self.cursor_.get_usr()

    def get_referenced_callables(self):
        for cursor in self.cursor_.walk_preorder():
            if cursor.kind == CursorKind.CALL_EXPR:
                # TODO(KNR): what's the point of `get_definition()` in list_references_of_func.py?
                definition = cursor.referenced
                # TODO(KNR): pass self as parent
                yield Callable(_get_function_signature(definition), definition, self.index_)
