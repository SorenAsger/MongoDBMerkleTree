from bson import ObjectId

from node import Two3Node


class Cache:

    def __init__(self, dbi):
        self.dbi = dbi
        self.deleted = []
        self.added = []
        self.updated = []

    def add(self, node):
        if node.node_id is None:
            node.node_id = str(ObjectId())
        if node.node_id in self.deleted:
            self.deleted.remove(node.node_id)
        self.added[node.node_id] = node
        return node

    def add_using_key_and_children(self, key, children=None) -> 'Two3Node':
        node_to_insert = Two3Node(None, key)

        if children is None:
            node_to_insert.left_child_id = None
            node_to_insert.mid_child_id = None
            node_to_insert.right_child_id = None

        if len(children) == 3:
            node_to_insert.left_child_id = children[0]
            node_to_insert.mid_child_id = children[1]
            node_to_insert.right_child_id = children[2]
        else:
            node_to_insert.left_child_id = children[0]
            node_to_insert.right_child_id = children[1]

        return self.add(node_to_insert)

    def get(self, node_id):
        if node_id not in self.deleted:
            if node_id in self.updated:
                return self.updated[node_id]
            if node_id in self.added:
                return self.added[node_id]
            else:
                return self.dbi.get_23_node_by_id(node_id)

    def update(self, node):
        # If a node has been added to cache
        # and is then updated, then we can just
        # change the node that is to be added
        # to save an update.
        node_id = node.node_id
        if node_id in self.added:
            self.added[node_id] = node
        else:
            self.updated[node_id] = node

    def delete(self, node_id):
        self.deleted.append(node_id)

    def write_cache_to_db(self):
        self.dbi.create_many_23_nodes_from_node(list(self.added.values()))
        self.dbi.update_many_23_nodes(list(self.updated.values()))
        self.dbi.delete_many_23_nodes(self.deleted)

