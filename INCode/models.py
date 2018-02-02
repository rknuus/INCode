from clang.cindex import CursorKind, Index, TranslationUnitLoadError


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
        return self._get_function_definitions()

    def _get_function_definitions(self):
        filename = self.tu_.cursor.spelling
        for cursor in self.tu_.cursor.walk_preorder():
            if cursor.location.file is None or cursor.location.file.name != filename:
                pass
            elif cursor.kind == CursorKind.FUNCTION_DECL:
                yield Callable(self._get_function_signature(cursor), cursor)

    @staticmethod
    def _get_function_signature(cursor):
        return '{} {}'.format(cursor.result_type.spelling, cursor.displayname)


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
        return []
