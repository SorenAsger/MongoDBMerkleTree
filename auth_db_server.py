from node import Two3Node


class AuthDBServer:

    def __init__(self, dbi):
        print("Server started.")
        self.root_id = None
        self.dbi = dbi

    def split_node(self, node, value, left_children=None, right_children=None):
        values = [node.left, node.right, value]
        values.sort()
        min_node = self.dbi.create_23_node(values[0], left_children)
        max_node = self.dbi.create_23_node(values[2], right_children)
        min_node.update_hash(self.dbi)
        max_node.update_hash(self.dbi)
        return min_node, max_node, values[1]

    def find_nearest_node_and_parent(self, value):
        current = self.dbi.get_23_node_by_id(self.root_id)
        parent = None
        nearest_node = None
        depth = 0
        path = []
        while current is not None:
            current.parent = nearest_node
            path.append(current)
            depth += 1
            # If the value is in the current node
            if value in current.get_values():
                return current, nearest_node, path
            # 2-node
            if current.is_2_node():
                if value < current.left:
                    child_id = current.left_child_id
                else:
                    child_id = current.right_child_id
            # 3-node
            else:
                if value < current.left:
                    child_id = current.left_child_id
                elif value > current.right:
                    child_id = current.right_child_id
                else:
                    child_id = current.mid_child_id

            parent = nearest_node
            nearest_node = current
            current = self.dbi.get_23_node_by_id(child_id)


        return nearest_node, parent, path

    def build_proof(self, current):
        # The order of a proof is:
        # 1. left
        # 2. right
        # 3. left child
        # 4. Mid child
        # 5. Right child
        proof = []

        # For each node upwards append the
        # values and child hashes to the proof,
        # but omit the calling child's hash.
        # The calling child's hash is not necessary
        # since that is the one the verifier calculates
        prev_node_id = - 1
        while current is not None:
            proof.append(current.get_proof_values_and_hashes(self.dbi, prev_node_id))
            prev_node_id = current.node_id
            current = current.parent
        return proof

    def get_membership_proof(self, value):
        current, parent, path = self.find_nearest_node_and_parent(value)
        if value not in current.get_values():
            return None
        return self.build_proof(current)

    def get_non_membership_proof(self, value):
        current, parent, path = self.find_nearest_node_and_parent(value)
        if value in current.get_values():
            return None
        return self.build_proof(current)

    def contains(self, value):
        nearest_node, _, _ = self.find_nearest_node_and_parent(value)
        if nearest_node is None:
            return False
        return value in nearest_node.get_values()

    def insert(self, value):
        if self.root_id is None:
            self.root_id = "root"
            root_node = Two3Node(self.root_id, value)
            root_node.update_hash(self.dbi)
            self.dbi.create_23_node_from_node(root_node)
            root_node.update_hash(self.dbi)
            return

        insertion_node, parent, _ = self.find_nearest_node_and_parent(value)
        insertion_node.parent = parent
        self.insert_at(insertion_node, value)

    def update_hashes_upwards(self, starting_node: 'Two3Node'):
        current = starting_node
        updated_nodes = []
        while current is not None:
            updated_nodes.append(current.update_hash(self.dbi))
            current = current.parent
        #self.dbi.update_many_23_nodes(updated_nodes)

    def insert_at(self, insertion_node: 'Two3Node', value):
        parent = insertion_node.parent
        if insertion_node is not None and value in [insertion_node.left, insertion_node.right]:
            print("value " + str(value) + " is already in the tree.")
        elif insertion_node.is_2_node():
            self.insert_2_node(value, insertion_node)
        elif parent is None:
            self.insert_3_node_root(value, insertion_node)
        elif parent.is_2_node():
            self.insert_3_node_2_parent(value, insertion_node, parent)
        else:
            self.insert_3_node_3_parent(value, insertion_node, parent)

    def insert_3_node_root(self, value, insert_location: 'Two3Node'):
        # TODO Split here
        min_node, max_node, mid = self.split_node(insert_location, value)
        insert_location.left_child_id = min_node.node_id
        insert_location.right_child_id = max_node.node_id
        insert_location.left = mid
        insert_location.right = None

        # TODO: Update parent in database and delete insert_location from database
        # TODO: Could maybe be more efficient to not delete insert_location and reuse it instead?
        # TODO: Update upwards and hash thing
        self.dbi.update_23_node(insert_location)
        insert_location.update_hash(self.dbi)

    def insert_3_node_3_parent(self, value, insert_location: 'Two3Node', parent: 'Two3Node'):
        min_node, max_node, mid = self.split_node(insert_location, value)
        if insert_location.node_id == parent.left_child_id:
            all_children_id = [min_node.node_id, max_node.node_id, parent.mid_child_id, parent.right_child_id]
        elif insert_location.node_id == parent.mid_child_id:
            all_children_id = [parent.left_child_id, min_node.node_id, max_node.node_id, parent.right_child_id]
        else:
            all_children_id = [parent.left_child_id, parent.mid_child_id, min_node.node_id, max_node.node_id]
        values = sorted([parent.left, parent.right, mid])
        self.insert_3_node_help(parent, all_children_id, values)
        self.dbi.update_23_node(parent)
        self.dbi.remove_23_node(insert_location.node_id)
        # TODO: Update parent in database and delete insert_location from database
        # TODO: Could maybe be more efficient to not delete insert_location and reuse it instead?
        # TODO: Update upwards and hash thing

    def insert_3_node_help(self, node: "Two3Node", children_ids, values):
        # Children ids are sorted
        parent = node.parent
        min_node = self.dbi.create_23_node(values[0], children_ids[:2])
        min_node.update_hash(self.dbi)
        max_node = self.dbi.create_23_node(values[2], children_ids[2:])
        max_node.update_hash(self.dbi)

        if parent is None:
            # Handle case for root
            node.left_child_id = min_node.node_id
            node.right_child_id = max_node.node_id
            node.left = values[1]
            node.right = None
            node.mid_child_id = None
            self.dbi.update_23_node(node)
            self.update_hashes_upwards(node)
            # ROOT CASE SHOULD WORK
        elif parent.is_2_node():
            if node.node_id == parent.left_child_id:
                parent.left_child_id = min_node.node_id
                parent.mid_child_id = max_node.node_id
            else:
                parent.mid_child_id = min_node.node_id
                parent.right_child_id = max_node.node_id
            if values[1] > parent.left:
                parent.right = values[1]
            else:
                parent.right = parent.left
                parent.left = values[1]
            self.dbi.update_23_node(parent)
            self.dbi.remove_23_node(node.node_id)
            self.update_hashes_upwards(parent)

        else:
            # Parent is 3 node as well
            # Need to create a new temp 4 node
            new_values = sorted([parent.left, parent.right, values[1]])
            if node.node_id == parent.left_child_id:
                new_children_id = [min_node.node_id, max_node.node_id, parent.mid_child_id, parent.right_child_id]
            elif node.node_id == parent.mid_child_id:
                new_children_id = [parent.left_child_id, min_node.node_id, max_node.node_id, parent.right_child_id]
            else:
                new_children_id = [parent.left_child_id, parent.mid_child_id, min_node.node_id, max_node.node_id]
            self.insert_3_node_help(parent, new_children_id, new_values)
            self.dbi.remove_23_node(node.node_id)

    def insert_3_node_2_parent(self, value, insert_location: 'Two3Node', parent: 'Two3Node'):
        # Create 2 new nodes for min and max
        min_node, max_node, mid = self.split_node(insert_location, value)

        if insert_location.node_id == parent.left_child_id:
            parent.left_child_id = min_node.node_id
            parent.mid_child_id = max_node.node_id
        else:
            parent.mid_child_id = min_node.node_id
            parent.right_child_id = max_node.node_id

        if mid > parent.left:
            parent.right = mid
        else:
            parent.right = parent.left
            parent.left = mid
        # TODO: Update parent in database and delete insert_location from database
        # TODO: Could maybe be more efficient to not delete insert_location and reuse it instead?
        # TODO: Update upwards and hash thing
        self.dbi.update_23_node(parent)
        self.dbi.remove_23_node(insert_location.node_id)
        self.update_hashes_upwards(parent)

    def insert_2_node(self, value, insert_location):
        # Insert value into node in sorted order
        if value > insert_location.left:
            insert_location.right = value
        else:
            insert_location.right = insert_location.left
            insert_location.left = value
        # push update to DB
        self.dbi.update_23_node(insert_location)
        self.update_hashes_upwards(insert_location)

    def delete(self, value):
        if self.root_id is None:
            print("Tree is empty")
            return
        nearest_node, parent, _ = self.find_nearest_node_and_parent(value)
        contains_val = value in [nearest_node.left, nearest_node.right]
        last_elem = nearest_node.node_id == self.root_id and \
                    nearest_node.is_2_node() and \
                    contains_val and \
                    nearest_node.left_child_id is None
        if last_elem:
            self.dbi.remove_23_node(nearest_node.node_id)
            self.root_id = None
        elif nearest_node is not None and contains_val:
            self.delete_at(value, nearest_node)
        else:
            print("Value", value, "not in tree")

    def delete_at(self, value, node):
        if node.is_leaf():
            if node.is_2_node() is False:
                self.delete_3_node_no_children(value, node)
                return
            else:
                self.delete_hole(node)
                return
        inorder_succ = self.find_succ(node, value)
        if node.is_2_node():
            node.update_23_node_value_children(self.dbi, [inorder_succ.left, None])
        else:
            if node.right == value:
                node.update_23_node_value_children(self.dbi, [inorder_succ.left, node.left])
            else:
                node.update_23_node_value_children(self.dbi, [inorder_succ.left, node.right])

        if node.node_id == inorder_succ.parent.node_id:
            inorder_succ.parent = node
        self.delete_hole(inorder_succ)

    def find_succ(self, node, value):
        if node.is_2_node() or node.right == value:
            current = self.dbi.get_23_node_by_id(node.right_child_id)
        else:
            current = self.dbi.get_23_node_by_id(node.mid_child_id)
        succ = current
        current.parent = node
        while current is not None:
            parent = current
            current = self.dbi.get_23_node_by_id(current.left_child_id)
            if current is not None:
                succ = current
                succ.parent = parent
        return succ

    def delete_hole(self, node):
        if node.is_2_node() is False:
            self.delete_3_node_no_children(node.left, node)
            return
        if node.is_hole_node() is False:
            hole = self.dbi.make_hole_node(node)
        else:
            hole = node

        parent = hole.parent
        if parent is None:
            self.delete_root(hole)
            return

        sibling = self.dbi.get_23_node_by_id(parent.get_sibling(hole))
        sibling.parent = parent
        if parent.is_2_node() and sibling.is_2_node():
            self.delete_2_node_sib_2_node_parent(hole, sibling, parent)
            if node.is_hole_node() is False:
                leaf = self.dbi.get_23_node_by_id(sibling.node_id)
                self.update_hashes_upwards(leaf)
        elif parent.is_2_node() and sibling.is_2_node() is False:
            self.delete_3_node_sib_2_node_parent(hole, sibling, parent)
        elif parent.is_2_node() is False and sibling.is_2_node():
            self.delete_2_node_sib_3_node_parent(hole, sibling, parent)
        elif parent.is_2_node() is False and sibling.is_2_node() is False:
            self.delete_3_node_sib_3_node_parent(hole, sibling, parent)

    def delete_root(self, node):
        self.dbi.remove_23_node(node.node_id)
        self.dbi.new_root(node.left_child_id)
        self.dbi.remove_23_node(node.left_child_id)

    def delete_3_node_no_children(self, value, node):
        delete_left = node.left == value
        if delete_left:
            node.left = node.right
            node.right = None
        else:
            node.right = None
        node.update_hash(self.dbi)
        self.update_hashes_upwards(node)

    def delete_2_node_sib_2_node_parent(self, hole, sibling, parent):
        _, new_parent, _ = self.find_nearest_node_and_parent(parent.left)
        if sibling.left < parent.left:
            values = [sibling.left, parent.left]
            children = [sibling.left_child_id, sibling.right_child_id, hole.left_child_id]
            sibling.update_23_node_value_children(self.dbi, values, children)
            hole_node = self.dbi.make_hole_node(parent, sibling.node_id)
        else:
            values = [parent.left, sibling.left]
            children = [hole.left_child_id, sibling.left_child_id, sibling.right_child_id]
            sibling.update_23_node_value_children(self.dbi, values, children)
            hole_node = self.dbi.make_hole_node(parent, sibling.node_id)
        self.dbi.remove_23_node(hole.node_id)
        hole_node.parent = new_parent
        self.delete_hole(hole_node)

    def delete_3_node_sib_2_node_parent(self, hole, sibling, parent):
        if sibling.left < parent.left:
            # left
            lvalues = [sibling.left, None]
            lchildren = [sibling.left_child_id, None, sibling.mid_child_id]
            # parent
            pvalues = [sibling.right, None]
            # right
            rvalues = [parent.left, None]
            rchildren = [sibling.right_child_id, None, hole.left_child_id]

            sibling.update_23_node_value_children(self.dbi, lvalues, lchildren)
            hole.update_23_node_value_children(self.dbi, rvalues, rchildren)
            parent.update_23_node_value_children(self.dbi, pvalues)
        else:
            # left
            lvalues = [parent.left, None]
            lchildren = [hole.left_child_id, None, sibling.left_child_id]
            # parent
            pvalues = [sibling.left, None]
            # right
            rvalues = [sibling.right, None]
            rchildren = [sibling.mid_child_id, None, sibling.right_child_id]

            hole.update_23_node_value_children(self.dbi, lvalues, lchildren)
            sibling.update_23_node_value_children(self.dbi, rvalues, rchildren)
            parent.update_23_node_value_children(self.dbi, pvalues)
        self.update_hashes_upwards(sibling)

    def delete_2_node_sib_3_node_parent(self, hole, sibling, parent):
        if parent.left_child_id == hole.node_id or sibling.left < parent.left:
            # left
            if sibling.left < parent.left:
                lvalues = [sibling.left, parent.left]
                lchildren = [sibling.left_child_id, sibling.right_child_id, hole.left_child_id]
                parent_children = [parent.left_child_id, None, parent.right_child_id]
            else:
                lvalues = [parent.left, sibling.left]
                lchildren = [hole.left_child_id, sibling.left_child_id, sibling.right_child_id]
                parent_children = [parent.mid_child_id, None, parent.right_child_id]
            #self.dbi.update_23_node_value_children(sibling, values, children)
            # parent
            pvalues = [parent.right, None]

            # remove hole
            self.dbi.remove_23_node(hole.node_id)
            sibling.update_23_node_value_children(self.dbi, lvalues, lchildren)
            parent.update_23_node_value_children(self.dbi, pvalues, parent_children)
            self.update_hashes_upwards(sibling)
        else:
            # right
            if sibling.left < parent.right:
                lvalues = [sibling.left, parent.right]
                lchildren = [sibling.left_child_id, sibling.right_child_id, hole.left_child_id]
                parent_children = [parent.left_child_id, None, parent.right_child_id]
            else:
                lvalues = [parent.right, sibling.left]
                lchildren = [hole.left_child_id, sibling.left_child_id, sibling.right_child_id]
                parent_children = [parent.left_child_id, None, parent.mid_child_id]

            # parent
            pvalues = [parent.left, None]

            # remove hole
            self.dbi.remove_23_node(sibling.node_id)
            hole.update_23_node_value_children(self.dbi, lvalues, lchildren)
            parent.update_23_node_value_children(self.dbi, pvalues, parent_children)
            self.update_hashes_upwards(hole.make_23_node(lvalues, lchildren))

    def delete_3_node_sib_3_node_parent(self, hole, sibling, parent):
        if parent.left_child_id == hole.node_id or sibling.left < parent.left:
            if sibling.left < parent.left:
                # left
                lvalues = [sibling.left, None]
                lchildren = [sibling.left_child_id, None, sibling.mid_child_id]

                # right
                rvalues = [parent.left, None]
                rchildren = [sibling.right_child_id, None, hole.left_child_id]

                pvalues = [sibling.right, parent.right]

                sibling.update_23_node_value_children(self.dbi, lvalues, lchildren)
                hole.update_23_node_value_children(self.dbi, rvalues, rchildren)
            else:
                # left
                lvalues = [parent.left, None]
                lchildren = [hole.left_child_id, None, sibling.left_child_id]

                # right
                rvalues = [sibling.right, None]
                rchildren = [sibling.mid_child_id, None, sibling.right_child_id]

                pvalues = [sibling.left, parent.right]

                hole.update_23_node_value_children(self.dbi, lvalues, lchildren)
                sibling.update_23_node_value_children(self.dbi, rvalues, rchildren)

            # parent
            parent.update_23_node_value_children(self.dbi, pvalues)
            self.update_hashes_upwards(sibling)

        else:
            if sibling.left < parent.right:
                # left
                lvalues = [sibling.left, None]
                lchildren = [sibling.left_child_id, None, sibling.mid_child_id]

                # right
                rvalues = [parent.right, None]
                rchildren = [sibling.right_child_id, None, hole.left_child_id]

                pvalues = [parent.left, sibling.right]

                sibling.update_23_node_value_children(self.dbi, lvalues, lchildren)
                hole.update_23_node_value_children(self.dbi, rvalues, rchildren)
            else:
                # left
                lvalues = [parent.right, None]
                lchildren = [hole.left_child_id, None, sibling.left_child_id]

                # right
                rvalues = [sibling.right, None]
                rchildren = [sibling.mid_child_id, None, sibling.right_child_id]

                pvalues = [parent.left, sibling.left]

                hole.update_23_node_value_children(self.dbi, lvalues, lchildren)
                sibling.update_23_node_value_children(self.dbi, rvalues, rchildren)

            # parent
            parent.update_23_node_value_children(self.dbi, pvalues)
            self.update_hashes_upwards(sibling)

    def print_db(self):
        print("\nAll records in DB")
        cursor = self.dbi.nodes.find()
        for record in cursor:
            print(record)

    def get_db_cursor(self):
        return self.dbi.nodes.find()

    def get_root_hash(self):
        return self.dbi.get_root_hash()

    def destroy_db(self):
        self.dbi.destroy_db()
        self.root = None

    def tree_to_str(self, node: 'Two3Node', depth=0):
        if node is None:
            return "None"
        left = self.tree_to_str(self.dbi.get_23_node_by_id(node.left_child_id), depth + 1)
        mid = self.tree_to_str(self.dbi.get_23_node_by_id(node.mid_child_id), depth + 1)
        right = self.tree_to_str(self.dbi.get_23_node_by_id(node.right_child_id), depth + 1)
        tabs = "\t" * depth
        return f"Depth {depth} " + node.__str__() + f"\n {tabs} | {left} \n {tabs} | {mid} \n {tabs} | {right}"

    def print_tree(self):
        if self.root_id is None:
            print("Empty tree")
        else:
            print(self.tree_to_str(self.dbi.get_23_node_by_id(self.root_id)))

