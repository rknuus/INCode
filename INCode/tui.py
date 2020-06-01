# Copyright (C) 2020 R. Knuus

from anytree import Node, RenderTree
from anytree.search import find
from INCode.call_tree_manager import CallTreeManager
from pubsub import pub


class TuiViewModel(object):
    '''Maintains a view model based on pub/sub updated from actual data model.'''
    def __init__(self, manager):
        super(TuiViewModel, self).__init__()
        self.manager_ = manager  # TODO(KNR): probably required to fetch child nodes
        self.root_ = None
        pub.subscribe(self.update_node_data, 'update_node_data')

    def set_root(self, root):
        self.root_ = Node(root.name, data=root)
        self.build_tree_(self.root_)

    @property
    def view(self):
        tree = ''
        for pre, _, node in RenderTree(self.root_):
            tree += ('%s%s\n' % (pre, node.name))
        return tree

    def build_tree_(self, parent):
        for old_child in parent.children:
            old_child.parent = None
        for call in self.manager_.get_calls_of(parent.name):
            child = Node(call.name, parent=parent)
            self.build_tree_(child)

    def update_node_data(self, new_data):
        node = find(self.root_, lambda node: node.name == new_data.name)
        assert node
        node.data = new_data
        self.build_tree_(node)
