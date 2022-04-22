from bson import ObjectId

from node import Two3Node


class Cache:

    def __init__(self, dbi):
        self.dbi = dbi
        self._deleted = set()
        self._added = {}
        self._updated = {}

    def add(self, node):
        if node.node_id is None:
            node.node_id = str(ObjectId())
        if node.node_id in self._deleted:
            self._deleted.remove(node.node_id)
        self._added[node.node_id] = node
        return node

    def add_using_key_and_children(self, key, children=None) -> 'Two3Node':
        node_to_insert = Two3Node(None, key)

        if children is None:
            children = [None, None, None]

        if len(children) == 3:
            node_to_insert.left_child_id = children[0]
            node_to_insert.mid_child_id = children[1]
            node_to_insert.right_child_id = children[2]
        else:
            node_to_insert.left_child_id = children[0]
            node_to_insert.right_child_id = children[1]

        return self.add(node_to_insert)

    def get(self, node_id):
        if node_id not in self._deleted:
            if node_id in self._updated:
                return self._updated[node_id]
            if node_id in self._added:
                return self._added[node_id]
            else:
                return self.dbi.get_23_node_by_id(node_id)

    def update(self, node):
        # If a node has been added to cache
        # and is then updated, then we can just
        # change the node that is to be added
        # to save an update.
        node_id = node.node_id
        if node_id in self._added:
            self._added[node_id] = node
        else:
            self._updated[node_id] = node

    def delete(self, node_id):
        self._deleted.add(node_id)

    def reset(self):
        self._deleted = set()
        self._added = {}
        self._updated = {}

    def write_cache_to_db(self):
        self.dbi.delete_many_23_nodes(list(self._deleted))
        self.dbi.create_many_23_nodes_from_node(list(self._added.values()))
        self.dbi.update_many_23_nodes(list(self._updated.values()))
        self.reset()