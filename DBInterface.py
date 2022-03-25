class DatabaseGeneralNodeInterface:

    def get_node_by_id(self, node_id):
        raise NotImplementedError()

    def remove_node(self, node: 'Node'):
        raise NotImplementedError()

    def update_node(self, node: 'Node'):
        raise NotImplementedError()

    def update_up_from(self, node: 'Node'):
        raise NotImplementedError()


class Database23NodeInterface:
    def update_up_from_23_node(self, node: 'Two3Node'):
        raise NotImplementedError()

    def get_23_node_by_id(self, node_id) -> 'Two3Node':
        raise NotImplementedError()

    def create_23_node(self, key, children=None) -> 'Two3Node':
        raise NotImplementedError()

    def update_23_node(self, node: 'Two3Node'):
        raise NotImplementedError()

    def remove_23_node(self, node: 'Two3Node'):
        raise NotImplementedError()

    def create_root(self, value) -> 'Two3Node':
        raise NotImplementedError()