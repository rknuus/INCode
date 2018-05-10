## Copyright (C) 2018 R. Knuus

from clang.cindex import CursorKind, Index, TranslationUnitLoadError
from INCode.views import EntryView


class EntryController(object):
    '''Controls the entry definition phase.'''

    def __init__(self):
        super(EntryController, self).__init__()
        self.index_ = Index.create()
        self.view_ = EntryView()

    def on_select_entry_file(self, entry_file, **kwargs):
        try:
            tu = self.index_.parse(entry_file, **kwargs)  # TODO(KNR): cache tu
            functions = self._get_function_definitions(tu)
            signatures = (self._get_function_signature(c) for c in functions)
            self.view_.load_callables(list(signatures))
        except TranslationUnitLoadError:
            raise ValueError('Cannot parse file {}'.format(entry_file))

    def _get_function_signature(self, cursor):
        return '{} {}'.format(cursor.result_type.spelling, cursor.displayname)

    def _get_function_definitions(self, tu):
        filename = tu.cursor.spelling
        for c in tu.cursor.walk_preorder():
            if c.location.file is None or c.location.file.name != filename:
                pass
            elif c.kind == CursorKind.FUNCTION_DECL:
                yield c
