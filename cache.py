

class Cache:

    def __init__(self, dbi):
        self.dbi = dbi
        self.deleted = {}
        self.added = {}
        self.updated = {}

    def add(self, node_id, node):
        self.added[node_id] = node

    def get(self, node_id):
        if node_id not in self.deleted:
            if node_id in self.updated:
                return self.added[node_id]
            if node_id in self.added:
                return self.added[node_id]

    def update(self, node_id, node):
        # If a node has been added to cache
        # and is then updated, then we can just
        # change the node that is to be added
        # to save an update.
        if node_id in self.added:
            self.added[node_id] = node
        else:
            self.updated[node_id] = node

    def delete(self, node_id, node):
        self.added[node_id] = node

    def write_cache_to_db(self):
        self.dbi.create_many_23_nodes_from_node(list(self.added.values()))
        self.dbi.update_many_23_nodes(list(self.updated.values()))
        self.dbi.delete_many_23_nodes(list(self.deleted.keys()))

