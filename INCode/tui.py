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
        self.included_ = set()
        pub.subscribe(self.update_node_data, 'update_node_data')
        pub.subscribe(self.node_included, 'node_included')
        pub.subscribe(self.node_excluded, 'node_excluded')

    def set_root(self, root):
        self.root_ = Node(root.name, data=root)
        self.build_tree_(self.root_)

    @property
    def view(self):
        tree = ''
        for pre, _, node in RenderTree(self.root_):
            state = 'y' if node.name in self.included_ else ' '
            tree += ('%s  %s%s\n' % (state, pre, node.name))
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

    def node_included(self, node_name):
        self.included_.add(node_name)

    def node_excluded(self, node_name):
        self.included_.remove(node_name)
