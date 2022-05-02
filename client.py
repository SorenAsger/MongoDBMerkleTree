from crypto_util import HashFunction
from verifier import Verifier

class Client:

    def __init__(self, server):
        self.server = server
        self.server.destroy_db()
        self.hash_function = HashFunction()
        self.verifier = Verifier(server)

    def split_node(self, node, value, left_children=None, right_children=None):
        values = [node.left, node.right, value]
        values.sort()
        min_node = ClientNode([values[0], None])
        if left_children is not None:
            min_node.left_hash = left_children[0]
            min_node.right_hash = left_children[1]
        max_node = ClientNode([values[2], None])
        if right_children is not None:
            max_node.left_hash = right_children[0]
            max_node.right_hash = right_children[1]
        min_node.update_hash()
        max_node.update_hash()
        return min_node.hash, max_node.hash, values[1]

    def insert(self, value):
        self.verifier.verify_non_membership(value)
        insert_node, insert_path, hashes = self.server.get_insert_path(value)
        new_path = []
        for i in range(0, len(insert_path)):
            node = insert_path[i]
            new_node = ClientNode([node.left, node.right])
            if i == 0:
                new_node.parent = None
            else:
                new_node.parent = new_path[i - 1]

            if len(insert_path) > 0 and i < len(insert_path) - 1:
                last = insert_path[i + 1].hash
            else:
                last = -1

            child_hashes = hashes[i]
            if last == child_hashes[0]:
                child_hashes = [None, child_hashes[1], child_hashes[2]]
            elif last == child_hashes[1]:
                child_hashes = [child_hashes[0], None, child_hashes[2]]
            elif last == child_hashes[2]:
                child_hashes = [child_hashes[0], child_hashes[1], None]
            else:
                child_hashes = [child_hashes[0], child_hashes[1], child_hashes[2]]

            new_node.set_hashes(child_hashes)
            new_node.hash = node.hash
            new_path.append(new_node)
        if not new_path:
            self.hash_function.update(value)
            root_hash = self.hash_function.digest()
            self.server.insert(value)
        else:
            self.verifier.verify_membership(insert_node.left)
            root_hash = self.insert_at(new_path[-1], value)
            self.server.insert(value)
        server_hash = self.server.get_root_hash()
        if root_hash == server_hash:
            return True
        else:
            return False

    def update_hashes_upwards(self, node):
        last_hash = node.update_hash()
        current = node.parent
        while current is not None:
            last_hash = current.update_hash(last_hash)
            current = current.parent
        return last_hash

    def insert_at(self, insertion_node, value):
        parent = insertion_node.parent
        if insertion_node.is_2_node():
            return self.insert_2_node(value, insertion_node)
        elif parent is None:
            return self.insert_3_node_root(value, insertion_node)
        elif parent.is_2_node():
            return self.insert_3_node_2_parent(value, insertion_node, parent)
        else:
            return self.insert_3_node_3_parent(value, insertion_node, parent)

    def insert_3_node_root(self, value, insert_location):
        min_node, max_node, mid = self.split_node(insert_location, value)
        node = ClientNode([mid, None])
        node.left_hash = min_node
        node.right_hash = max_node
        return node.update_hash()

    def insert_3_node_3_parent(self, value, insert_location, parent):
        min_node, max_node, mid = self.split_node(insert_location, value)
        if parent.left_hash is None:
            all_children_id = [min_node, max_node, parent.mid_hash, parent.right_hash]
        elif parent.mid_hash is None:
            all_children_id = [parent.left_hash, min_node, max_node, parent.right_hash]
        else:
            all_children_id = [parent.left_hash, parent.mid_hash, min_node, max_node]
        values = sorted([parent.left, parent.right, mid])
        root_hash = self.insert_3_node_help(parent, all_children_id, values)
        return root_hash

    def insert_3_node_help(self, node, children_hashes, values):
        # Children ids are sorted
        parent = node.parent
        min_node = ClientNode([values[0], None])
        min_node.left_hash = children_hashes[0]
        min_node.right_hash = children_hashes[1]
        min_node.update_hash()
        max_node = ClientNode([values[2], None])
        max_node.left_hash = children_hashes[2]
        max_node.right_hash = children_hashes[3]
        max_node.update_hash()

        if parent is None:
            # Handle case for root
            node.left_hash = min_node.hash
            node.right_hash = max_node.hash
            node.left = values[1]
            node.right = None
            node.mid_hash = None
            root_hash = self.update_hashes_upwards(node)
            return root_hash
            # ROOT CASE SHOULD WORK
        elif parent.is_2_node():
            if parent.left_hash is None:
                parent.left_hash = min_node.hash
                parent.mid_hash = max_node.hash
            else:
                parent.mid_hash = min_node.hash
                parent.right_hash = max_node.hash
            if values[1] > parent.left:
                parent.right = values[1]
            else:
                parent.right = parent.left
                parent.left = values[1]
            return self.update_hashes_upwards(node)

        else:
            # Parent is 3 node as well
            # Need to create a new temp 4 node
            new_values = sorted([parent.left, parent.right, values[1]])
            if parent.left_hash is None:
                new_children_hashes = [min_node.hash, max_node.hash, parent.mid_hash, parent.right_hash]
            elif parent.mid_hash is None:
                new_children_hashes = [parent.left_hash, min_node.hash, max_node.hash, parent.right_hash]
            else:
                new_children_hashes = [parent.left_hash, parent.mid_hash, min_node.hash, max_node.hash]
            return self.insert_3_node_help(parent, new_children_hashes, new_values)

    def insert_3_node_2_parent(self, value, insert_location, parent):
        # Create 2 new nodes for min and max
        min_node, max_node, mid = self.split_node(insert_location, value)

        if parent.left_hash is None:
            parent.left_hash = min_node
            parent.mid_hash = max_node
        else:
            parent.mid_hash = min_node
            parent.right_hash = max_node

        if mid > parent.left:
            parent.right = mid
        else:
            parent.right = parent.left
            parent.left = mid

        return self.update_hashes_upwards(parent)

    def insert_2_node(self, value, insert_location):
        # Insert value into node in sorted order
        if value > insert_location.left:
            insert_location.right = value
        else:
            insert_location.right = insert_location.left
            insert_location.left = value
        root_hash = self.update_hashes_upwards(insert_location)
        return root_hash

    def delete(self, value):
        if not self.verifier.verify_membership(value):
            print("no such value")
            return
        deletion_node, delete_path, hashes, siblings, sibling_hashes = self.server.get_delete_path(value)

        new_path = []
        not_leaf = False
        for i in range(0, len(delete_path)):
            node = delete_path[i]
            values = [node.left, node.right]
            if value in values and i < len(delete_path) - 1:
                not_leaf = True
                if node.left == value:
                    values = [delete_path[-1].left, node.right]
                else:
                    values = [node.left, delete_path[-1].left]

            new_node = ClientNode(values)
            if i == 0:
                new_node.parent = None
            else:
                sibling = siblings[i - 1]
                sibling_node = ClientNode([sibling.left, sibling.right])
                sibling_node.set_hashes(sibling_hashes[i - 1])
                sibling_node.update_hash()

                new_node.sibling = sibling_node
                new_node.parent = new_path[i - 1]
            if len(delete_path) > 0 and i < len(delete_path) - 1:
                last = delete_path[i + 1].hash
            else:
                if not_leaf:
                    new_node.left = value
                last = -1

            child_hashes = hashes[i]
            if last == child_hashes[0]:
                child_hashes = [None, child_hashes[1], child_hashes[2]]
            elif last == child_hashes[1]:
                child_hashes = [child_hashes[0], None, child_hashes[2]]
            elif last == child_hashes[2]:
                child_hashes = [child_hashes[0], child_hashes[1], None]
            else:
                child_hashes = [child_hashes[0], child_hashes[1], child_hashes[2]]

            new_node.set_hashes(child_hashes)
            new_node.hash = node.hash
            new_path.append(new_node)

        last_elem = len(new_path) == 1 and \
                    new_path[0].right is None

        if last_elem:
            root_hash = None
            self.server.delete(value)
            server_hash = self.server.get_root_hash()
            return root_hash == server_hash
        else:
            root_hash = self.delete_at(value, new_path[-1])
            self.server.delete(value)
            server_hash = self.server.get_root_hash()
            return root_hash == server_hash

    def delete_at(self, value, node):
        if value in [node.left, node.right]:
            if node.right is not None:
                root_hash = self.delete_3_node_no_children(value, node)
                return root_hash
            else:
                root_hash = self.delete_hole(node)
                return root_hash

    def delete_hole(self, node):
        if node.hash is not None:
            node.hash = None
            hole = node
        else:
            hole = node

        parent = hole.parent
        if parent is None:
            return hole.left_hash

        sibling = hole.sibling
        if parent.is_2_node() and sibling.is_2_node():
            return self.delete_2_node_sib_2_node_parent(hole, sibling, parent)
        elif parent.is_2_node() and sibling.is_2_node() is False:
            return self.delete_3_node_sib_2_node_parent(hole, sibling, parent)
        elif parent.is_2_node() is False and sibling.is_2_node():
            return self.delete_2_node_sib_3_node_parent(hole, sibling, parent)
        elif parent.is_2_node() is False and sibling.is_2_node() is False:
            return self.delete_3_node_sib_3_node_parent(hole, sibling, parent)

    def delete_root(self, node):
        values = [node.left, node.right]
        node.set_values_and_hashes(values, [None, None, None])
        node.update_hash()
        return node.hash

    def delete_3_node_no_children(self, value, node):
        delete_left = node.left == value
        if delete_left:
            node.left = node.right
            node.right = None
        else:
            node.right = None
        node.update_hash()
        return self.update_hashes_upwards(node)

    def delete_2_node_sib_2_node_parent(self, hole, sibling, parent):
        if sibling.left < parent.left:
            values = [sibling.left, parent.left]
            hashes = [sibling.left_hash, sibling.right_hash, hole.left_hash]
            sibling.set_values_and_hashes(values, hashes)

            sibling.hash = None
            hole_node = sibling
        else:
            values = [parent.left, sibling.left]
            hashes = [hole.left_hash, sibling.left_hash, sibling.right_hash]
            sibling.set_values_and_hashes(values, hashes)

            sibling.hash = None
            hole_node = sibling

        hole_node.parent = parent.parent
        hole_node.update_hash()
        hole_node.left_hash = hole_node.hash
        hole_node.sibling = parent.sibling
        return self.delete_hole(hole_node)

    def delete_3_node_sib_2_node_parent(self, hole, sibling, parent):
        if sibling.left < parent.left:
            # left
            lvalues = [sibling.left, None]
            lhashes = [sibling.left_hash, None, sibling.mid_hash]
            # parent
            pvalues = [sibling.right, None]
            # right
            rvalues = [parent.left, None]
            rhashes = [sibling.right_hash, None, hole.left_hash]

            sibling.set_values_and_hashes(lvalues, lhashes)
            hole.set_values_and_hashes(rvalues, rhashes)
            hole.update_hash()
            sibling.update_hash()

            phashes = [sibling.hash, None, hole.hash]
            parent.set_values_and_hashes(pvalues, phashes)
        else:
            # left
            lvalues = [parent.left, None]
            lhashes = [hole.left_hash, None, sibling.left_hash]
            # parent
            pvalues = [sibling.left, None]
            # right
            rvalues = [sibling.right, None]
            rhashes = [sibling.mid_hash, None, sibling.right_hash]

            hole.set_values_and_hashes(lvalues, lhashes)
            sibling.set_values_and_hashes(rvalues, rhashes)
            hole.update_hash()
            sibling.update_hash()

            phashes = [hole.hash, None, sibling.hash]
            parent.set_values_and_hashes(pvalues, phashes)
        sibling.parent = parent
        return self.update_hashes_upwards(sibling)

    def delete_2_node_sib_3_node_parent(self, hole, sibling, parent):
        if parent.left_hash is None or sibling.left < parent.left:
            # left
            if sibling.left < parent.left:
                lvalues = [sibling.left, parent.left]
                lhashes = [sibling.left_hash, sibling.right_hash, hole.left_hash]
                sibling.set_values_and_hashes(lvalues, lhashes)
                sibling.update_hash()
                phashes = [sibling.hash, None, parent.right_hash]
            else:
                lvalues = [parent.left, sibling.left]
                lhashes = [hole.left_hash, sibling.left_hash, sibling.right_hash]
                sibling.set_values_and_hashes(lvalues, lhashes)
                sibling.update_hash()
                phashes = [sibling.hash, None, parent.right_hash]
            # parent
            pvalues = [parent.right, None]

            parent.set_values_and_hashes(pvalues, phashes)
            sibling.parent = parent
            return self.update_hashes_upwards(sibling)
        else:
            # right
            if sibling.left < parent.right:
                rvalues = [sibling.left, parent.right]
                rhashes = [sibling.left_hash, sibling.right_hash, hole.left_hash]
                hole.set_values_and_hashes(rvalues, rhashes)
                hole.update_hash()
                phashes = [parent.left_hash, None, hole.hash]
            else:
                rvalues = [parent.right, sibling.left]
                rhashes = [hole.left_hash, sibling.left_hash, sibling.right_hash]
                hole.set_values_and_hashes(rvalues, rhashes)
                hole.update_hash()
                phashes = [parent.left_hash, None, hole.hash]

            # parent
            pvalues = [parent.left, None]

            parent.set_values_and_hashes(pvalues, phashes)
            return self.update_hashes_upwards(hole)

    def delete_3_node_sib_3_node_parent(self, hole, sibling, parent):
        if parent.left_hash is None or sibling.left < parent.left:
            if sibling.left < parent.left:
                # left
                lvalues = [sibling.left, None]
                lhashes = [sibling.left_hash, None, sibling.mid_hash]

                # right
                rvalues = [parent.left, None]
                rhashes = [sibling.right_hash, None, hole.left_hash]

                pvalues = [sibling.right, parent.right]

                sibling.set_values_and_hashes(lvalues, lhashes)
                hole.set_values_and_hashes(rvalues, rhashes)
                sibling.update_hash()
                hole.update_hash()
                phashes = [sibling.hash, hole.hash, parent.right_hash]
            else:
                # left
                lvalues = [parent.left, None]
                lhashes = [hole.left_hash, None, sibling.left_hash]

                # right
                rvalues = [sibling.right, None]
                rhashes = [sibling.mid_hash, None, sibling.right_hash]

                pvalues = [sibling.left, parent.right]

                hole.set_values_and_hashes(lvalues, lhashes)
                sibling.set_values_and_hashes(rvalues, rhashes)
                sibling.update_hash()
                hole.update_hash()
                phashes = [hole.hash, sibling.hash, parent.right_hash]

            # parent
            parent.set_values_and_hashes(pvalues, phashes)
            sibling.parent = parent
            return self.update_hashes_upwards(sibling)

        else:
            if sibling.left < parent.right:
                # left
                lvalues = [sibling.left, None]
                lhashes = [sibling.left_hash, None, sibling.mid_hash]

                # right
                rvalues = [parent.right, None]
                rhashes = [sibling.right_hash, None, hole.left_hash]

                pvalues = [parent.left, sibling.right]

                sibling.set_values_and_hashes(lvalues, lhashes)
                hole.set_values_and_hashes(rvalues, rhashes)
                sibling.update_hash()
                hole.update_hash()
                phashes = [parent.left_hash, sibling.hash, hole.hash]
            else:
                # left
                lvalues = [parent.right, None]
                lhashes = [hole.left_hash, None, sibling.left_hash]

                # right
                rvalues = [sibling.right, None]
                rhashes = [sibling.mid_hash, None, sibling.right_hash]

                pvalues = [parent.left, sibling.left]

                hole.set_values_and_hashes(lvalues, lhashes)
                sibling.set_values_and_hashes(rvalues, rhashes)
                sibling.update_hash()
                hole.update_hash()
                phashes = [parent.left_hash, hole.hash, sibling.hash]

            # parent
            parent.set_values_and_hashes(pvalues, phashes)
            sibling.parent = parent
            return self.update_hashes_upwards(sibling)


class ClientNode:

    def __init__(self, values):
        self.parent = None
        self.sibling = None
        self.left = values[0]
        self.right = values[1]
        self.hash_function = HashFunction()
        self.hash = None
        self.left_hash = None
        self.mid_hash = None
        self.right_hash = None

    def is_2_node(self):
        return self.right is None

    def update_hash(self, last_hash=None):
        self.hash_function.update(self.left)
        self.hash_function.update(self.right)
        if self.left_hash is None:
            hashes = [last_hash, self.mid_hash, self.right_hash]
        elif self.mid_hash is None and not self.is_2_node():
            hashes = [self.left_hash, last_hash, self.right_hash]
        elif self.right_hash is None:
            hashes = [self.left_hash, self.mid_hash, last_hash]
        else:
            hashes = [self.left_hash, self.mid_hash, self.right_hash]
        self.hash_function.update(hashes[0])
        self.hash_function.update(hashes[1])
        self.hash_function.update(hashes[2])
        self.hash = self.hash_function.digest()
        return self.hash

    def set_values_and_hashes(self, values, hashes=None):
        if hashes is not None:
            self.set_hashes(hashes)
        self.left = values[0]
        self.right = values[1]

    def set_hashes(self, hashes):
        self.left_hash = hashes[0]
        self.mid_hash = hashes[1]
        self.right_hash = hashes[2]

    def is_2_node(self):
        return self.right == None

    def __str__(self):
        return f" Children hashes {self.left_hash}, {self.mid_hash}, {self.right_hash}, " \
               f"Values {self.left}, {self.right}"


