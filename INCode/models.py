from clang.cindex import CursorKind, Index, TranslationUnitLoadError


def _get_function_signature(cursor):
    return '{} {}'.format(cursor.result_type.spelling, cursor.displayname)


class File(object):
    '''Represents a file and provides a list of callables.'''

    def __init__(self, file, **kwargs):
        super(File, self).__init__()
        self.index_ = Index.create()
        try:
            self.tu_ = self.index_.parse(file, **kwargs)
        except TranslationUnitLoadError:
            raise ValueError('Cannot parse file {}'.format(file))

    def get_callables(self):
        filename = self.tu_.cursor.spelling
        for cursor in self.tu_.cursor.walk_preorder():
            if cursor.location.file is None or cursor.location.file.name != filename:
                pass
            elif cursor.kind == CursorKind.FUNCTION_DECL:
                yield Callable(_get_function_signature(cursor), cursor)


class Callable(object):
    '''Represents a Callable and provides a list of callables used by this callable.'''

    def __init__(self, name, cursor):
        super(Callable, self).__init__()
        self.name_ = name
        self.cursor_ = cursor

    # TODO(KNR): replace by read-only attribute
    def get_name(self):
        return self.name_

    def get_referenced_callables(self):
        for cursor in self.cursor_.walk_preorder():
            if cursor.kind == CursorKind.CALL_EXPR:
                definition = cursor.get_definition()
                yield Callable(_get_function_signature(definition), definition)  # TODO(KNR): pass self as parent
