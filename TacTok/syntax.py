# Help dealing with syntax options, without clutter

from lark.tree import Tree

class SyntaxConfig:

    def __init__(self, include_locals=True, include_defs=True, include_paths=True):
        self.include_locals = include_locals
        self.include_defs = include_defs
        self.include_paths = include_paths

    # The node is an identifier
    def is_ident(self, node):
        return (node.data == 'names__id__t')

    # The node is a variable
    def is_var(self, node):
        return (node.data == 'constructor_var')

    # The node is a name
    def is_name(self, node):
        return (node.data == 'constructor_name')
    
    # The node is a local variable (for now, whenever it is a variable or a name)
    def is_local(self, node):
        return self.is_var(node) or self.is_name(node)

    # The node is a path
    def is_path(self, node):
        return (node.data == 'constructor_dirpath')

    # The node is a label
    def is_label(self, node):
        return (node.data == 'names__label__t')

    # Make a new ident
    def singleton_ident(self, value):
        return Tree('names__id__t', [value])
