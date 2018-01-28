class EntryView(object):
    '''View of the entry phase'''

    def __init__(self):
        super(EntryView, self).__init__()
        self.callables_ = []

    def load_callables(self, callables):
        self.callables_ = callables
